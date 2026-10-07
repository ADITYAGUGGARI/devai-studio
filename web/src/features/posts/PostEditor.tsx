import { useState } from 'react';
import { downloadPost, request } from '../../services/api';
import type { Post, ReviewAction } from '../../types/posts';
import { SlidePreview } from './SlidePreview';

interface Props {
  post: Post;
  busy: boolean;
  onBack: () => void;
  onAction: (operation: () => Promise<unknown>) => Promise<void>;
}

export function PostEditor({ post, busy, onBack, onAction }: Props) {
  const [index, setIndex] = useState(0);
  const [title, setTitle] = useState(post.title);
  const [caption, setCaption] = useState(post.caption);
  const [headline, setHeadline] = useState(post.slides[0]?.headline || '');
  const [body, setBody] = useState(post.slides[0]?.body || '');
  const locked = busy || post.status === 'publishing' || post.status === 'published';
  const slide = post.slides[index];

  function changeSlide(position: number) {
    setIndex(position);
    setHeadline(post.slides[position]?.headline || '');
    setBody(post.slides[position]?.body || '');
  }

  function transition(action: ReviewAction) {
    return onAction(() => request(`/posts/${post.id}/${action}`, 'POST'));
  }

  return (
    <>
      <div className="reviewhead">
        <button className="ghost" disabled={busy} onClick={onBack}>
          ← Back to library
        </button>
        <span className={`pill ${post.status}`}>{post.status.replace('_', ' ')}</span>
      </div>
      <div className="reviewgrid">
        <SlidePreview slides={post.slides} index={index} onChange={changeSlide} />
        <section className="editor">
          <div className="panel">
            <h3>Post details · v{post.version}</h3>
            <label htmlFor="edit-title">Headline</label>
            <input
              id="edit-title"
              disabled={locked}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
            <label htmlFor="edit-caption">Caption</label>
            <textarea
              id="edit-caption"
              disabled={locked}
              rows={7}
              value={caption}
              onChange={(event) => setCaption(event.target.value)}
            />
            <button
              className="secondary"
              disabled={locked}
              onClick={() =>
                onAction(() => request(`/posts/${post.id}`, 'PATCH', { title, caption }))
              }
            >
              Save post
            </button>
          </div>
          <div className="panel">
            <h3>Selected slide</h3>
            <label htmlFor="edit-headline">Headline</label>
            <input
              id="edit-headline"
              disabled={locked || !slide}
              value={headline}
              onChange={(event) => setHeadline(event.target.value)}
            />
            <label htmlFor="edit-body">Body</label>
            <textarea
              id="edit-body"
              disabled={locked || !slide}
              rows={4}
              value={body}
              onChange={(event) => setBody(event.target.value)}
            />
            <button
              className="secondary"
              disabled={locked || !slide}
              onClick={() =>
                slide &&
                onAction(() =>
                  request(`/posts/${post.id}/slides/${slide.id}`, 'PATCH', { headline, body }),
                )
              }
            >
              Save slide
            </button>
            <button
              className="secondary"
              disabled={busy || !post.slides.length}
              onClick={() => onAction(() => downloadPost(post.id))}
            >
              Download 1080 × 1350 PNG ZIP
            </button>
          </div>
          <div className="panel">
            <h3>Approval workflow</h3>
            <p className="hint">
              Editing invalidates approval. Instagram publishing requires separate configuration.
            </p>
            <div className="actions">
              {post.status === 'draft' && (
                <button className="primary" disabled={busy} onClick={() => transition('submit')}>
                  Submit for review
                </button>
              )}
              {post.status === 'pending_review' && (
                <>
                  <button className="primary" disabled={busy} onClick={() => transition('approve')}>
                    Approve
                  </button>
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => transition('reject')}
                  >
                    Reject
                  </button>
                </>
              )}
              {post.status === 'rejected' && (
                <button className="primary" disabled={busy} onClick={() => transition('submit')}>
                  Resubmit
                </button>
              )}
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
