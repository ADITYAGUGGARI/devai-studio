import { useEffect, useRef, useState } from 'react';
import type { Job } from '../../types/posts';
import { request } from '../../services/api';
const pending = (job: Job) => ['queued', 'running', 'retry_wait'].includes(job.status);
export function TaskDock({
  jobs,
  busy,
  canWrite,
  onAction,
  onOpen,
  onActivity,
  onResearch,
}: {
  jobs: Job[];
  busy: boolean;
  canWrite: boolean;
  onAction: (op: () => Promise<unknown>) => Promise<void>;
  onOpen: (id: string) => void;
  onActivity: () => void;
  onResearch: () => void;
}) {
  const previous = useRef<Map<string, string> | null>(null);
  const [finished, setFinished] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    if (previous.current) {
      const changed = jobs.find(
        (job) =>
          previous.current!.has(job.id) &&
          previous.current!.get(job.id) !== job.status &&
          !pending(job),
      );
      if (changed) setFinished(changed.id);
    }
    previous.current = new Map(jobs.map((job) => [job.id, job.status]));
  }, [jobs]);
  const active = jobs.filter(pending);
  const recent = jobs.find((job) => job.id === finished);
  const job = active[0] || recent;
  if (!job) return null;
  const failed = ['failed', 'needs_reconciliation'].includes(job.status);
  const completed = job.status.startsWith('completed');
  return (
    <section className="task-dock" aria-label="Task status">
      <div className="task-summary">
        <div role="status" aria-live="polite">
          <strong>
            {active.length
              ? `${active.length} background ${active.length === 1 ? 'task' : 'tasks'}`
              : failed
                ? 'Task needs attention'
                : 'Task completed'}
          </strong>
          <span>
            {job.kind.replaceAll('_', ' ')} · {job.step}
          </span>
        </div>
        <div className="actions">
          {completed && job.result?.post_id && (
            <button className="secondary" onClick={() => onOpen(job.result!.post_id!)}>
              Open ready draft
            </button>
          )}
          {completed && job.kind === 'research' && (
            <button className="secondary" onClick={onResearch}>
              Explore results
            </button>
          )}
          {job.status === 'failed' && job.kind !== 'publish' && (
            <button
              className="secondary"
              disabled={busy || !canWrite}
              onClick={() => onAction(() => request(`/jobs/${job.id}/retry`, 'POST'))}
            >
              Retry task
            </button>
          )}
          <button className="ghost" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Hide task details' : 'Task details'}
          </button>
          <button className="ghost" onClick={onActivity}>
            View activity
          </button>
          {!active.length && (
            <button
              className="ghost"
              aria-label="Dismiss task notification"
              onClick={() => setFinished(null)}
            >
              ×
            </button>
          )}
        </div>
      </div>
      {active.length > 0 && (
        <progress
          aria-label="Current background task progress"
          value={job.progress}
          max={Math.max(job.total, 1)}
        />
      )}
      {expanded && (
        <div className="task-expanded">
          {(active.length ? active : [job]).map((item) => (
            <div key={item.id}>
              <strong>
                {item.kind.replaceAll('_', ' ')} · {item.status.replaceAll('_', ' ')}
              </strong>
              <p>
                {item.step} · attempt {item.attempts}/{item.max_attempts}
              </p>
              {item.error && <p className="run-warning">{item.error}</p>}
              {item.status === 'retry_wait' && (
                <p>Next attempt: {new Date(item.available_at).toLocaleTimeString()}</p>
              )}
              {item.result?.warnings?.length ? (
                <p className="run-warning">
                  Completed with source warnings. Review diagnostics in Activity.
                </p>
              ) : null}
              {item.status === 'needs_reconciliation' && (
                <p>
                  Check Instagram before reconciling this version. Publishing cannot be retried
                  automatically.
                </p>
              )}
            </div>
          ))}
          <p className="hint">
            Work continues on the server. You can switch screens or return later.
          </p>
        </div>
      )}
    </section>
  );
}
