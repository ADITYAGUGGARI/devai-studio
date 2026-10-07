import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { samplePost } from '../data/samplePost';
import { PostEditor } from '../features/posts/PostEditor';
import { PostLibrary } from '../features/posts/PostLibrary';
import { GenerationForm } from '../features/research/GenerationForm';
import { request } from '../services/api';
import type { Post, SourceInput } from '../types/posts';

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
  } = useQuery({ queryKey: ['posts'], queryFn: () => request<Post[]>('/posts') });
  const active = data.find((post) => post.id === id);

  async function run(operation: () => Promise<unknown>): Promise<void> {
    setBusy(true);
    setError('');
    try {
      await operation();
      await queryClient.invalidateQueries({ queryKey: ['posts'] });
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
  const generate = (source: SourceInput) => openDraft('/research/generate', source);
  const visibleError = error || queryError?.message;

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
          {active ? (
            <PostEditor
              key={active.id}
              post={active}
              busy={busy}
              onBack={() => setId(null)}
              onAction={run}
            />
          ) : (
            <>
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
