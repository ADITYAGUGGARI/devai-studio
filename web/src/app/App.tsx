import { useState } from 'react';
import { useAtom, useAtomValue } from 'jotai';
import { accountAtom, selectedPostAtom, navigationAtom } from './state';
import { PublishingWorkspace, OperationsWorkspace } from '../features/Workspace';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { samplePost } from '../data/samplePost';
import { PostEditor } from '../features/posts/PostEditor';
import { PostLibrary } from '../features/posts/PostLibrary';
import { DailyRunPanel } from '../features/research/DailyRunPanel';
import { GenerationForm } from '../features/research/GenerationForm';
import { request } from '../services/api';
import { JobPanel } from '../features/workflow/JobPanel';
import { TopicQueue } from '../features/workflow/TopicQueue';
import { StudioOverview } from '../features/StudioOverview';
import type {
  Job,
  Topic,
  WorkflowConfig,
  DailyRunSummary,
  Post,
  SourceInput,
} from '../types/posts';

export function App() {
  const queryClient = useQueryClient();
  const [id, setId] = useAtom(selectedPostAtom);
  const [tab, setTab] = useAtom(navigationAtom);
  const account = useAtomValue(accountAtom);
  const canWrite = account?.role !== 'viewer';
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const {
    data = [],
    isLoading,
    error: queryError,
  } = useQuery({
    queryKey: ['posts'],
    queryFn: () => request<Post[]>('/posts'),
    refetchInterval: 3000,
  });
  const { data: daily, isLoading: dailyLoading } = useQuery({
    queryKey: ['daily-run'],
    queryFn: () => request<DailyRunSummary>('/research/daily/latest'),
    refetchInterval: 3000,
  });
  const { data: jobs = [], error: jobsError } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => request<Job[]>('/jobs'),
    refetchInterval: 2000,
  });
  const { data: topics = [], error: topicsError } = useQuery({
    queryKey: ['topics'],
    queryFn: () => request<Topic[]>('/topics'),
    refetchInterval: 3000,
  });
  const { data: config } = useQuery({
    queryKey: ['workflow-config'],
    queryFn: () => request<WorkflowConfig>('/workflow/config'),
  });
  function openPost(postId: string) {
    setId(postId);
    setTab('Library');
  }
  const active = data.find((post) => post.id === id);

  async function run(operation: () => Promise<unknown>): Promise<void> {
    setBusy(true);
    setError('');
    try {
      await operation();
      await queryClient.invalidateQueries({ queryKey: ['posts'] });
      await queryClient.invalidateQueries({ queryKey: ['daily-run'] });
      await queryClient.invalidateQueries({ queryKey: ['jobs'] });
      await queryClient.invalidateQueries({ queryKey: ['topics'] });
      await queryClient.invalidateQueries({ queryKey: ['schedules'] });
      await queryClient.invalidateQueries({ queryKey: ['operations'] });
      await queryClient.invalidateQueries({ queryKey: ['versions'] });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Something went wrong');
    } finally {
      setBusy(false);
    }
  }

  async function openDraft(path: string, payload: unknown) {
    await run(async () => {
      const draft = await request<{ id: string }>(path, 'POST', payload);
      setId(draft.id);
      setTab('Library');
    });
  }

  const create = () => openDraft('/posts', samplePost);
  const generate = (source: SourceInput) => run(() => request('/topics', 'POST', source));
  const runDaily = () => run(() => request('/research/daily/run', 'POST'));
  const regenerateResearch = () =>
    run(async () => {
      await request('/research/refresh', 'POST');
      setTab('Activity');
    });
  const visibleError = error || queryError?.message || jobsError?.message || topicsError?.message;

  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span className="brandmark">✳</span>devai studio
        </div>
        <div className="workspace">WORKSPACE</div>
        <nav>
          {['Overview', 'Research', 'Library', 'Publishing', 'Activity', 'Operations'].map(
            (name) => (
              <button
                key={name}
                disabled={busy}
                className={tab === name ? 'nav active' : 'nav'}
                onClick={() => {
                  setTab(name);
                  setId(null);
                }}
              >
                {name}
              </button>
            ),
          )}
        </nav>
        <div className="sidefoot">Creator workspace · Private review</div>
      </aside>
      <main>
        <header>
          <span>Workspace / {tab}</span>
          <span>✓ Approval required</span>
          <span className="hint">
            {account?.email} · {account?.role}
          </span>
          <button
            className="ghost"
            onClick={async () => {
              await request('/auth/logout', 'POST');
              window.location.reload();
            }}
          >
            Sign out
          </button>
        </header>
        <nav className="mobile-nav" aria-label="Workspace navigation">
          {['Overview', 'Research', 'Library', 'Publishing', 'Activity', 'Operations'].map(
            (name) => (
              <button
                key={name}
                aria-current={tab === name ? 'page' : undefined}
                className={tab === name ? 'nav active' : 'nav'}
                onClick={() => {
                  setTab(name);
                  setId(null);
                }}
              >
                {name}
              </button>
            ),
          )}
        </nav>
        <div className="content">
          <div className="topline">
            <div>
              <div className="eyebrow">✳ CONTENT INTELLIGENCE</div>
              <h1>
                {active ? 'Review content' : tab === 'Overview' ? 'Good morning, creator.' : tab}
              </h1>
              <p className="subtitle">
                {active
                  ? 'Review one carousel, one version at a time.'
                  : tab === 'Overview'
                    ? 'Your content studio. One clear next step.'
                    : tab === 'Research'
                      ? 'Choose a credible story worth explaining.'
                      : tab === 'Library'
                        ? 'Pick up a draft where you left off.'
                        : tab === 'Activity'
                          ? 'Background progress and recovery, in one place.'
                          : 'Your developer content workspace.'}
              </p>
            </div>
            {tab === 'Library' && !active && (
              <button className="primary" onClick={create} disabled={busy}>
                + New draft
              </button>
            )}
          </div>
          {visibleError && (
            <div className="error" role="alert">
              {visibleError}
            </div>
          )}
          {(active || tab === 'Activity') && (
            <JobPanel
              jobs={
                active
                  ? jobs.filter(
                      (job) =>
                        job.payload.post_id === active.id &&
                        String(job.payload.version) === active.version,
                    )
                  : jobs
              }
              config={config}
              busy={busy || !canWrite}
              onAction={run}
              onOpen={openPost}
            />
          )}
          {active ? (
            <PostEditor
              key={active.id}
              post={active}
              busy={busy}
              onBack={() => setId(null)}
              onAction={run}
              jobs={jobs}
              config={config}
            />
          ) : tab === 'Publishing' ? (
            <PublishingWorkspace posts={data} busy={busy} onAction={run} onOpen={openPost} />
          ) : tab === 'Operations' ? (
            <OperationsWorkspace busy={busy} onAction={run} />
          ) : tab === 'Overview' ? (
            <StudioOverview
              posts={data}
              topics={topics}
              jobs={jobs}
              onOpen={openPost}
              onNavigate={(name) => {
                setTab(name);
                setId(null);
              }}
            />
          ) : tab === 'Research' ? (
            <>
              <details className="panel research-status">
                <summary>Daily research status</summary>
                <DailyRunPanel
                  summary={daily}
                  loading={dailyLoading}
                  busy={busy}
                  onRun={runDaily}
                  onRegenerate={regenerateResearch}
                />
              </details>
              <TopicQueue
                topics={topics}
                busy={busy || !canWrite}
                onAction={run}
                onOpen={openPost}
                onBackgroundWork={() => setTab('Activity')}
              />
              <details className="panel">
                <summary>Add your own source</summary>
                <GenerationForm busy={busy || !canWrite} onGenerate={generate} />
              </details>
            </>
          ) : tab === 'Library' ? (
            <PostLibrary
              posts={data}
              loading={isLoading}
              busy={busy}
              onCreate={create}
              onSelect={(post) => {
                setId(post.id);
                setTab('Library');
              }}
            />
          ) : null}
        </div>
      </main>
    </div>
  );
}
