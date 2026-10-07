import type { Post } from '../../types/posts';

interface Props {
  posts: Post[];
  loading: boolean;
  busy: boolean;
  onSelect: (post: Post) => void;
  onCreate: () => void;
}

export function PostLibrary({ posts, loading, busy, onSelect, onCreate }: Props) {
  return (
    <>
      <div className="stats">
        <div className="stat">
          <span>Total posts</span>
          <strong>{posts.length}</strong>
        </div>
        <div className="stat">
          <span>Needs review</span>
          <strong>{posts.filter((post) => post.status === 'pending_review').length}</strong>
        </div>
        <div className="stat">
          <span>Approved</span>
          <strong>{posts.filter((post) => post.status === 'approved').length}</strong>
        </div>
      </div>
      <h2>Content library</h2>
      {loading ? (
        <p>Loading…</p>
      ) : posts.length === 0 ? (
        <div className="empty">
          <h3>Your next great post starts here.</h3>
          <button className="primary" disabled={busy} onClick={onCreate}>
            Create first draft
          </button>
        </div>
      ) : (
        <div className="cards">
          {posts.map((post) => (
            <button
              key={post.id}
              className="postcard"
              disabled={busy}
              onClick={() => onSelect(post)}
            >
              <div className="cardart">
                <span>AI / ENGINEERING</span>
                <strong>{post.slides[0]?.headline || post.title}</strong>
                <small>{post.slides.length} SLIDES</small>
              </div>
              <div className="cardinfo">
                <span className={`pill ${post.status}`}>{post.status.replace('_', ' ')}</span>
                <h3>{post.title}</h3>
                <p>{new Date(post.created).toLocaleDateString()}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </>
  );
}
