import type { Slide } from '../../types/posts';
import { useEffect, useState } from 'react';
import { loadSlidePreview } from '../../services/api';
export function ArtworkImage({
  postId,
  slide,
  alt,
}: {
  postId: string;
  slide: Slide | undefined;
  alt: string;
}) {
  const [url, setUrl] = useState('');
  const id = slide?.id,
    hash = slide?.validation?.image_sha256,
    hasArtwork = slide?.has_artwork;
  useEffect(() => {
    let active = true,
      objectUrl = '';
    setUrl('');
    if (id && hasArtwork) {
      void loadSlidePreview(postId, id)
        .then((value) => {
          if (active) {
            objectUrl = value;
            setUrl(value);
          } else URL.revokeObjectURL(value);
        })
        .catch(() => {
          if (active) setUrl('unavailable');
        });
    } else setUrl('unavailable');
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [postId, id, hash, hasArtwork]);
  return url && url !== 'unavailable' ? (
    <img src={url} alt={alt} />
  ) : (
    <div className="slide-preview-loading" role="status">
      {url === 'unavailable' ? 'No image yet' : 'Loading image…'}
    </div>
  );
}
export function SlidePreview({
  postId,
  slides,
  index,
  onChange,
}: {
  postId: string;
  slides: Slide[];
  index: number;
  onChange: (index: number) => void;
}) {
  return (
    <section
      className="preview desktop-preview"
      aria-label="Carousel preview"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'ArrowRight' && index < slides.length - 1) {
          e.preventDefault();
          onChange(index + 1);
        } else if (e.key === 'ArrowLeft' && index > 0) {
          e.preventDefault();
          onChange(index - 1);
        }
      }}
    >
      <div className="slidestrip" aria-label="Slide thumbnails">
        {slides.map((slide, position) => (
          <button
            key={slide.id}
            aria-label={`Slide ${position + 1}`}
            aria-pressed={index === position}
            className={index === position ? 'thumb chosen' : 'thumb'}
            onClick={() => onChange(position)}
          >
            <ArtworkImage postId={postId} slide={slide} alt="" />
            <span>{position + 1}</span>
          </button>
        ))}
      </div>
      <div className="artwork-canvas">
        <div className="canvas-toolbar">
          <button
            className="ghost"
            aria-label="Previous slide"
            disabled={index === 0}
            onClick={() => onChange(index - 1)}
          >
            ←
          </button>
          <span>
            Slide {index + 1} of {slides.length}
          </span>
          <button
            className="ghost"
            aria-label="Next slide"
            disabled={index >= slides.length - 1}
            onClick={() => onChange(index + 1)}
          >
            →
          </button>
          <span className="hint">4:5 · Instagram</span>
        </div>
        <div className="slide-preview-frame">
          <ArtworkImage
            postId={postId}
            slide={slides[index]}
            alt={`Slide ${index + 1}: ${slides[index]?.headline || ''}`}
          />
        </div>
        <p className="canvas-hint">Use ← → to browse slides. Review every image before approval.</p>
      </div>
    </section>
  );
}
