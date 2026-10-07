import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { samplePost } from '../data/samplePost';
import { PostEditor } from '../features/posts/PostEditor';
import { PostLibrary } from '../features/posts/PostLibrary';
import { DailyRunPanel } from '../features/research/DailyRunPanel';
import { GenerationForm } from '../features/research/GenerationForm';
import { request } from '../services/api';
import { JobPanel } from '../features/workflow/JobPanel';
import { TopicQueue } from '../features/workflow/TopicQueue';
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
  const [id, setId] = useState<string | null>(null);
  const [tab, setTab] = useState('Overview');
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
  const regenerateResearch = () => run(() => request('/research/refresh', 'POST'));
  const visibleError = error || queryError?.message || jobsError?.message || topicsError?.message;

  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span className="brandmark">✳</span>devai studio
        </div>
        <div className="workspace">WORKSPACE</div>
        <nav>
          {['Overview', 'Library'].map((name) => (
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
          ))}
        </nav>
        <div className="sidefoot">Creator workspace · Private review</div>
      </aside>
      <main>
        <header>
          <span>Workspace / {tab}</span>
          <span>✓ Approval required</span>
        </header>
        <div className="content">
          <div className="topline">
            <div>
              <div className="eyebrow">✳ CONTENT INTELLIGENCE</div>
              <h1>
                {active ? 'Review content' : tab === 'Overview' ? 'Good morning, creator.' : tab}
              </h1>
              <p className="subtitle">Turn emerging AI stories into exceptional content.</p>
            </div>
            <button className="primary" onClick={create} disabled={busy}>
              + New draft
            </button>
          </div>
          {visibleError && (
            <div className="error" role="alert">
              {visibleError}
            </div>
          )}
          <JobPanel jobs={jobs} config={config} busy={busy} onAction={run} onOpen={openPost} />
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
          ) : (
            <>
              <DailyRunPanel
                summary={daily}
                loading={dailyLoading}
                busy={busy}
                onRun={runDaily}
                onRegenerate={regenerateResearch}
              />
              <TopicQueue topics={topics} busy={busy} onAction={run} onOpen={openPost} />
              <GenerationForm busy={busy} onGenerate={generate} />
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
            </>
          )}
        </div>
      </main>
    </div>
  );
}
