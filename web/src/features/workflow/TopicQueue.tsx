import { useAtomValue } from 'jotai';
import { accountAtom } from '../../app/state';
import { useState } from 'react';
import type { Topic } from '../../types/posts';
import { request } from '../../services/api';
interface Props {
  topics: Topic[];
  busy: boolean;
  onAction: (op: () => Promise<unknown>) => Promise<void>;
  onOpen: (id: string) => void;
  onBackgroundWork: () => void;
  onViewActivity: () => void;
  onAddSource: () => void;
}
export function TopicQueue({
  topics,
  busy,
  onAction,
  onOpen,
  onBackgroundWork,
  onViewActivity,
  onAddSource,
}: Props) {
  const account = useAtomValue(accountAtom),
    canReview = ['admin', 'reviewer'].includes(account?.role || '');
  const [selected, setSelected] = useState(''),
    [category, setCategory] = useState('all'),
    [query, setQuery] = useState('');
  const [count, setCount] = useState(8),
    [artwork, setArtwork] = useState(true),
    [showArchived, setShowArchived] = useState(false);
  const visible = topics.filter(
    (t) =>
      (category === 'all' || t.category === category) &&
      (showArchived || t.status !== 'archived') &&
      `${t.title} ${t.source}`.toLowerCase().includes(query.toLowerCase()),
  );
  const selectedId =
    visible.find((t) => t.id === selected)?.id ||
    visible.find((t) => t.selected)?.id ||
    visible[0]?.id ||
    '';
  const topic = topics.find((t) => t.id === selectedId),
    eligible = topic?.status === 'queued' && topic.verification !== 'unverified' && topic.approved;
  return (
    <section className="research-workbench" aria-labelledby="topic-heading">
      <div className="research-toolbar">
        <label className="topic-search">
          Search topics
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search stories or sources…"
          />
        </label>
        <label>
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="all">All categories</option>
            {['news', 'tutorial', 'architecture', 'tools', 'insight'].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show archived
        </label>
        <button className="secondary" disabled={busy} onClick={onAddSource}>
          Add your own source
        </button>
        <button
          className="primary"
          disabled={busy}
          onClick={() =>
            onAction(async () => {
              await request('/research/refresh', 'POST');
              onBackgroundWork();
            })
          }
        >
          Refresh research
        </button>
      </div>
      <div className="research-split">
        <div className="research-list">
          <div className="list-heading">
            <h2 id="topic-heading">Prioritized topic queue</h2>
            <span className="hint">{visible.length} stories</span>
          </div>
          <div className="ranked-topics">
            {visible.map((item, i) => (
              <label
                key={item.id}
                className={selectedId === item.id ? 'topic-row selected' : 'topic-row'}
              >
                <input
                  type="radio"
                  name="selected-topic"
                  aria-label={`Select ${item.title}`}
                  checked={selectedId === item.id}
                  disabled={busy}
                  onChange={() => {
                    setSelected(item.id);
                    if (item.status === 'queued')
                      void onAction(() => request(`/topics/${item.id}/select`, 'POST'));
                  }}
                />
                <span className="topic-rank">{String(i + 1).padStart(2, '0')}</span>
                <span className="topic-row-copy">
                  <strong>{item.title}</strong>
                  <small>
                    {item.source} · {item.category}
                  </small>
                  <span className="topic-row-meta">
                    {item.published_at
                      ? new Date(item.published_at).toLocaleDateString()
                      : 'Date not supplied'}
                    <span className="pill">{item.approved ? 'approved' : item.status}</span>
                  </span>
                </span>
              </label>
            ))}
          </div>
          {!visible.length && (
            <div className="list-empty">
              <h3>{query ? 'No matching stories' : 'Your next story starts here'}</h3>
              <p className="hint">
                Refresh research, search the web, or add an article you want to explain.
              </p>
            </div>
          )}
          <details className="web-search">
            <summary>Search current developer news</summary>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const q = new FormData(e.currentTarget).get('query');
                void onAction(async () => {
                  await request('/research/search', 'POST', { query: q });
                  onBackgroundWork();
                });
              }}
            >
              <label>
                Search current developer news
                <input
                  name="query"
                  minLength={5}
                  maxLength={300}
                  placeholder="AI coding agents, production RAG…"
                  required
                />
              </label>
              <button className="secondary" disabled={busy}>
                Search primary sources
              </button>
            </form>
          </details>
        </div>
        <div className="topic-detail" aria-label="Selected story">
          {topic ? (
            <>
              <div className="topic-detail-head">
                <span className="eyebrow">
                  {topic.category.toUpperCase()} · PRIORITY {topic.priority}
                </span>
                <span className="pill">{topic.verification.replaceAll('_', ' ')}</span>
              </div>
              <h2>{topic.title}</h2>
              <a className="source-link" href={topic.url} target="_blank" rel="noreferrer">
                {topic.source} ↗
              </a>
              <p className="hint">
                {topic.published_at
                  ? `Published ${new Date(topic.published_at).toLocaleDateString()}`
                  : 'Publication date not supplied'}{' '}
                · Evidence saved {new Date(topic.retrieved_at).toLocaleDateString()}
              </p>
              <details className="evidence-disclosure" key={topic.id}>
                <summary>Review saved evidence</summary>
                <p>{topic.excerpt}</p>
              </details>
              {topic.error && (
                <details className="evidence-disclosure">
                  <summary>Generation needs attention</summary>
                  <p className="run-warning">{topic.error}</p>
                </details>
              )}
              <div className="topic-decision">
                <h3>
                  {topic.approved
                    ? 'Ready to create your carousel'
                    : topic.verification === 'unverified'
                      ? 'Verify this source first'
                      : 'Review this topic'}
                </h3>
                <p className="hint">
                  {topic.approved
                    ? 'Generate original copy and complete AI-designed images. Your post stays a draft until you review it.'
                    : 'Read the saved evidence and original article before approving this story for generation.'}
                </p>
                {topic.status === 'queued' && (
                  <>
                    {topic.verification === 'unverified' ? (
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() =>
                          onAction(() => request(`/topics/${topic.id}/verify`, 'POST'))
                        }
                      >
                        I reviewed and verified this evidence
                      </button>
                    ) : !topic.approved ? (
                      <button
                        className="primary"
                        disabled={busy || !canReview}
                        onClick={() =>
                          onAction(() => request(`/topics/${topic.id}/approve`, 'POST'))
                        }
                      >
                        Approve topic
                      </button>
                    ) : null}
                    <div className="generation-options">
                      <label>
                        Slides
                        <select
                          aria-label="Slides"
                          value={count}
                          onChange={(e) => setCount(Number(e.target.value))}
                        >
                          {[6, 7, 8].map((n) => (
                            <option key={n}>{n}</option>
                          ))}
                        </select>
                      </label>
                      <label className="check">
                        <input
                          type="checkbox"
                          checked={artwork}
                          onChange={(e) => setArtwork(e.target.checked)}
                        />
                        Generate complete slide images
                      </label>
                    </div>
                    <button
                      className="primary"
                      disabled={busy || !eligible}
                      onClick={() =>
                        onAction(async () => {
                          await request(`/topics/${topic.id}/generate`, 'POST', {
                            slide_count: count,
                            artwork,
                          });
                          onBackgroundWork();
                        })
                      }
                    >
                      Generate selected topic · {count} slides →
                    </button>
                  </>
                )}
                {topic.post_id && (
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={() => onOpen(topic.post_id!)}
                  >
                    Open draft
                  </button>
                )}
                {topic.status === 'generating' && (
                  <button className="secondary" onClick={onViewActivity}>
                    View generation progress
                  </button>
                )}
              </div>
              {['queued', 'archived'].includes(topic.status) && (
                <details className="evidence-disclosure">
                  <summary>Topic options</summary>
                  <div className="topic-tools">
                    <label>
                      Priority (0–100)
                      <input
                        type="number"
                        aria-label={`Priority for ${topic.title}`}
                        min={0}
                        max={100}
                        key={`${topic.id}-${topic.priority}`}
                        defaultValue={topic.priority}
                        disabled={busy || topic.status !== 'queued'}
                        onBlur={(e) => {
                          const p = Number(e.target.value);
                          if (Number.isInteger(p) && p >= 0 && p <= 100 && p !== topic.priority)
                            void onAction(() =>
                              request(`/topics/${topic.id}`, 'PATCH', { priority: p }),
                            );
                        }}
                      />
                    </label>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() =>
                        onAction(() =>
                          request(`/topics/${topic.id}`, 'PATCH', {
                            status: topic.status === 'archived' ? 'queued' : 'archived',
                          }),
                        )
                      }
                    >
                      {topic.status === 'archived' ? 'Restore' : 'Archive'}
                    </button>
                  </div>
                  {topic.status === 'queued' && topic.verification === 'unverified' && (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const excerpt = new FormData(e.currentTarget).get('excerpt');
                        void onAction(() => request(`/topics/${topic.id}`, 'PATCH', { excerpt }));
                      }}
                    >
                      <label>
                        Reviewed source excerpt
                        <textarea
                          name="excerpt"
                          minLength={240}
                          maxLength={10000}
                          required
                          defaultValue={topic.excerpt}
                          key={topic.id}
                          rows={5}
                        />
                      </label>
                      <button className="secondary" disabled={busy}>
                        Save source evidence
                      </button>
                    </form>
                  )}
                </details>
              )}
            </>
          ) : (
            <div className="detail-empty">
              <span aria-hidden="true">⌕</span>
              <h2>Choose a story</h2>
              <p className="hint">
                Select a topic to review its source evidence and create a carousel.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
