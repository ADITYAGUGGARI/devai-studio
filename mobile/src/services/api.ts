import { getDefaultStore } from 'jotai';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { sessionAtom, type Session } from '../app/state';
export const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000').replace(
  /\/$/,
  '',
);
export async function request<T>(
  path: string,
  method = 'GET',
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<T> {
  const session = getDefaultStore().get(sessionAtom);
  const response = await fetch(API_URL + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    if (response.status === 401 && path != '/auth/login') await saveSession(null);
    throw new Error(
      typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}
export async function saveSession(session: Session | null) {
  getDefaultStore().set(sessionAtom, session);
  if (Platform.OS !== 'web') {
    if (session) await SecureStore.setItemAsync('devai-session', JSON.stringify(session));
    else await SecureStore.deleteItemAsync('devai-session');
  }
}
export async function restoreSession() {
  if (Platform.OS === 'web') return;
  const raw = await SecureStore.getItemAsync('devai-session');
  if (raw) {
    let session: Session;
    try {
      session = JSON.parse(raw) as Session;
    } catch {
      await saveSession(null);
      return;
    }
    getDefaultStore().set(sessionAtom, session);
    // Only an explicit 401 revokes the local session. Offline launch must retain it.
    await request('/auth/me').catch(() => {});
  }
}
export async function exportPost(id: string) {
  const session = getDefaultStore().get(sessionAtom);
  if (!session) throw new Error('Sign in first');
  if (Platform.OS === 'web') {
    throw new Error(
      'ZIP sharing is available in the native iOS app. Use the web dashboard for browser downloads.',
    );
  }
  const result = await FileSystem.downloadAsync(
    `${API_URL}/posts/${id}/export`,
    `${FileSystem.cacheDirectory}devai-${id}.zip`,
    { headers: { Authorization: `Bearer ${session.token}` } },
  );
  if (result.status !== 200) throw new Error('Export failed; complete the slide images first');
  if (!(await Sharing.isAvailableAsync()))
    throw new Error('File sharing is unavailable on this device');
  await Sharing.shareAsync(result.uri, { mimeType: 'application/zip', UTI: 'public.zip-archive' });
}
