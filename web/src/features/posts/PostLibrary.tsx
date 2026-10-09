import { useState } from 'react';
import type { Post } from '../../types/posts';
import { ArtworkImage } from './SlidePreview';
export function PostLibrary({
  posts,
  loading,
  busy,
  onSelect,
  onCreate,
}: {
  posts: Post[];
  loading: boolean;
  busy: boolean;
  onSelect: (post: Post) => void;
  onCreate: () => void;
}) {
  const [filter, setFilter] = useState('All'),
    [search, setSearch] = useState('');
  const visible = posts.filter(
    (p) =>
      p.title.toLowerCase().includes(search.toLowerCase()) &&
      (filter === 'All' ||
        (filter === 'Drafts'
          ? ['draft', 'rejected'].includes(p.status)
          : filter === 'Review'
            ? p.status === 'pending_review'
            : p.status === 'approved')),
  );
  return (
    <section aria-label="Content library">
      <div className="library-toolbar">
        <div className="view-tabs" role="tablist" aria-label="Library filters">
          {['All', 'Drafts', 'Review', 'Approved'].map((f) => (
            <button role="tab" aria-selected={filter === f} key={f} onClick={() => setFilter(f)}>
              {f}
            </button>
          ))}
        </div>
        <label className="library-search">
          Search drafts
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find a carousel…"
          />
        </label>
      </div>
      <h2 className="library-count">
        Your carousels <span className="hint">{visible.length} carousels</span>
      </h2>
      {loading ? (
        <p role="status">Loading your carousels…</p>
      ) : visible.length ? (
        <div className="cards">
          {visible.map((post) => (
            <button
              key={post.id}
              className="postcard"
              disabled={busy}
              aria-label={`Open carousel: ${post.title}`}
              onClick={() => onSelect(post)}
            >
              <div className="cardart">
                <ArtworkImage postId={post.id} slide={post.slides[0]} alt="" />
              </div>
              <div className="cardinfo">
                <span className={`pill ${post.status}`}>{post.status.replaceAll('_', ' ')}</span>
                <h3>{post.title}</h3>
                <p>
                  {post.slides.length} slides · Version {post.version}
                </p>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="empty">
          <h3>
            {search || filter !== 'All'
              ? 'No matching carousels'
              : 'Your next great post starts here.'}
          </h3>
          <p className="hint">Choose an approved story in Research or start an editable draft.</p>
          <button className="primary" disabled={busy} onClick={onCreate}>
            Create first draft
          </button>
        </div>
      )}
    </section>
  );
}
