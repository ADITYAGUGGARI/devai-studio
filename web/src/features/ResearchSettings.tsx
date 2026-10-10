import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError, request } from '../services/api';
import {
  researchCategories,
  schedulePayload,
  type ResearchSchedule,
} from '../../../shared/researchSchedule';

export function ResearchSettings({ onDirtyChange }: { onDirtyChange: (dirty: boolean) => void }) {
  const navigate = useNavigate();
  const [saved, setSaved] = useState<ResearchSchedule | null>(null);
  const [draft, setDraft] = useState<ResearchSchedule | null>(null);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('Loading research settings…');
  const [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState<ResearchSchedule | null>(null);
  const key = useRef('');
  const runKey = useRef('');
  const dirty = Boolean(
    saved &&
    draft &&
    JSON.stringify(schedulePayload(saved)) !== JSON.stringify(schedulePayload(draft)),
  );
  function edit(value: ResearchSchedule) {
    key.current = '';
    setDraft(value);
  }
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  async function load() {
    setError('');
    setStatus('Loading research settings…');
    try {
      const account = await request<{ workspace_id: string }>('/auth/me');
      const value = await request<ResearchSchedule>(
        `/v1/workspaces/${encodeURIComponent(account.workspace_id)}/settings`,
      );
      setSaved(value);
      setDraft(value);
      setStatus('Saved');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load settings');
      setStatus('');
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function save() {
    if (!draft || !saved || !draft.canEdit) return;
    key.current ||= crypto.randomUUID();
    setBusy(true);
    setError('');
    setStatus('Saving…');
    try {
      const value = await request<ResearchSchedule>(
        `/v1/workspaces/${draft.workspaceId}/settings`,
        'PATCH',
        schedulePayload(draft),
        { 'Idempotency-Key': key.current },
      );
      setSaved(value);
      setDraft(value);
      setConflict(null);
      key.current = '';
      setStatus('Saved');
    } catch (cause) {
      setStatus('Save failed · Your changes are retained');
      setError(cause instanceof Error ? cause.message : 'Could not save settings');
      if (
        cause instanceof ApiError &&
        cause.status === 409 &&
        typeof cause.detail === 'object' &&
        cause.detail &&
        'server' in cause.detail
      ) {
        setConflict(cause.detail.server as ResearchSchedule);
      }
      if (cause instanceof ApiError) key.current = '';
    } finally {
      setBusy(false);
    }
  }
  async function runNow() {
    if (!saved || dirty || !saved.canRunResearch) return;
    runKey.current ||= crypto.randomUUID();
    setBusy(true);
    setError('');
    try {
      const result = await request<{ runId: string }>(
        '/v1/research/runs',
        'POST',
        { categoryIds: saved.categories },
        { 'Idempotency-Key': runKey.current },
      );
      runKey.current = '';
      navigate(`/discover?run=${encodeURIComponent(result.runId)}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not start research');
      if (cause instanceof ApiError) runKey.current = '';
    } finally {
      setBusy(false);
    }
  }
  if (!draft)
    return (
      <section className="panel">
        <p role="status">{status}</p>
        {error && (
          <>
            <p role="alert">{error}</p>
            <button onClick={() => void load()}>Retry</button>
          </>
        )}
      </section>
    );
  const disabled = busy || !draft.canEdit;
  return (
    <section className="panel research-settings" aria-labelledby="research-settings-title">
      <h2 id="research-settings-title">Daily discovery</h2>
      <p>
        Daily discovery collects a fixed previous 24 hours and saves findings for review. Leaving
        the app does not stop a research job.
      </p>
      {saved?.workerHealth && !saved.workerHealth.healthy && (
        <p role="status">
          The worker is currently offline. Research jobs will stay queued until it reconnects.
        </p>
      )}
      {!draft.canEdit && <p role="status">Only a studio owner can change this schedule.</p>}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void save();
        }}
      >
        <fieldset disabled={disabled}>
          <label>
            <input
              type="checkbox"
              checked={draft.researchEnabled}
              onChange={(event) => edit({ ...draft, researchEnabled: event.target.checked })}
            />{' '}
            Daily research
          </label>
          <label>
            Research time
            <input
              type="time"
              required
              value={draft.researchLocalTime}
              onChange={(event) => edit({ ...draft, researchLocalTime: event.target.value })}
            />
          </label>
          <label>
            Research timezone
            <input
              required
              list="research-timezones"
              value={draft.timeZone}
              onChange={(event) => edit({ ...draft, timeZone: event.target.value })}
            />
          </label>
          <datalist id="research-timezones">
            {Intl.supportedValuesOf('timeZone').map((zone) => (
              <option key={zone} value={zone} />
            ))}
          </datalist>
          <fieldset>
            <legend>Category mix · Choose at least one</legend>
            {researchCategories.map((category) => (
              <label key={category}>
                <input
                  type="checkbox"
                  checked={draft.categories.includes(category)}
                  onChange={(event) =>
                    edit({
                      ...draft,
                      categories: event.target.checked
                        ? [...draft.categories, category]
                        : draft.categories.filter((item) => item !== category),
                    })
                  }
                />
                {category}
              </label>
            ))}
          </fieldset>
        </fieldset>
        <p>
          Automatic drafting is unavailable until the revised generation workflow is ready.
          Scheduling research does not generate artwork or publish content.
        </p>
        <p>
          {saved?.researchEnabled
            ? `Next saved run: ${new Date(saved.nextRunAt!).toLocaleString(undefined, { timeZone: saved.timeZone })} (${saved.timeZone})`
            : 'Daily research is off. You can still run research manually.'}
        </p>
        <p role="status">{dirty && !busy ? 'Unsaved changes' : status}</p>
        {error && <p role="alert">{error}</p>}
        {conflict && (
          <div role="alert">
            <p>This schedule changed on another device. Your changes are retained.</p>
            <button
              type="button"
              onClick={() => {
                setDraft({ ...draft, revision: conflict.revision });
                setSaved({
                  ...draft,
                  ...conflict,
                  canEdit: draft.canEdit,
                  autoDraftAvailable: draft.autoDraftAvailable,
                });
                setConflict(null);
                setError('');
              }}
            >
              Keep my changes against latest revision
            </button>
            <button
              type="button"
              onClick={() => {
                const value = {
                  ...draft,
                  ...conflict,
                  canEdit: draft.canEdit,
                  autoDraftAvailable: draft.autoDraftAvailable,
                };
                setSaved(value);
                setDraft(value);
                setConflict(null);
                setError('');
              }}
            >
              Use saved schedule
            </button>
          </div>
        )}
        <button
          className="primary"
          disabled={disabled || !dirty || !draft.categories.length || Boolean(conflict)}
        >
          {busy ? 'Saving…' : 'Save schedule'}
        </button>
        <button type="button" className="secondary" onClick={() => navigate('/discover')}>
          Open research
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busy || dirty || !saved?.canRunResearch}
          onClick={() => void runNow()}
        >
          Run research now
        </button>
        {dirty && <p>Save your schedule changes before starting research.</p>}
      </form>
    </section>
  );
}
