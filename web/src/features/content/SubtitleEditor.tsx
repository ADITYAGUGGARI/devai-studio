import { useState } from 'react';
import { subtitleCues, type StudioOutput } from '../../../../shared/content';

export function SubtitleEditor({
  output,
  disabled,
  onChange,
}: {
  output: StudioOutput;
  disabled: boolean;
  onChange: (value: StudioOutput) => void;
}) {
  const [selected, setSelected] = useState('');
  const cues = subtitleCues(output);
  const index = Math.max(
    0,
    cues.findIndex((cue, position) => (cue.id || String(position)) === selected),
  );
  const cue = cues[index];
  const edit = (change: Partial<typeof cue>) =>
    onChange({
      ...output,
      data: {
        ...output.data,
        subtitleCues: cues.map((item, position) =>
          position === index ? { ...item, ...change } : item,
        ),
      },
    });
  const style = output.data.subtitleStyle || {
    fontSize: 52,
    position: 'lower' as const,
    bold: false,
    background: false,
  };
  const styleChange = (change: Partial<typeof style>) =>
    onChange({ ...output, data: { ...output.data, subtitleStyle: { ...style, ...change } } });
  return (
    <section aria-label="Subtitle cues">
      <h3>Subtitle cues</h3>
      <label>
        Selected subtitle cue
        <select
          value={cue?.id || String(index)}
          onChange={(event) => setSelected(event.target.value)}
        >
          {cues.map((item, position) => (
            <option key={item.id || position} value={item.id || String(position)}>
              Cue {position + 1} · {item.start}–{item.end}s
            </option>
          ))}
        </select>
      </label>
      <p>Times are in seconds. Changes need source verification and a new render.</p>
      <fieldset disabled={disabled}>
        <legend>Cue {index + 1}</legend>
        {cue && (
          <>
            <label>
              Cue {index + 1} text
              <textarea
                aria-label={`Cue ${index + 1} text`}
                maxLength={1000}
                value={cue.text}
                onChange={(event) => edit({ text: event.target.value })}
              />
            </label>
            {(['start', 'end'] as const).map((key) => (
              <label key={key}>
                Cue {index + 1} {key} (seconds)
                <input
                  type="number"
                  min={0}
                  max={40}
                  step={0.1}
                  value={cue[key]}
                  onChange={(event) => edit({ [key]: Number(event.target.value) })}
                />
              </label>
            ))}
          </>
        )}
        <label>
          Subtitle size (pixels)
          <input
            type="number"
            min={36}
            max={80}
            value={style.fontSize}
            onChange={(event) => styleChange({ fontSize: Number(event.target.value) })}
          />
        </label>
        <label>
          Subtitle position
          <select
            value={style.position}
            onChange={(event) =>
              styleChange({ position: event.target.value as 'lower' | 'middle' })
            }
          >
            <option value="lower">Lower safe area</option>
            <option value="middle">Middle</option>
          </select>
        </label>
        {(['bold', 'background'] as const).map((key) => (
          <label className="choice-row" key={key}>
            <input
              type="checkbox"
              checked={style[key]}
              onChange={(event) => styleChange({ [key]: event.target.checked })}
            />
            {key === 'bold' ? 'Bold subtitles' : 'High-contrast subtitle background'}
          </label>
        ))}
        <button
          className="secondary"
          type="button"
          onClick={() => onChange({ ...output, data: { ...output.data, subtitleCues: null } })}
        >
          Reset subtitles to script
        </button>
      </fieldset>
    </section>
  );
}
