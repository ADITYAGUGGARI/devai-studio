import { useEffect, useState, useRef } from 'react';
import { useAtomValue } from 'jotai';
import { accountAtom } from '../../app/state';
import { downloadPost, request } from '../../services/api';
import type { Job, Post, ReviewAction, WorkflowConfig } from '../../types/posts';
import { SlidePreview } from './SlidePreview';
import { VersionHistory } from './VersionHistory';

interface Props {
  post: Post;
  busy: boolean;
  jobs: Job[];
  config?: WorkflowConfig;
  onBack: () => void;
  onAction: (operation: () => Promise<unknown>) => Promise<void>;
}

export function PostEditor({ post, busy, jobs, config, onBack, onAction }: Props) {
  const account = useAtomValue(accountAtom);
  const canReview = ['admin', 'reviewer'].includes(account?.role || '');
  const [index, setIndex] = useState(0);
  const [inspector, setInspector] = useState<'Slide' | 'Copy' | 'Approval' | 'History'>('Slide');
  const [title, setTitle] = useState(post.title);
  const [caption, setCaption] = useState(post.caption);
  const [headline, setHeadline] = useState(post.slides[0]?.headline || '');
  const [body, setBody] = useState(post.slides[0]?.body || '');
  const [reviewed, setReviewed] = useState(false);
  useEffect(() => setReviewed(false), [post.version]);
  const previousVersion = useRef(post.version);
  useEffect(() => {
    if (previousVersion.current === post.version) return;
    previousVersion.current = post.version;
    setTitle(post.title);
    setCaption(post.caption);
    setHeadline(post.slides[index]?.headline || '');
    setBody(post.slides[index]?.body || '');
  }, [post.version, post.title, post.caption, post.slides, index]);
  const [confirmedPublished, setConfirmedPublished] = useState(false);
  const [externalId, setExternalId] = useState('');
  const [reconcileNote, setReconcileNote] = useState('');
  const jobActive = jobs.some(
    (job) =>
      job.payload.post_id === post.id && ['queued', 'running', 'retry_wait'].includes(job.status),
  );
  const locked =
    busy ||
    account?.role === 'viewer' ||
    jobActive ||
    post.status === 'publishing' ||
    post.status === 'published';
  const ready = Boolean(
    post.evidence &&
    post.verification?.supported &&
    post.caption.includes(post.evidence.source_url) &&
    post.slides.length >= 6 &&
    post.slides.length <= 8 &&
    post.slides.every(
      (item) =>
        item.artwork_current && item.composition_mode === 'ai_native' && item.validation?.passed,
    ),
  );
  const slide = post.slides[index];

  function changeSlide(position: number) {
    setIndex(position);
    setHeadline(post.slides[position]?.headline || '');
    setBody(post.slides[position]?.body || '');
  }

  function transition(action: ReviewAction) {
    return onAction(async () => {
      await request(`/posts/${post.id}/${action}`, 'POST');
      setInspector('Approval');
    });
  }

  return (
    <>
      <div className="reviewhead editor-heading">
        <button className="ghost" disabled={busy} onClick={onBack}>
          ← Back to library
        </button>
        <div className="editor-title">
          <h1>Review content</h1>
          <h2>{post.title}</h2>
          <span className={`pill ${post.status}`}>{post.status.replace('_', ' ')}</span>
          <span className="hint">
            Version {post.version} · {post.slides.length} slides
          </span>
        </div>
        <div className="actions">
          {' '}
          <button
            className="secondary"
            disabled={
              busy ||
              !post.slides.length ||
              post.slides.some(
                (item) => !item.artwork_current || item.composition_mode !== 'ai_native',
              )
            }
            onClick={() => onAction(() => downloadPost(post.id))}
          >
            Download 1080 × 1350 PNG ZIP
          </button>
          {['draft', 'rejected'].includes(post.status) && (
            <button className="primary" disabled={locked} onClick={() => transition('submit')}>
              {post.status === 'rejected' ? 'Resubmit' : 'Submit for review'}
            </button>
          )}
        </div>
      </div>
      {jobs
        .filter(
          (job) =>
            job.payload.post_id === post.id &&
            ['queued', 'running', 'retry_wait'].includes(job.status),
        )
        .map((job) => (
          <div key={job.id} className="panel" role="status">
            <strong>
              {job.kind.replaceAll('_', ' ')} · {job.status.replaceAll('_', ' ')}
            </strong>
            <p className="hint">
              {job.step} · attempt {job.attempts}/{job.max_attempts}
            </p>
            <progress aria-label={`${job.kind} progress`} value={job.progress} max={job.total} />
            <p className="hint">
              You can leave this screen; work continues in the background. Open Activity for
              details.
            </p>
          </div>
        ))}
      {!post.verification?.supported && (
        <div className="panel">
          <p className="run-warning">Current copy needs source grounding before approval.</p>
          <button
            className="secondary"
            disabled={locked}
            onClick={() => onAction(() => request(`/posts/${post.id}/verify`, 'POST'))}
          >
            Verify current copy against source
          </button>
        </div>
      )}
      <div className="reviewgrid">
        <SlidePreview postId={post.id} slides={post.slides} index={index} onChange={changeSlide} />
        <section className="editor inspector" aria-label="Carousel inspector">
          <div className="inspector-tabs" role="tablist" aria-label="Editor sections">
            {(['Slide', 'Copy', 'Approval', 'History'] as const).map((name) => (
              <button
                key={name}
                role="tab"
                aria-selected={inspector === name}
                id={`inspector-${name}`}
                aria-controls="inspector-content"
                onClick={() => setInspector(name)}
              >
                {name}
              </button>
            ))}
          </div>
          <div id="inspector-content" role="tabpanel" aria-labelledby={`inspector-${inspector}`}>
            {inspector === 'History' && (
              <VersionHistory
                id={post.id}
                version={post.version}
                locked={locked}
                onAction={onAction}
              />
            )}
            {inspector === 'Copy' && (
              <>
                <div className="panel">
                  <h3>Post details · v{post.version}</h3>
                  {post.evidence && (
                    <div className="source-evidence">
                      <strong>Source evidence · {post.evidence.topic}</strong>
                      <a href={post.evidence.source_url} target="_blank" rel="noreferrer">
                        {post.evidence.source_name}: {post.evidence.source_title}
                      </a>
                      <p className="hint">Angle: {post.evidence.editorial_angle}</p>
                      <details>
                        <summary>Review source excerpt</summary>
                        <p>{post.evidence.excerpt}</p>
                      </details>
                      <span className="hint">
                        Published{' '}
                        {post.evidence.published_at
                          ? new Date(post.evidence.published_at).toLocaleString()
                          : 'date unavailable'}{' '}
                        · Retrieved {new Date(post.evidence.retrieved_at).toLocaleString()}
                      </span>
                    </div>
                  )}
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
              </>
            )}
            {inspector === 'Slide' && (
              <>
                <div className="panel">
                  <h3>Slide artwork</h3>
                  <p className="hint">
                    AI designs the entire image for every slide, including typography and diagrams.
                    Each image is checked against the saved copy. Regeneration replaces the artwork
                    and requires a new review.
                  </p>
                  <button
                    className="secondary"
                    disabled={locked || busy || !post.slides.length}
                    onClick={() => onAction(() => request(`/posts/${post.id}/artwork`, 'POST'))}
                  >
                    {jobActive
                      ? 'Artwork job in progress…'
                      : post.slides.every((item) => item.has_artwork)
                        ? 'Regenerate AI artwork for all slides'
                        : 'Create unique AI artwork for all slides'}
                  </button>
                  {slide && (
                    <>
                      <button
                        className="secondary"
                        disabled={locked}
                        onClick={() =>
                          onAction(() =>
                            request(`/posts/${post.id}/slides/${slide.id}/regenerate`, 'POST'),
                          )
                        }
                      >
                        Regenerate selected slide
                      </button>
                      <p
                        className={
                          slide.validation?.passed && slide.artwork_current ? 'hint' : 'run-warning'
                        }
                      >
                        {!slide.artwork_current
                          ? 'Image missing or stale after a copy change.'
                          : slide.validation?.passed
                            ? 'Image validation passed. Human visual review is still required.'
                            : 'Image validation failed or has not run.'}
                      </p>
                      {slide.validation?.issues.map((issue, i) => (
                        <p className="run-warning" key={i}>
                          {issue}
                        </p>
                      ))}
                      {slide.composition_mode === 'legacy' && (
                        <p className="run-warning">
                          This older slide used a text overlay. Regenerate it for a complete
                          AI-native composition.
                        </p>
                      )}
                    </>
                  )}
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
                        request(`/posts/${post.id}/slides/${slide.id}`, 'PATCH', {
                          headline,
                          body,
                        }),
                      )
                    }
                  >
                    Save slide
                  </button>
                </div>
              </>
            )}
            {inspector === 'Approval' && (
              <div className="panel">
                <h3>Approval workflow</h3>
                <p className="hint">
                  Verify every source claim, citation, code example, and complete slide image.
                  Editing or regenerating images invalidates approval.
                </p>
                {post.verification && (
                  <details>
                    <summary>Source grounding audit</summary>
                    <p className="hint">
                      {post.verification.supported
                        ? 'Factual claims passed the evidence check.'
                        : 'Grounding check needs review.'}
                    </p>
                    {post.verification.issues.map((issue, i) => (
                      <p key={i}>{issue}</p>
                    ))}
                  </details>
                )}
                {!ready && (
                  <p className="run-warning">
                    Approval requires source evidence, citation, and a current validated AI image
                    for all 6–8 slides.
                  </p>
                )}
                <label className="check">
                  <input
                    type="checkbox"
                    checked={reviewed}
                    onChange={(e) => setReviewed(e.target.checked)}
                    disabled={locked}
                  />
                  I reviewed the sources, copy, code and all slide images.
                </label>
                <div className="actions">
                  {post.status === 'pending_review' && (
                    <>
                      <button
                        className="primary"
                        disabled={locked || !canReview || !ready || !reviewed}
                        onClick={() => transition('approve')}
                      >
                        Approve
                      </button>
                      <button
                        className="secondary"
                        disabled={locked || !canReview}
                        onClick={() => transition('reject')}
                      >
                        Reject
                      </button>
                    </>
                  )}
                  {post.status === 'approved' && (
                    <button
                      className="primary"
                      disabled={
                        locked ||
                        !canReview ||
                        !config?.instagram_configured ||
                        !config?.public_media_configured
                      }
                      onClick={() => onAction(() => request(`/posts/${post.id}/publish`, 'POST'))}
                    >
                      Publish approved carousel to Instagram
                    </button>
                  )}
                </div>
                {post.status === 'approved' &&
                  (!config?.instagram_configured || !config?.public_media_configured) && (
                    <p className="hint">
                      Configure Instagram credentials and the API’s public HTTPS media address to
                      publish this approved version.
                    </p>
                  )}
                {post.status === 'publishing' && !jobActive && (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      void onAction(() =>
                        request(`/posts/${post.id}/reconcile`, 'POST', {
                          published: confirmedPublished,
                          external_id: externalId || null,
                          note: reconcileNote,
                        }),
                      );
                    }}
                  >
                    <h3>Reconcile Instagram outcome</h3>
                    <p className="run-warning">
                      Check the Instagram account and Meta activity before confirming the result. An
                      uncertain publish is never retried automatically.
                    </p>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={confirmedPublished}
                        onChange={(e) => setConfirmedPublished(e.target.checked)}
                      />
                      I confirmed this carousel was published
                    </label>
                    <label htmlFor="instagram-id">Instagram media ID (required if published)</label>
                    <input
                      id="instagram-id"
                      value={externalId}
                      onChange={(e) => setExternalId(e.target.value)}
                      required={confirmedPublished}
                    />
                    <label htmlFor="reconcile-note">Verification notes</label>
                    <textarea
                      id="reconcile-note"
                      minLength={10}
                      required
                      value={reconcileNote}
                      onChange={(e) => setReconcileNote(e.target.value)}
                    />
                    <button className="secondary" disabled={busy || reconcileNote.length < 10}>
                      Save verified outcome
                    </button>
                  </form>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </>
  );
}
