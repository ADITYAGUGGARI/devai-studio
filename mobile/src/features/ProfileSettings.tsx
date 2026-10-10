import { useEffect, useRef, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, Text, View } from 'react-native';
import { useNavigation, usePreventRemove } from '@react-navigation/native';
import { ApiError, request } from '../services/api';
import { Button, ErrorText, Field, Screen, styles } from '../components/ui';

interface Profile {
  id: string;
  email: string;
  displayName: string;
  timeZone: string;
  revision: number;
}

export function ProfileSettings() {
  const navigation = useNavigation();
  const [saved, setSaved] = useState<Profile | null>(null);
  const [name, setName] = useState('');
  const [zone, setZone] = useState('America/Chicago');
  const [status, setStatus] = useState('Loading profile…');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState<Profile | null>(null);
  const key = useRef('');
  const dirty = Boolean(saved && (saved.displayName !== name || saved.timeZone !== zone));
  async function load() {
    try {
      const value = await request<Profile>('/v1/me');
      setSaved(value);
      setName(value.displayName);
      setZone(value.timeZone);
      setStatus('Saved');
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Profile could not load.');
      setStatus('');
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function save() {
    if (!saved || conflict) return false;
    setBusy(true);
    setError('');
    setStatus('Saving…');
    if (!key.current)
      key.current = `ios-profile-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    try {
      const value = await request<Profile>(
        '/v1/me',
        'PATCH',
        { displayName: name, timeZone: zone, locale: 'en', expectedRevision: saved.revision },
        { 'Idempotency-Key': key.current },
      );
      key.current = '';
      setSaved(value);
      setName(value.displayName);
      setZone(value.timeZone);
      setStatus('Saved');
      return true;
    } catch (cause) {
      if (cause instanceof ApiError) {
        key.current = '';
        if (
          cause.status === 409 &&
          typeof cause.detail === 'object' &&
          cause.detail !== null &&
          'server' in cause.detail
        )
          setConflict(cause.detail.server as Profile);
      }
      setError(cause instanceof Error ? cause.message : 'Save failed. Your changes are retained.');
      setStatus('Save failed · changes retained');
      return false;
    } finally {
      setBusy(false);
    }
  }
  usePreventRemove(dirty, ({ data }) => {
    const proceed = () => navigation.dispatch(data.action);
    Alert.alert('Keep your changes?', 'Your profile has changes that have not been saved.', [
      { text: 'Stay', style: 'cancel' },
      { text: 'Discard local changes', style: 'destructive', onPress: proceed },
      {
        text: 'Save and leave',
        onPress: () => {
          void save().then((success) => {
            if (success) proceed();
          });
        },
      },
    ]);
  });
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={{ flex: 1 }}
    >
      <Screen title="Profile & preferences">
        <ErrorText value={error} />
        <Text style={styles.muted} accessibilityLiveRegion="polite">
          {dirty && !busy && !error ? 'Unsaved changes' : status}
        </Text>
        {!saved ? (
          <Button title="Retry profile" onPress={() => void load()} secondary />
        ) : (
          <View>
            <Text style={styles.text}>{saved.email}</Text>
            <Field
              label="Display name"
              value={name}
              onChange={(value) => {
                key.current = '';
                setName(value);
              }}
            />
            <Text style={styles.muted}>
              Language · English. Additional languages are not available in this release.
            </Text>
            <Field
              label="Personal timezone"
              value={zone}
              onChange={(value) => {
                key.current = '';
                setZone(value);
              }}
            />
            <Text style={styles.muted}>
              Use an IANA timezone such as America/Chicago. Existing publication reservations retain
              their confirmed timing.
            </Text>
            {conflict && (
              <View>
                <Text style={styles.text}>
                  Changed on another device: {conflict.displayName} · {conflict.timeZone}
                </Text>
                <Button
                  title="Keep my input for a new save"
                  secondary
                  onPress={() => {
                    setSaved(conflict);
                    setConflict(null);
                    setError('');
                  }}
                />
                <Button
                  title="Use saved profile and discard my input"
                  secondary
                  onPress={() => {
                    setSaved(conflict);
                    setName(conflict.displayName);
                    setZone(conflict.timeZone);
                    setConflict(null);
                    setError('');
                    setStatus('Saved version loaded');
                  }}
                />
              </View>
            )}
            <Button
              title={busy ? 'Saving…' : 'Save profile'}
              disabled={busy || !dirty || Boolean(conflict)}
              onPress={() => void save()}
            />
          </View>
        )}
      </Screen>
    </KeyboardAvoidingView>
  );
}
