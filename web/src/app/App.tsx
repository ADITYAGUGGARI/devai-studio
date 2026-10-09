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
import { TaskDock } from '../features/workflow/TaskDock';
import { JobPanel } from '../features/workflow/JobPanel';
import { TopicQueue } from '../features/workflow/TopicQueue';
import { Modal } from '../components/Modal';
import { WorkspaceShell } from '../components/WorkspaceShell';
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
  const [notice, setNotice] = useState('');
  const [dirty, setDirty] = useState(false);
  const [leaveAction, setLeaveAction] = useState<(() => void) | null>(null);
  function navigate(action: () => void) {
    const next = () => {
      setNotice('');
      action();
    };
    if (dirty) setLeaveAction(() => next);
    else next();
  }
  const [manualSource, setManualSource] = useState(false);
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
    setNotice('');
    try {
      await operation();
      await Promise.all(
        ['posts', 'daily-run', 'jobs', 'topics', 'schedules', 'operations', 'versions'].map((key) =>
          queryClient.invalidateQueries({ queryKey: [key] }),
        ),
      );
      setNotice((current) => current || 'Workspace updated.');
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
  const generate = (source: SourceInput) =>
    run(async () => {
      await request('/topics', 'POST', source);
      setManualSource(false);
    });
  const runDaily = () => run(() => request('/research/daily/run', 'POST'));
  const regenerateResearch = () =>
    run(async () => {
      await request('/research/refresh', 'POST');
      setNotice('Research started. You can keep working while it runs.');
    });
  const visibleError = error || queryError?.message || jobsError?.message || topicsError?.message;

  return (
    <WorkspaceShell
      tab={tab}
      account={account}
      activeCount={
        jobs.filter((j) => ['queued', 'running', 'retry_wait'].includes(j.status)).length
      }
      onNavigate={(name) =>
        navigate(() => {
          setTab(name);
          setId(null);
        })
      }
      onLogout={() =>
        navigate(() => {
          void request('/auth/logout', 'POST')
            .then(() => window.location.reload())
            .catch((cause) => setError(cause instanceof Error ? cause.message : 'Sign out failed'));
        })
      }
    >
      {(busy || notice) && (
        <div className="action-feedback" role="status" aria-live="polite">
          {busy ? 'Updating your workspace…' : notice}
          {!busy && (
            <button
              className="ghost"
              aria-label="Dismiss success message"
              onClick={() => setNotice('')}
            >
              ×
            </button>
          )}
        </div>
      )}
      {tab !== 'Activity' && (
        <TaskDock
          jobs={jobs}
          busy={busy}
          canWrite={canWrite}
          onAction={run}
          onOpen={(id) => navigate(() => openPost(id))}
          onActivity={() =>
            navigate(() => {
              setId(null);
              setTab('Activity');
            })
          }
          onResearch={() =>
            navigate(() => {
              setId(null);
              setTab('Research');
            })
          }
        />
      )}
      {!active && (
        <div className="topline">
          <div>
            <div className="eyebrow">✳ CONTENT INTELLIGENCE</div>
            <h1>
              {tab === 'Overview'
                ? 'Your studio, today'
                : tab === 'Research'
                  ? 'Discover your next story'
                  : tab === 'Operations'
                    ? 'Workspace settings'
                    : tab === 'Library'
                      ? 'Content library'
                      : tab}
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
            <button className="primary" onClick={create} disabled={busy || !canWrite}>
              + New draft
            </button>
          )}
        </div>
      )}
      {visibleError && !manualSource && (
        <div className="error" role="alert">
          {visibleError}
        </div>
      )}
      {tab === 'Activity' && !active && (
        <JobPanel
          jobs={jobs}
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
          onBack={() =>
            navigate(() => {
              setId(null);
              setTab('Library');
            })
          }
          onDirtyChange={setDirty}
          onAction={run}
          jobs={jobs}
          config={config}
        />
      ) : tab === 'Publishing' ? (
        <PublishingWorkspace
          config={config}
          posts={data}
          busy={busy}
          onAction={run}
          onOpen={openPost}
        />
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
          <TopicQueue
            topics={topics}
            busy={busy || !canWrite}
            onAction={run}
            onOpen={openPost}
            onViewActivity={() => {
              setTab('Activity');
              setId(null);
            }}
            onBackgroundWork={() =>
              setNotice('Task started. Progress stays visible while you work.')
            }
            onAddSource={() => setManualSource(true)}
          />
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
      {leaveAction && (
        <Modal title="You have unsaved edits" onClose={() => setLeaveAction(null)}>
          <p>
            Save your copy or slide changes before leaving, or discard these edits. Saved drafts and
            artwork will remain intact.
          </p>
          <div className="actions">
            <button className="primary" onClick={() => setLeaveAction(null)}>
              Keep editing
            </button>
            <button
              className="secondary"
              onClick={() => {
                leaveAction();
                setDirty(false);
                setLeaveAction(null);
              }}
            >
              Discard edits and leave
            </button>
          </div>
        </Modal>
      )}
      {manualSource && (
        <Modal title="Add your own source" onClose={() => setManualSource(false)}>
          {visibleError && (
            <p className="error" role="alert">
              {visibleError}
            </p>
          )}
          <GenerationForm busy={busy || !canWrite} onGenerate={generate} />
        </Modal>
      )}
    </WorkspaceShell>
  );
}
