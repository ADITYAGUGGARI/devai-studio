import type { DailyRunSummary, Job } from '../../types/posts';
import { useEffect, useState } from 'react';

interface Props {
  summary?: DailyRunSummary;
  loading: boolean;
  busy: boolean;
  onRun: () => void;
  onRegenerate: () => void;
}

const topicLabels: Record<string, string> = {
  news: 'AI news and developer impact',
  tutorial: 'A practical AI development tutorial',
  architecture: 'AI system architecture',
  tools: 'Developer tools and trade-offs',
  insight: 'An engineering insight',
};

function RefreshStatus({ job }: { job: Job }) {
  const completed = job.status.startsWith('completed');
  const timestamp = new Date(job.finished_at || job.created_at).toLocaleString();
  return (
    <>
      <p className="hint">Latest research refresh · {timestamp}</p>
      {completed ? (
        <>
          <p className="hint">
            {job.result?.created_topic_ids?.length ?? 0} new topics added ·{' '}
            {job.result?.skipped_urls?.length ?? 0} sources already queued or used. Select a story
            below to generate its carousel.
          </p>
          {job.result?.warnings?.length ? (
            <details className="run-warning">
              <summary>
                Latest refresh source warnings ({new Set(job.result.warnings).size})
              </summary>
              <ul>
                {[...new Set(job.result.warnings)].map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </details>
          ) : (
            <p className="hint">Latest refresh completed without source warnings.</p>
          )}
        </>
      ) : job.status === 'failed' ? (
        <p className="run-warning" role="status">
          Latest research refresh failed. {job.error}
        </p>
      ) : (
        <p className="hint" role="status">
          Research refresh is in progress. {job.step}
        </p>
      )}
    </>
  );
}

export function DailyRunPanel({ summary, loading, busy, onRun, onRegenerate }: Props) {
  const [now, setNow] = useState(() => Date.now());
  const run = summary?.run;
  const topicOnly = summary?.mode !== 'carousel';
  const latestResearch = summary?.latest_research;
  const refresh =
    topicOnly &&
    latestResearch &&
    (!run ||
      new Date(latestResearch.created_at).getTime() >
        new Date(run.finished_at || run.started_at).getTime())
      ? latestResearch
      : null;
  const refreshActive = Boolean(
    refresh && ['queued', 'running', 'retry_wait'].includes(refresh.status),
  );
  const title = run?.result?.source_title;
  const retryAfter = run?.retry_after ? new Date(run.retry_after) : null;
  const retryAfterMs = retryAfter?.getTime();
  useEffect(() => {
    if (!retryAfterMs || retryAfterMs <= now) return;
    const timer = window.setTimeout(() => setNow(Date.now()), retryAfterMs - now);
    return () => window.clearTimeout(timer);
  }, [retryAfterMs, now]);
  const retryIsWaiting = Boolean(retryAfterMs && retryAfterMs > now);
  const retryTime = retryAfter?.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return (
    <section className="daily-run panel" aria-labelledby="daily-run-heading">
      <div className="daily-run-copy">
        <div className="eyebrow">
          DAILY EDITORIAL ·{' '}
          {(summary?.timezone || 'America/Chicago').replaceAll('_', ' ').toUpperCase()}
        </div>
        <h2 id="daily-run-heading">{topicLabels[summary?.topic || 'news']}</h2>
        {loading ? (
          <p className="hint">Checking today’s research run…</p>
        ) : refresh ? (
          <>
            <RefreshStatus job={refresh} />
            {run && (
              <details className="hint">
                <summary>
                  Earlier daily run · {new Date(run.finished_at || run.started_at).toLocaleString()}
                </summary>
                <p>Saved daily run: {run.status.replaceAll('_', ' ')}.</p>
                {run.result?.warnings?.length ? (
                  <p>Historical source warnings: {[...new Set(run.result.warnings)].join('; ')}</p>
                ) : null}
                {run.error && <p>{run.error}</p>}
              </details>
            )}
          </>
        ) : run?.status === 'running' ? (
          <p className="hint">
            Research is in progress. You can review the draft as soon as it finishes.
          </p>
        ) : run?.status === 'completed' || run?.status === 'completed_with_warnings' ? (
          <>
            <p className="hint">
              {topicOnly
                ? 'Today’s topic queue is refreshed. Select a story below to generate its carousel.'
                : `Today’s draft is ready for review${title ? `: ${title}` : '.'}`}
            </p>
            {topicOnly && run.result?.created_topic_ids && (
              <p className="hint">
                {run.result.created_topic_ids.length} new topics added ·{' '}
                {run.result.skipped_urls?.length ?? 0} sources already queued or used
              </p>
            )}
            {run.status === 'completed_with_warnings' && (
              <p className="run-warning">
                Some sources could not supply enough readable evidence:{' '}
                {[...new Set(run.result?.warnings)].join('; ')}
              </p>
            )}
          </>
        ) : run?.status === 'failed' ? (
          <p className="run-warning" role="status">
            Research did not finish.{' '}
            {run.error?.includes('OPENAI_API_KEY is not configured') ? (
              <>
                Add <code>OPENAI_API_KEY</code> to the root <code>.env</code>, then restart the API
                and scheduler. Once configured, you can retry this run from here.
              </>
            ) : (
              run.error
            )}{' '}
            {run.attempt_count < 3
              ? retryIsWaiting
                ? `Automatic retry is available after ${retryTime}. You can manually retry now.`
                : 'You can retry this run now.'
              : 'Automatic retries stopped. You can manually retry from Background work.'}
          </p>
        ) : (
          <p className="hint">
            {topicOnly
              ? 'Daily discovery saves recent primary-source topics. Choose a topic below when you are ready to create a carousel.'
              : 'One source-backed, 8-slide draft each day. A configured OpenAI key is needed; every draft stays unapproved until you review it.'}
          </p>
        )}
      </div>
      {refresh || run?.status === 'completed' || run?.status === 'completed_with_warnings' ? (
        <div className="daily-run-actions">
          <button
            className="primary"
            disabled={busy || loading || refreshActive}
            onClick={onRegenerate}
          >
            {busy || refreshActive
              ? 'Researching…'
              : refresh?.status === 'failed'
                ? 'Retry research'
                : 'Refresh more topics'}
          </button>
          <p className="hint">Adds recent unused sources to your topic queue.</p>
        </div>
      ) : (
        <button
          className="primary"
          disabled={
            busy ||
            loading ||
            run?.status === 'running' ||
            (run?.status === 'failed' && run.attempt_count >= 3)
          }
          onClick={onRun}
        >
          {run?.status === 'running'
            ? 'Researching…'
            : run?.status === 'failed'
              ? 'Retry today’s run'
              : topicOnly
                ? 'Research today’s topics'
                : 'Prepare today’s carousel'}
        </button>
      )}
    </section>
  );
}
