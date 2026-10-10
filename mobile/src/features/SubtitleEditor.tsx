import { useState } from 'react';
import { Switch, Text, View } from 'react-native';
import { subtitleCues, type StudioOutput } from '../../../shared/content';
import { Button, Field, Segments, styles } from '../components/ui';

export function NativeSubtitleEditor({
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
    <>
      <Text style={styles.heading}>
        Cue {index + 1} of {cues.length}
      </Text>
      <Text style={styles.muted}>
        Times are in seconds. Edited text needs source verification and a new render.
      </Text>
      <View style={{ flexDirection: 'row', gap: 12 }}>
        <Button
          title="Previous cue"
          secondary
          disabled={index === 0}
          onPress={() => setSelected(cues[index - 1].id || String(index - 1))}
        />
        <Button
          title="Next cue"
          secondary
          disabled={index >= cues.length - 1}
          onPress={() => setSelected(cues[index + 1].id || String(index + 1))}
        />
      </View>
      {cue && (
        <>
          <Field
            label={`Cue ${index + 1} text`}
            value={cue.text}
            multiline
            disabled={disabled}
            onChange={(text) => edit({ text })}
          />
          {(['start', 'end'] as const).map((key) => (
            <Field
              key={key}
              label={`Cue ${index + 1} ${key} (seconds)`}
              value={String(cue[key])}
              keyboardType="decimal-pad"
              disabled={disabled}
              onChange={(text) => edit({ [key]: Number(text) })}
            />
          ))}
        </>
      )}
      <Field
        label="Subtitle size (pixels)"
        value={String(style.fontSize)}
        keyboardType="number-pad"
        disabled={disabled}
        onChange={(text) => styleChange({ fontSize: Number(text) })}
      />
      <Text style={styles.muted}>Subtitle position</Text>
      <Segments
        items={['lower', 'middle'] as const}
        value={style.position}
        onChange={(value) => {
          if (!disabled) styleChange({ position: value });
        }}
      />
      {(['bold', 'background'] as const).map((key) => (
        <View
          key={key}
          style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
            minHeight: 52,
          }}
        >
          <Text style={styles.text}>
            {key === 'bold' ? 'Bold subtitles' : 'High-contrast background'}
          </Text>
          <Switch
            accessibilityLabel={
              key === 'bold' ? 'Bold subtitles' : 'High-contrast subtitle background'
            }
            disabled={disabled}
            value={style[key]}
            onValueChange={(value) => styleChange({ [key]: value })}
          />
        </View>
      ))}
      <Button
        title="Reset subtitles to script"
        secondary
        disabled={disabled}
        onPress={() => onChange({ ...output, data: { ...output.data, subtitleCues: null } })}
      />
    </>
  );
}
