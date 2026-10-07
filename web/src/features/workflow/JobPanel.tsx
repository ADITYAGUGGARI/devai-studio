import { useState } from 'react';
import type { Job, WorkflowConfig } from '../../types/posts';
import { request } from '../../services/api';

interface Props {
  jobs: Job[];
  config?: WorkflowConfig;
  busy: boolean;
  onAction: (operation: () => Promise<unknown>) => Promise<void>;
  onOpen: (id: string) => void;
}

export function JobPanel({ jobs, config, busy, onAction, onOpen }: Props) {
  const [showHistory, setShowHistory] = useState(false);
  const pending = jobs.filter((job) =>
    ['queued', 'running', 'retry_wait', 'needs_reconciliation'].includes(job.status),
  );
  const history = jobs.filter((job) => !pending.includes(job));
  const visible = showHistory ? [...pending, ...history] : [...pending, ...history].slice(0, 6);
  if (!jobs.length && !config) return null;
  return (
    <section className="panel" aria-label="Background work">
      <div className="sectiontitle">
        <h2>Background work</h2>
        <span className="hint">
          {config?.daily_enabled
            ? `Daily at ${config.daily_hour}:00 · ${config.timezone}`
            : 'Daily schedule disabled · manual runs available'}
        </span>
      </div>
      {config && !config.openai_configured && (
        <p className="run-warning">
          Configure the server’s OpenAI key to generate copy, images and validation reports.
        </p>
      )}
      {visible.map((job) => (
        <div className="job-row" key={job.id}>
          <div className="sectiontitle">
            <strong>{job.kind.replaceAll('_', ' ')}</strong>
            <span className="pill">
              {job.status === 'completed' && job.result?.warnings?.length
                ? 'completed with warnings'
                : job.status.replaceAll('_', ' ')}
            </span>
          </div>
          <p className="hint" role="status">
            {job.step} · attempt {job.attempts}/{job.max_attempts}
          </p>
          <progress
            aria-label={`${job.kind} progress`}
            value={job.status.startsWith('completed') ? job.total : job.progress}
            max={job.total}
          />
          {job.error && (
            <p className="run-warning">
              {job.error}
              {job.status === 'retry_wait'
                ? ` · Next attempt: ${new Date(job.available_at).toLocaleTimeString()}`
                : ''}
            </p>
          )}
          {job.result?.created_topic_ids && (
            <p className="hint">
              {job.result.created_topic_ids.length} new topics added ·{' '}
              {job.result.skipped_urls?.length ?? 0} sources already queued or used
            </p>
          )}
          {job.result?.warnings?.length ? (
            <details className="run-warning">
              <summary>Source warnings ({new Set(job.result.warnings).size})</summary>
              <ul>
                {[...new Set(job.result.warnings)].map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </details>
          ) : null}
          <div className="actions">
            {job.result?.post_id && (
              <button
                className="secondary"
                disabled={busy}
                onClick={() => onOpen(job.result!.post_id!)}
              >
                Review draft
              </button>
            )}
            {job.status === 'failed' && job.kind !== 'publish' && (
              <button
                className="secondary"
                disabled={busy}
                onClick={() => onAction(() => request(`/jobs/${job.id}/retry`, 'POST'))}
              >
                Retry job
              </button>
            )}
          </div>
        </div>
      ))}
      {jobs.length > 6 && (
        <button className="ghost" onClick={() => setShowHistory(!showHistory)}>
          {showHistory ? 'Collapse history' : 'Show job history'}
        </button>
      )}
      <p className="hint">
        Jobs continue on the server when you leave this screen. Open drafts to review source
        evidence and every slide before approving.
      </p>
    </section>
  );
}
