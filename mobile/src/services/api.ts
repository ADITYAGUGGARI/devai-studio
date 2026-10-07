const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function request<T>(path: string, apiKey: string, method = 'GET'): Promise<T> {
  const response = await fetch(API_URL + path, { method, headers: { 'X-API-Key': apiKey } });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}
