import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';
import { request } from '../../services/api';

interface Run {
  id: string;
  jobId: string;
  status: string;
  windowStartUTC: string;
  windowEndUTC: string;
  coverage: Record<string, { status: string; captured?: number; error?: string }>;
  job: { progress: number; total: number; step: string; cancel_requested: boolean };
}
interface Finding {
  id: string;
  topicId: string | null;
  title: string;
  url: string;
  source: string;
  score: number;
  publishedAt: string | null;
  capturedAt: string;
  disposition: string;
  dimensions: Record<string, number>;
  evidence: { excerpt: string; claims_verified: boolean };
}
interface Page {
  items: Finding[];
  total: number;
  nextCursor: string | null;
}

export function ResearchDiscovery({ canWrite }: { canWrite: boolean }) {
  const cache = useQueryClient();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const selectedRun = params.get('run') || '';
  const query = params.get('q') || '';
  const disposition = params.get('disposition') ?? 'usable';
  const cursor = params.get('cursor') || '';
  function changeFilters(values: Record<string, string>, replace = false) {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        next.delete('cursor');
        for (const [key, value] of Object.entries(values)) next.set(key, value);
        return next;
      },
      { replace },
    );
  }
  function setCursor(value: string) {
    changeFilters({ cursor: value });
  }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const history = useInfiniteQuery({
    queryKey: ['research-runs'],
    initialPageParam: '',
    queryFn: ({ pageParam }) =>
      request<{ items: Run[]; nextCursor?: string | null }>(
        `/v1/research/runs?${new URLSearchParams({ cursor: pageParam })}`,
      ),
    getNextPageParam: (page) => page.nextCursor || undefined,
    refetchInterval: 3000,
  });
  const runs = history.data?.pages.flatMap((page) => page.items) || [];
  const selected = useQuery({
    queryKey: ['research-run', selectedRun],
    retry: false,
    enabled: Boolean(selectedRun),
    queryFn: () => request<Run>(`/v1/research/runs/${encodeURIComponent(selectedRun)}`),
    refetchInterval: 3000,
  });
  const run = selectedRun ? selected.data : runs[0];
  const results = useQuery({
    queryKey: ['research-findings', run?.id, query, disposition, cursor],
    enabled: Boolean(run),
    queryFn: () =>
      request<Page>(
        `/v1/research/runs/${run!.id}/findings?${new URLSearchParams({ q: query, disposition, cursor: String(cursor) })}`,
      ),
    refetchInterval: run?.status === 'running' ? 3000 : false,
  });
  async function mutate(path: string, body: unknown = {}) {
    setBusy(true);
    setError('');
    try {
      const result = await request<{ runId?: string }>(path, 'POST', body, {
        'Idempotency-Key': crypto.randomUUID(),
      });
      if (result.runId) {
        changeFilters({ run: result.runId });
      }
      await cache.invalidateQueries({ queryKey: ['research-runs'] });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Research could not start. Try again.');
    } finally {
      setBusy(false);
    }
  }
  const active = run && ['queued', 'running', 'retry_wait'].includes(run.status);
  return (
    <section className="panel discovery-workspace" aria-labelledby="discovery-title">
      <div className="section-head">
        <div>
          <h2 id="discovery-title">Developer AI news · Last 24 hours</h2>
          <p>
            Ranked source findings. Publication dates define freshness; collection time does not.
          </p>
        </div>
        <button
          className="primary"
          disabled={busy || !canWrite || Boolean(active)}
          onClick={() => void mutate('/v1/research/runs')}
        >
          Run research
        </button>
      </div>
      {(error || history.error || selected.error || results.error) && (
        <p className="error" role="alert">
          {error || history.error?.message || selected.error?.message || results.error?.message}
        </p>
      )}
      {history.isPending || (selectedRun && selected.isPending) ? (
        <p role="status">Loading research history…</p>
      ) : !run ? (
        <p>
          {selectedRun
            ? 'This research run is unavailable. It may belong to another workspace.'
            : 'No research runs yet. Start a run to collect findings from configured sources.'}
          {selectedRun && (
            <button className="secondary" onClick={() => changeFilters({ run: '' })}>
              Return to latest research
            </button>
          )}
        </p>
      ) : (
        <>
          <label>
            Research run
            <select
              value={run.id}
              onChange={(event) => {
                changeFilters({ run: event.target.value });
              }}
            >
              {selectedRun && !runs.some((item) => item.id === selectedRun) && (
                <option value={run.id}>
                  {new Date(run.windowEndUTC).toLocaleString()} · {run.status}
                </option>
              )}
              {runs.map((item) => (
                <option key={item.id} value={item.id}>
                  {new Date(item.windowEndUTC).toLocaleString()} · {item.status}
                </option>
              ))}
            </select>
          </label>
          {history.hasNextPage && (
            <button
              className="secondary"
              disabled={history.isFetchingNextPage}
              onClick={() => void history.fetchNextPage()}
            >
              {history.isFetchingNextPage ? 'Loading earlier runs…' : 'Load earlier research runs'}
            </button>
          )}
          <p className="muted">
            Window: {new Date(run.windowStartUTC).toLocaleString()} —{' '}
            {new Date(run.windowEndUTC).toLocaleString()}
          </p>
          {active && (
            <div role="status">
              <p>
                {run.job.cancel_requested
                  ? 'Cancelling at the next safe checkpoint…'
                  : run.job.step}{' '}
                · {run.job.progress}/{run.job.total} sources
              </p>
              <progress
                value={run.job.progress}
                max={run.job.total}
                aria-label="Source collection progress"
              />
              <button
                className="secondary"
                disabled={busy || run.job.cancel_requested || !canWrite}
                onClick={() => void mutate(`/v1/jobs/${run.jobId}/cancel`)}
              >
                Cancel research
              </button>
            </div>
          )}
          <div className="discovery-filters">
            <label>
              Search findings
              <input
                type="search"
                value={query}
                onChange={(event) => {
                  changeFilters({ q: event.target.value }, true);
                }}
                placeholder="Search titles"
              />
            </label>
            <label>
              Finding status
              <select
                value={disposition}
                onChange={(event) => {
                  changeFilters({ disposition: event.target.value });
                }}
              >
                <option value="usable">Current opportunities</option>
                <option value="">All captured findings</option>
                <option value="date_unverified">Date unverified</option>
                <option value="outside_window">Outside window</option>
                <option value="duplicate">Duplicates</option>
                <option value="excluded_irrelevant">Excluded</option>
                <option value="excluded_category">Outside category mix</option>
              </select>
            </label>
            <button className="secondary" onClick={() => void results.refetch()}>
              Refresh findings
            </button>
          </div>
          <p>{results.data?.total ?? 0} findings in this view · Highest priority first</p>
          {results.isPending ? (
            <p role="status">Loading findings…</p>
          ) : results.data?.items.length === 0 ? (
            <p>No matching findings. Change the filter to inspect all captured results.</p>
          ) : (
            results.data?.items.map((finding) => (
              <article className="finding-card" key={finding.id}>
                <div>
                  <span className="eyebrow">
                    {finding.source} · {finding.disposition.replaceAll('_', ' ')}
                  </span>
                  <h3>{finding.title}</h3>
                  <p>
                    Priority {finding.score}/100 ·{' '}
                    {finding.publishedAt
                      ? new Date(finding.publishedAt).toLocaleString()
                      : 'Publication date unverified'}
                  </p>
                </div>
                {finding.topicId && (
                  <button
                    className="secondary"
                    onClick={() =>
                      navigate(`/discover/queue?topic=${encodeURIComponent(finding.topicId!)}`)
                    }
                  >
                    Review this topic
                  </button>
                )}
                <details>
                  <summary>Why ranked here & source evidence</summary>
                  <dl>
                    {Object.entries(finding.dimensions).map(([dimension, value]) => (
                      <div key={dimension}>
                        <dt>{dimension.replaceAll('_', ' ')}</dt>
                        <dd>{Math.round(value * 100)}%</dd>
                      </div>
                    ))}
                  </dl>
                  <p>{finding.evidence.excerpt || 'No readable excerpt was supplied.'}</p>
                  <p>Feed excerpt; claims require verification before generation and review.</p>
                  <p>Collected {new Date(finding.capturedAt).toLocaleString()}</p>
                  <a href={finding.url} target="_blank" rel="noreferrer">
                    Open original source ↗
                  </a>
                </details>
              </article>
            ))
          )}
          <div className="actions">
            <button className="secondary" disabled={!cursor} onClick={() => setCursor('')}>
              First page
            </button>
            <button
              className="secondary"
              disabled={results.data?.nextCursor == null}
              onClick={() => setCursor(results.data!.nextCursor!)}
            >
              Next
            </button>
          </div>
          <details>
            <summary>Coverage and limitations</summary>
            <p>Configured source feeds only. This is not exhaustive internet coverage.</p>
            <ul>
              {Object.entries(run.coverage).map(([name, item]) => (
                <li key={name}>
                  {name}: {item.status}
                  {item.error ? ` · ${item.error}` : ` · ${item.captured ?? 0} captured`}
                </li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}
