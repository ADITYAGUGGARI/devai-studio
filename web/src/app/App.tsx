import { ProfileSettings } from '../features/ProfileSettings';
import { useState, useEffect } from 'react';
import { useBlocker, useNavigate } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { accountAtom } from './state';
import { useStudioRouting } from './routing';
import { PublishingWorkspace, OperationsWorkspace } from '../features/Workspace';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { PostEditor } from '../features/posts/PostEditor';
import { PostLibrary } from '../features/posts/PostLibrary';
import { DailyRunPanel } from '../features/research/DailyRunPanel';
import { ResearchDiscovery } from '../features/research/ResearchDiscovery';
import { GenerationForm } from '../features/research/GenerationForm';
import { request } from '../services/api';
import { TaskDock } from '../features/workflow/TaskDock';
import { JobPanel } from '../features/workflow/JobPanel';
import { TopicQueue } from '../features/workflow/TopicQueue';
import { ResearchSettings } from '../features/ResearchSettings';
import { CreateWizard } from '../features/content/CreateWizard';
import { ContentWorkspace, StudioContentLibrary } from '../features/content/ContentWorkspace';
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
  const routerNavigate = useNavigate();
  const {
    id,
    tab,
    contentId,
    setupId,
    outputFormat,
    editorTool,
    sceneId,
    navigateWorkspace: setTab,
    openPost,
  } = useStudioRouting();
  const account = useAtomValue(accountAtom);
  const canWrite = account?.role !== 'viewer';
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dirty, setDirty] = useState(false);
  const [leaveAction, setLeaveAction] = useState<(() => void) | null>(null);
  const blocker = useBlocker(dirty);
  useEffect(() => {
    function beforeUnload(event: BeforeUnloadEvent) {
      if (dirty) {
        event.preventDefault();
        event.returnValue = '';
      }
    }
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, [dirty]);
  function keepEditing() {
    if (blocker.state === 'blocked') blocker.reset();
    setLeaveAction(null);
  }
  function navigate(action: () => void, confirmLocalAction = false) {
    const next = () => {
      setNotice('');
      action();
    };
    if (dirty && confirmLocalAction) setLeaveAction(() => next);
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
  const {
    data: topics = [],
    error: topicsError,
    isPending: topicsLoading,
  } = useQuery({
    queryKey: ['topics'],
    queryFn: () => request<Topic[]>('/topics'),
    refetchInterval: 3000,
  });
  const { data: config } = useQuery({
    queryKey: ['workflow-config'],
    queryFn: () => request<WorkflowConfig>('/workflow/config'),
  });
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

  const create = () => setTab('Create');
  const generate = (source: SourceInput) =>
    run(async () => {
      const created = await request<{ id: string }>('/topics', 'POST', source);
      setManualSource(false);
      routerNavigate(`/discover/queue?topic=${encodeURIComponent(created.id)}`);
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
        })
      }
      onLogout={() =>
        navigate(() => {
          void request('/auth/logout', 'POST')
            .then(() => window.location.reload())
            .catch((cause) => setError(cause instanceof Error ? cause.message : 'Sign out failed'));
        }, true)
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
              setTab('Activity');
            })
          }
          onResearch={() =>
            navigate(() => {
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
              {tab === 'Create'
                ? 'Create your next story'
                : tab === 'ContentWorkspace'
                  ? 'Your content workspace'
                  : tab === 'ResearchSettings'
                    ? 'Research schedule'
                    : tab === 'Overview'
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
      {tab === 'Not found' || (id && !active && !isLoading) ? (
        <section className="panel">
          <h2>This destination is unavailable</h2>
          <p>The content may have been removed or you may not have access.</p>
          <button className="primary" onClick={() => setTab('Library')}>
            Open content library
          </button>
        </section>
      ) : tab === 'Create' ? (
        <CreateWizard key={setupId || 'new'} setupId={setupId} onDirtyChange={setDirty} />
      ) : tab === 'ContentWorkspace' && contentId ? (
        <ContentWorkspace
          key={contentId}
          contentId={contentId}
          outputFormat={outputFormat}
          editorTool={editorTool}
          initialSceneId={sceneId}
          onDirtyChange={setDirty}
        />
      ) : active ? (
        <PostEditor
          key={active.id}
          post={active}
          busy={busy}
          onBack={() =>
            navigate(() => {
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
      ) : tab === 'Profile' ? (
        <ProfileSettings onDirtyChange={setDirty} />
      ) : tab === 'ResearchSettings' ? (
        <ResearchSettings onDirtyChange={setDirty} />
      ) : tab === 'Operations' ? (
        <>
          <button className="secondary" onClick={() => setTab('Profile')}>
            Profile & preferences
          </button>
          <button className="secondary" onClick={() => setTab('ResearchSettings')}>
            Research schedule
          </button>
          <OperationsWorkspace busy={busy} onAction={run} />
        </>
      ) : tab === 'Overview' ? (
        <StudioOverview
          posts={data}
          topics={topics}
          jobs={jobs}
          onOpen={openPost}
          onNavigate={(name) => {
            setTab(name);
          }}
        />
      ) : tab === 'Research' ? (
        <>
          <ResearchDiscovery canWrite={canWrite} />
          <button className="secondary" onClick={() => setTab('Queue')}>
            Open editorial topic queue
          </button>
        </>
      ) : tab === 'Queue' ? (
        <>
          <TopicQueue
            topics={topics}
            loading={topicsLoading}
            busy={busy || !canWrite}
            onAction={run}
            onOpen={openPost}
            onViewActivity={() => {
              setTab('Activity');
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
        <>
          <StudioContentLibrary />
          <PostLibrary
            posts={data}
            loading={isLoading}
            busy={busy}
            onCreate={create}
            onSelect={(post) => {
              openPost(post.id);
            }}
          />
        </>
      ) : null}
      {(leaveAction || blocker.state === 'blocked') && (
        <Modal title="You have unsaved edits" onClose={keepEditing}>
          <p>
            Save your copy or slide changes before leaving, or discard these edits. Saved drafts and
            artwork will remain intact.
          </p>
          <div className="actions">
            <button className="primary" onClick={keepEditing}>
              Keep editing
            </button>
            <button
              className="secondary"
              onClick={() => {
                if (blocker.state === 'blocked') blocker.proceed();
                else leaveAction?.();
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
