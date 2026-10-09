import { useEffect, useRef, useState } from 'react';
import { ApiError, request } from '../services/api';

interface Profile {
  id: string;
  email: string;
  displayName: string;
  locale: 'en';
  timeZone: string;
  revision: number;
}

export function ProfileSettings({ onDirtyChange }: { onDirtyChange: (dirty: boolean) => void }) {
  const [saved, setSaved] = useState<Profile | null>(null);
  const [name, setName] = useState('');
  const [zone, setZone] = useState('America/Chicago');
  const [error, setError] = useState('');
  const [status, setStatus] = useState('Loading profile…');
  const [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState<Profile | null>(null);
  const key = useRef('');
  const dirty = Boolean(saved && (name !== saved.displayName || zone !== saved.timeZone));
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  async function load() {
    setError('');
    setStatus('Loading profile…');
    try {
      const value = await request<Profile>('/v1/me');
      setSaved(value);
      setName(value.displayName);
      setZone(value.timeZone);
      setStatus('Saved');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Profile could not load.');
      setStatus('');
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function save() {
    if (!saved) return;
    if (!key.current) key.current = crypto.randomUUID();
    setBusy(true);
    setError('');
    setStatus('Saving…');
    try {
      const value = await request<Profile>(
        '/v1/me',
        'PATCH',
        {
          displayName: name,
          locale: 'en',
          timeZone: zone,
          expectedRevision: saved.revision,
        },
        { 'Idempotency-Key': key.current },
      );
      key.current = '';
      setSaved(value);
      setName(value.displayName);
      setZone(value.timeZone);
      setConflict(null);
      setStatus('Saved');
    } catch (cause) {
      if (cause instanceof ApiError) {
        key.current = '';
        if (
          cause.status === 409 &&
          typeof cause.detail === 'object' &&
          cause.detail !== null &&
          'server' in cause.detail
        ) {
          setConflict(cause.detail.server as Profile);
        }
      }
      setError(cause instanceof Error ? cause.message : 'Save failed. Your changes are retained.');
      setStatus('Save failed · changes retained');
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel" aria-labelledby="profile-title">
      <h2 id="profile-title">Profile & preferences</h2>
      <p>
        Choose your display name and timezone. Existing publication reservations keep their
        confirmed timing.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <p role="status">{dirty && !busy && !error ? 'Unsaved changes' : status}</p>
      {!saved ? (
        <button className="secondary" onClick={() => void load()}>
          Retry profile
        </button>
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void save();
          }}
          style={{ maxWidth: 640 }}
        >
          <p>{saved.email}</p>
          <label>
            Display name
            <input
              required
              maxLength={80}
              value={name}
              disabled={busy}
              onChange={(event) => {
                key.current = '';
                setName(event.target.value);
              }}
            />
          </label>
          <label>
            Language
            <select value="en" disabled aria-describedby="language-info">
              <option value="en">English</option>
            </select>
          </label>
          <p id="language-info" className="hint">
            English is supported in this release.
          </p>
          <label>
            Personal timezone
            <input
              required
              list="profile-zones"
              value={zone}
              disabled={busy}
              onChange={(event) => {
                key.current = '';
                setZone(event.target.value);
              }}
            />
          </label>
          <datalist id="profile-zones">
            {Intl.supportedValuesOf('timeZone').map((value) => (
              <option key={value} value={value} />
            ))}
            <option value="UTC" />
          </datalist>
          {conflict && (
            <div className="source-evidence" role="region" aria-label="Profile conflict">
              <h3>Your profile changed on another device</h3>
              <p>
                Saved name: {conflict.displayName} · Saved timezone: {conflict.timeZone}
              </p>
              <p>
                Your input remains in the form. Continuing uses revision {conflict.revision} and
                still requires Save.
              </p>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setSaved(conflict);
                  setConflict(null);
                  setError('');
                }}
              >
                Keep my changes for a new save
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setSaved(conflict);
                  setName(conflict.displayName);
                  setZone(conflict.timeZone);
                  setConflict(null);
                  setError('');
                  setStatus('Saved version loaded');
                }}
              >
                Use saved version and discard my input
              </button>
            </div>
          )}
          <button className="primary" type="submit" disabled={busy || !dirty || Boolean(conflict)}>
            Save profile
          </button>
        </form>
      )}
    </section>
  );
}
