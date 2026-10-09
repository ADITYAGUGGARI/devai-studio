import { useQuery } from '@tanstack/react-query';
import { useAtomValue } from 'jotai';
import { useState } from 'react';
import { accountAtom } from '../app/state';
import { request, downloadPost } from '../services/api';
import type { Post, WorkflowConfig } from '../types/posts';

export function PublishingWorkspace({
  posts,
  busy,
  onOpen,
  onAction,
  config,
}: {
  config?: WorkflowConfig;
  posts: Post[];
  busy: boolean;
  onOpen: (id: string) => void;
  onAction: (op: () => Promise<unknown>) => Promise<void>;
}) {
  const [filter, setFilter] = useState('Ready');
  const { data: schedules = [] } = useQuery({
    queryKey: ['schedules'],
    queryFn: () =>
      request<
        {
          id: string;
          post_id: string;
          version: string;
          due_at: string;
          status: string;
          error: string | null;
        }[]
      >('/publishing/schedules'),
    refetchInterval: 3000,
  });
  const account = useAtomValue(accountAtom);
  const canPublish = ['admin', 'reviewer'].includes(account?.role || '');
  const configured = Boolean(config?.instagram_configured && config?.public_media_configured);
  return (
    <section className="panel" aria-label="Publishing workspace">
      <h2>Publishing workspace</h2>
      <p className="hint">
        Review, export, publish or schedule an approved version. Times below use your local
        timezone.
      </p>
      <div className="workspace-sections" aria-label="Publishing filters">
        {['Ready', 'Needs review', 'Published', 'Schedules'].map((label) => (
          <button
            key={label}
            className={filter === label ? 'secondary active' : 'ghost'}
            aria-pressed={filter === label}
            onClick={() => setFilter(label)}
          >
            {label}
          </button>
        ))}
      </div>
      {!configured && (
        <p className="hint">
          Export is available. To publish or schedule, configure Instagram credentials and a public
          HTTPS media address on the server.
        </p>
      )}
      {posts
        .filter((p) =>
          filter === 'Ready'
            ? ['approved', 'publishing'].includes(p.status)
            : filter === 'Needs review'
              ? p.status === 'pending_review'
              : filter === 'Published'
                ? p.status === 'published'
                : false,
        )
        .map((p) => (
          <article className="source-evidence" key={p.id}>
            <h3>{p.title}</h3>
            <span className="pill">
              {p.status} · v{p.version}
            </span>
            <div className="actions">
              <button className="secondary" onClick={() => onOpen(p.id)}>
                Review {p.title}
              </button>
              <button
                className="ghost"
                disabled={busy}
                onClick={() => onAction(() => downloadPost(p.id))}
              >
                Export ZIP
              </button>
              {p.status === 'approved' && canPublish && (
                <button
                  className="primary"
                  disabled={busy || !configured}
                  onClick={() => onAction(() => request(`/posts/${p.id}/publish`, 'POST'))}
                >
                  Publish approved version
                </button>
              )}
            </div>
            {p.status === 'approved' && canPublish && (
              <details>
                <summary>Schedule this carousel</summary>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const due = new FormData(e.currentTarget).get('due');
                    void onAction(() =>
                      request(`/posts/${p.id}/schedule`, 'POST', {
                        due_at: new Date(String(due)).toISOString(),
                      }),
                    );
                  }}
                >
                  <label>
                    Publication time
                    <input
                      aria-label={`Publication time for ${p.title}`}
                      type="datetime-local"
                      name="due"
                      required
                      min={new Date(Date.now() + 60000)
                        .toLocaleString('sv-SE')
                        .slice(0, 16)
                        .replace(' ', 'T')}
                    />
                  </label>
                  <button className="secondary" disabled={busy || !configured}>
                    Schedule approved version
                  </button>
                </form>
              </details>
            )}
          </article>
        ))}
      {filter === 'Ready' && !posts.some((p) => p.status === 'approved') && (
        <p className="hint">
          Approved carousels will appear here. Open a draft from the library to review it.
        </p>
      )}
      {filter !== 'Ready' &&
        filter !== 'Schedules' &&
        !posts.some(
          (p) => p.status === (filter === 'Needs review' ? 'pending_review' : 'published'),
        ) && <p className="hint">No carousels in this section yet.</p>}
      {filter === 'Schedules' && (
        <>
          <h3>Publication schedule</h3>
          {schedules.length ? (
            schedules.map((s) => (
              <div className="source-evidence" key={s.id}>
                <strong>
                  {posts.find((p) => p.id === s.post_id)?.title || s.post_id} · v{s.version}
                </strong>
                <p>
                  {new Date(s.due_at).toLocaleString()} · {s.status}
                </p>
                {s.error && <p className="run-warning">{s.error}</p>}
                {s.status === 'scheduled' && canPublish && (
                  <button
                    disabled={busy}
                    className="ghost"
                    onClick={() =>
                      onAction(() => request(`/publishing/schedules/${s.id}/cancel`, 'POST'))
                    }
                  >
                    Cancel schedule
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="hint">No scheduled publications.</p>
          )}
        </>
      )}
    </section>
  );
}

interface Ops {
  database: string;
  accounts: number;
  jobs: Record<string, number>;
  estimated_cost_usd: number;
  unpriced_calls: number;
  settings: {
    daily_enabled: boolean;
    daily_hour: number;
    timezone: string;
    daily_generate_carousel: boolean;
  };
  usage: {
    id: string;
    model: string;
    operation: string;
    status: string;
    input_tokens: number;
    output_tokens: number;
    images: number;
    estimated_cost_usd: number | null;
    created_at: string;
    duration_ms: number;
  }[];
}
export function OperationsWorkspace({
  busy,
  onAction,
}: {
  busy: boolean;
  onAction: (op: () => Promise<unknown>) => Promise<void>;
}) {
  const { data: ops, error } = useQuery({
    queryKey: ['operations'],
    queryFn: () => request<Ops>('/ops/summary'),
    refetchInterval: 5000,
  });
  const account = useAtomValue(accountAtom);
  const [message, setMessage] = useState('');
  const [section, setSection] = useState('Overview');
  if (error)
    return (
      <p role="alert" className="error">
        {error.message}
      </p>
    );
  if (!ops) return <p role="status">Loading workspace health…</p>;
  return (
    <section className="panel" aria-label="Operations workspace">
      <h2>Workspace operations</h2>
      <div className="workspace-sections" aria-label="Settings sections">
        {[
          'Overview',
          'Daily research',
          'Provider usage',
          ...(account?.role === 'admin' ? ['Accounts'] : []),
        ].map((label) => (
          <button
            key={label}
            className={section === label ? 'secondary active' : 'ghost'}
            aria-pressed={section === label}
            onClick={() => setSection(label)}
          >
            {label}
          </button>
        ))}
      </div>
      {section === 'Overview' && (
        <>
          <div className="stats">
            <div className="source-evidence">
              <strong>Database</strong>
              {ops.database}
            </div>
            <div className="source-evidence">
              <strong>Background work</strong>
              {Object.keys(ops.jobs).length === 0 && <span>No active jobs</span>}
              {Object.entries(ops.jobs).map(([s, n]) => (
                <span key={s}>
                  {s.replaceAll('_', ' ')}: {n}
                </span>
              ))}
            </div>
            <div className="source-evidence">
              <strong>Estimated provider cost</strong>${ops.estimated_cost_usd.toFixed(4)}
              <span className="hint">
                {ops.unpriced_calls} calls lack configured rates. Estimates are not invoice totals.
              </span>
            </div>
          </div>
        </>
      )}
      {section === 'Daily research' && (
        <>
          <h3>Daily research</h3>
          <p>
            {ops.settings.daily_enabled ? 'Enabled' : 'Disabled'} · {ops.settings.daily_hour}:00 ·{' '}
            {ops.settings.timezone}
          </p>
          {account?.role === 'admin' && (
            <form
              key={JSON.stringify(ops.settings)}
              onSubmit={(e) => {
                e.preventDefault();
                const d = new FormData(e.currentTarget);
                void onAction(() =>
                  request('/ops/settings', 'PATCH', {
                    daily_enabled: d.get('enabled') === 'on',
                    daily_hour: Number(d.get('hour')),
                    timezone: d.get('timezone'),
                    daily_generate_carousel: d.get('generate') === 'on',
                  }),
                );
              }}
            >
              <label className="check">
                <input name="enabled" type="checkbox" defaultChecked={ops.settings.daily_enabled} />
                Enable daily research
              </label>
              <label>
                Hour (0–23)
                <input
                  name="hour"
                  type="number"
                  min="0"
                  max="23"
                  defaultValue={ops.settings.daily_hour}
                  required
                />
              </label>
              <label>
                Timezone
                <input name="timezone" defaultValue={ops.settings.timezone} required />
              </label>
              <label className="check">
                <input
                  name="generate"
                  type="checkbox"
                  defaultChecked={ops.settings.daily_generate_carousel}
                />
                Automatically draft from an approved topic
              </label>
              <button className="primary" disabled={busy}>
                Save research schedule
              </button>
            </form>
          )}
        </>
      )}
      {section === 'Provider usage' && (
        <>
          <h3>Provider usage</h3>
          <div className="table-scroll">
            <table>
              <caption>Recent real provider calls</caption>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Model / operation</th>
                  <th>Status</th>
                  <th>Tokens in / out</th>
                  <th>Images</th>
                  <th>Estimated USD</th>
                </tr>
              </thead>
              <tbody>
                {ops.usage.map((u) => (
                  <tr key={u.id}>
                    <td>{new Date(u.created_at).toLocaleString()}</td>
                    <td>
                      {u.model}
                      <br />
                      {u.operation}
                    </td>
                    <td>{u.status}</td>
                    <td>
                      {u.input_tokens} / {u.output_tokens}
                    </td>
                    <td>{u.images}</td>
                    <td>
                      {u.estimated_cost_usd === null ? 'Unpriced' : u.estimated_cost_usd.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {section === 'Accounts' && account?.role === 'admin' && (
        <>
          <h3>Workspace accounts · {ops.accounts}</h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const form = e.currentTarget;
              const d = new FormData(form);
              void onAction(async () => {
                await request('/auth/users', 'POST', {
                  email: d.get('email'),
                  password: d.get('password'),
                  role: d.get('role'),
                });
                setMessage('Account created.');
                form.reset();
              });
            }}
          >
            <label>
              Account email
              <input name="email" type="email" autoComplete="off" required />
            </label>
            <label>
              Initial password
              <input
                name="password"
                type="password"
                autoComplete="new-password"
                minLength={12}
                required
              />
            </label>
            <label>
              Role
              <select name="role" aria-label="Role">
                <option>editor</option>
                <option>reviewer</option>
                <option>viewer</option>
                <option>admin</option>
              </select>
            </label>
            <button disabled={busy} className="secondary">
              Create account
            </button>
            <p role="status">{message}</p>
          </form>
        </>
      )}
    </section>
  );
}
