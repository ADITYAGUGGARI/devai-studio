import type { Slide } from '../../types/posts';

interface Props {
  slides: Slide[];
  index: number;
  onChange: (index: number) => void;
}

export function SlidePreview({ slides, index, onChange }: Props) {
  return (
    <section className="preview" aria-label="Carousel preview">
      <div className="slide">
        <div className="slidekicker">DEVAISTUDIO / AI ENGINEERING</div>
        <div className="slidecenter">
          <span className="micro">FIELD NOTES · {index + 1}</span>
          <h2>{slides[index]?.headline}</h2>
          <p>{slides[index]?.body || 'No slides yet.'}</p>
        </div>
        <div className="slidebottom">
          BUILD SMARTER. SHIP BETTER. {slides.length ? index + 1 : 0} / {slides.length}
        </div>
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
