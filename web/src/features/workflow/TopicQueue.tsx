import { useState } from 'react';
import type { Topic } from '../../types/posts';
import { request } from '../../services/api';

interface Props {
  topics: Topic[];
  busy: boolean;
  onAction: (operation: () => Promise<unknown>) => Promise<void>;
  onOpen: (id: string) => void;
}

export function TopicQueue({ topics, busy, onAction, onOpen }: Props) {
  const [selected, setSelected] = useState('');
  const [category, setCategory] = useState('all');
  const [count, setCount] = useState(8);
  const [artwork, setArtwork] = useState(true);
  const [showArchived, setShowArchived] = useState(false);
  const selectedId = selected || topics.find((item) => item.selected)?.id || '';
  const topic = topics.find((item) => item.id === selectedId);
  const eligible = topic?.status === 'queued' && topic.verification !== 'unverified';
  return (
    <section className="panel" aria-labelledby="topic-heading">
      <div className="sectiontitle">
        <h2 id="topic-heading">Prioritized topic queue</h2>
        <button
          className="secondary"
          disabled={busy}
          onClick={() => onAction(() => request('/research/refresh', 'POST'))}
        >
          Refresh research
        </button>
      </div>
      <p className="hint">
        Primary-source excerpts are saved with dates and citations. Rankings favor recent, practical
        engineering stories. Review a topic’s evidence before choosing it.
      </p>
      <div className="actions">
        <label>
          Category
          <select
            aria-label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="all">All categories</option>
            {['news', 'tutorial', 'architecture', 'tools', 'insight'].map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
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
          <input type="checkbox" checked={artwork} onChange={(e) => setArtwork(e.target.checked)} />
          Generate complete slide images
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show archived
        </label>
      </div>
      <div className="topic-list">
        {topics
          .filter(
            (item) =>
              (category === 'all' || item.category === category) &&
              (showArchived || item.status !== 'archived'),
          )
          .map((item) => (
            <div key={item.id} className="source-evidence">
              <label className="check">
                <input
                  type="radio"
                  name="selected-topic"
                  checked={selectedId === item.id}
                  onChange={() => {
                    setSelected(item.id);
                    void onAction(() => request(`/topics/${item.id}/select`, 'POST'));
                  }}
                  disabled={busy || item.status !== 'queued'}
                />
                <strong>{item.title}</strong>
              </label>
              <a href={item.url} target="_blank" rel="noreferrer">
                {item.source} · {item.category}
              </a>
              <span className="hint">
                {item.verification.replaceAll('_', ' ')} · {item.status} ·{' '}
                {item.published_at
                  ? new Date(item.published_at).toLocaleDateString()
                  : 'Publication date not supplied'}
              </span>
              <details>
                <summary>Review saved evidence</summary>
                <p>{item.excerpt}</p>
              </details>
              {item.status === 'queued' && item.verification === 'unverified' && (
                <details>
                  <summary>Update source evidence</summary>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const excerpt = new FormData(e.currentTarget).get('excerpt');
                      void onAction(() => request(`/topics/${item.id}`, 'PATCH', { excerpt }));
                    }}
                  >
                    <label>
                      Reviewed source excerpt
                      <textarea
                        name="excerpt"
                        minLength={240}
                        maxLength={10000}
                        required
                        defaultValue={item.excerpt}
                        rows={5}
                      />
                    </label>
                    <button className="secondary" disabled={busy}>
                      Save source evidence
                    </button>
                  </form>
                </details>
              )}
              {item.error && <p className="run-warning">{item.error}</p>}
              <div className="actions">
                <label>
                  Priority (0–100)
                  <input
                    aria-label={`Priority for ${item.title}`}
                    type="number"
                    min={0}
                    max={100}
                    key={`${item.id}-${item.priority}`}
                    defaultValue={item.priority}
                    disabled={busy || item.status !== 'queued'}
                    onBlur={(e) => {
                      const priority = Number(e.target.value);
                      if (
                        Number.isInteger(priority) &&
                        priority >= 0 &&
                        priority <= 100 &&
                        priority !== item.priority
                      )
                        void onAction(() => request(`/topics/${item.id}`, 'PATCH', { priority }));
                    }}
                  />
                </label>
                {item.verification === 'unverified' && item.status === 'queued' && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => onAction(() => request(`/topics/${item.id}/verify`, 'POST'))}
                  >
                    I reviewed and verified this evidence
                  </button>
                )}
                {item.post_id && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => onOpen(item.post_id!)}
                  >
                    Open draft
                  </button>
                )}
                {['queued', 'archived'].includes(item.status) && (
                  <button
                    className="ghost"
                    disabled={busy}
                    onClick={() =>
                      onAction(() =>
                        request(`/topics/${item.id}`, 'PATCH', {
                          status: item.status === 'archived' ? 'queued' : 'archived',
                        }),
                      )
                    }
                  >
                    {item.status === 'archived' ? 'Restore' : 'Archive'}
                  </button>
                )}
              </div>
            </div>
          ))}
        {!topics.length && (
          <p className="hint">Refresh research or add a source below to start your queue.</p>
        )}
      </div>
      <button
        className="primary"
        disabled={busy || !eligible}
        onClick={() =>
          onAction(() =>
            request(`/topics/${selectedId}/generate`, 'POST', { slide_count: count, artwork }),
          )
        }
      >
        Generate selected topic · {count} slides
      </button>
    </section>
  );
}
