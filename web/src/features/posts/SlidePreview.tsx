import type { Slide } from '../../types/posts';
import { useEffect, useState } from 'react';
import { loadSlidePreview } from '../../services/api';

interface Props {
  postId: string;
  slides: Slide[];
  index: number;
  onChange: (index: number) => void;
}

export function SlidePreview({ postId, slides, index, onChange }: Props) {
  const slide = slides[index];
  const slideId = slide?.id;
  const imageHash = slide?.validation?.image_sha256;
  const hasArtwork = slide?.has_artwork;
  const [imageUrl, setImageUrl] = useState('');
  useEffect(() => {
    let active = true;
    let objectUrl = '';
    setImageUrl('');
    if (slideId && hasArtwork) {
      void loadSlidePreview(postId, slideId)
        .then((url) => {
          if (active) {
            objectUrl = url;
            setImageUrl(url);
          } else {
            URL.revokeObjectURL(url);
          }
        })
        .catch(() => {
          if (active) setImageUrl('unavailable');
        });
    } else {
      setImageUrl('unavailable');
    }
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [postId, slideId, imageHash, hasArtwork]);
  return (
    <section className="preview" aria-label="Carousel preview">
      <div className="slide-preview-frame">
        {imageUrl && imageUrl !== 'unavailable' ? (
          <img src={imageUrl} alt={`Slide ${index + 1}: ${slide?.headline || ''}`} />
        ) : imageUrl === 'unavailable' ? (
          <div className="slide-preview-loading">
            No image yet. Generate or regenerate this slide in the editor.
          </div>
        ) : (
          <div className="slide-preview-loading">Loading slide preview…</div>
        )}
      </div>
      <div className="slidestrip">
        {slides.map((slide, position) => (
          <button
            key={slide.id}
            aria-label={`Slide ${position + 1}`}
            aria-pressed={index === position}
            className={index === position ? 'thumb chosen' : 'thumb'}
            onClick={() => onChange(position)}
          >
            {position + 1}
          </button>
        ))}
      </div>
    </section>
  );
}
