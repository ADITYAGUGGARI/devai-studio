import { useEffect, useMemo, useRef, useState } from 'react';
import { Text } from 'react-native';
import { useAtomValue } from 'jotai';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system/legacy';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { sessionAtom } from '../app/state';
import { API_URL, ApiError, request } from '../services/api';
import { Button, Field, Segments, styles } from '../components/ui';
import type { StudioDocument } from '../../../shared/content';

export function NativeAudioUpload({
  outputId,
  disabled,
  onSelect,
}: {
  outputId: string;
  disabled: boolean;
  onSelect: (id: string) => void;
}) {
  const session = useAtomValue(sessionAtom);
  const [file, setFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [basis, setBasis] = useState<'owned' | 'licensed'>('owned');
  const [reference, setReference] = useState('');
  const [rights, setRights] = useState(false);
  const [uploadId, setUploadId] = useState('');
  const [assetId, setAssetId] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const intent = useRef<{ fingerprint: string; key: string } | null>(null);
  const source = useMemo(
    () =>
      assetId && session
        ? {
            uri: `${API_URL}/v1/assets/${assetId}`,
            headers: { Authorization: `Bearer ${session.token}` },
          }
        : null,
    [assetId, session],
  );
  const player = useAudioPlayer(source);
  const playback = useAudioPlayerStatus(player);
  useEffect(() => {
    if (!uploadId) return;
    let live = true;
    const read = async () => {
      try {
        const value = await request<
          StudioDocument<{ assetId?: string; validation?: { trimmed?: boolean } }> & {
            job?: { status: string; error?: string };
          }
        >(`/v1/uploads/${uploadId}`);
        if (!live) return;
        if (value.data.assetId) {
          setAssetId(value.data.assetId);
          setBusy(false);
          setUploadId('');
          setStatus(
            value.data.validation?.trimmed
              ? 'Validated. The first 40 seconds are available.'
              : 'Audio decoded and validated.',
          );
        } else if (value.job && ['failed', 'cancelled'].includes(value.job.status)) {
          setError(value.job.error || 'Validation cancelled. Upload again to recover.');
          intent.current = null;
          setBusy(false);
          setUploadId('');
        } else
          setStatus(
            value.job?.status === 'running'
              ? 'Decoding audio on the server…'
              : 'Audio validation queued…',
          );
      } catch (cause) {
        if (live) {
          setError(cause instanceof Error ? cause.message : 'Upload status unavailable');
          setBusy(false);
        }
      }
    };
    void read();
    const timer = setInterval(() => void read(), 2000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [uploadId]);
  async function pick() {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/x-m4a', 'audio/x-wav'],
        copyToCacheDirectory: true,
      });
      if (!result.canceled) {
        setFile(result.assets[0]);
        setError('');
      }
    } catch {
      setError('Could not open the document picker. Try again.');
    }
  }
  async function upload() {
    if (!file || !session) return;
    setBusy(true);
    setError('');
    setStatus('Uploading original audio bytes…');
    try {
      const info = await FileSystem.getInfoAsync(file.uri);
      if (!info.exists || info.isDirectory)
        throw new Error('Selected audio is unavailable. Choose it again.');
      const mime =
        file.mimeType ||
        (file.name.toLowerCase().endsWith('.wav')
          ? 'audio/wav'
          : file.name.toLowerCase().endsWith('.mp3')
            ? 'audio/mpeg'
            : 'audio/mp4');
      const fingerprint = JSON.stringify([
        file.uri,
        file.name,
        info.size,
        mime,
        basis,
        reference,
        rights,
      ]);
      if (intent.current?.fingerprint !== fingerprint)
        intent.current = { fingerprint, key: `${Date.now()}-${Math.random()}` };
      const key = intent.current.key;
      const prepared = await request<{
        upload: { id: string };
        uploadPath: string;
        completePath: string;
        token: string;
      }>(
        `/v1/outputs/${outputId}/audio/uploads`,
        'POST',
        {
          fileName: file.name,
          mimeType: mime,
          sizeBytes: info.size,
          license: { acknowledged: rights, basis, reference },
        },
        { 'Idempotency-Key': key },
      );
      const result = await FileSystem.uploadAsync(API_URL + prepared.uploadPath, file.uri, {
        httpMethod: 'PUT',
        uploadType: FileSystem.FileSystemUploadType.BINARY_CONTENT,
        headers: {
          Authorization: `Bearer ${session.token}`,
          'X-Upload-Token': prepared.token,
          'Content-Type': mime,
        },
      });
      const bytes = JSON.parse(result.body);
      if (result.status !== 200)
        throw new ApiError(
          typeof bytes.detail === 'string'
            ? bytes.detail
            : 'Upload failed. Current media remains preserved.',
          result.status,
          bytes.detail,
        );
      await request(
        prepared.completePath,
        'POST',
        { sha256: bytes.sha256 },
        { 'Idempotency-Key': `${key}-complete` },
      );
      setUploadId(prepared.upload.id);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 410) intent.current = null;
      setError(cause instanceof Error ? cause.message : 'Audio upload failed');
      setBusy(false);
    }
  }
  return (
    <>
      <Text style={styles.title}>Licensed music</Text>
      <Text style={styles.muted}>
        WAV, MP3 or M4A, up to 50 MiB. Short tracks repeat to fill the Reel. Uploading does not
        select the music.
      </Text>
      <Button
        title={file ? `Choose audio: ${file.name}` : 'Choose audio file'}
        secondary
        disabled={disabled || busy}
        onPress={() => void pick()}
      />
      <Segments
        items={['owned', 'licensed']}
        value={basis}
        onChange={(value) => {
          if (!disabled && !busy) setBasis(value as 'owned' | 'licensed');
        }}
      />
      <Field
        label="Rights reference"
        value={reference}
        disabled={disabled || busy}
        onChange={setReference}
      />
      <Button
        title={rights ? 'Audio usage rights acknowledged' : 'I have permission to use this audio'}
        secondary
        disabled={disabled || busy}
        onPress={() => setRights(!rights)}
      />
      <Button
        title="Upload & validate audio"
        disabled={disabled || busy || !file || !rights || reference.trim().length < 3}
        onPress={() => void upload()}
      />
      {status && (
        <Text accessibilityLiveRegion="polite" style={styles.muted}>
          {status}
        </Text>
      )}
      {error && (
        <Text accessibilityRole="alert" style={styles.warning}>
          {error}
        </Text>
      )}
      {assetId && (
        <>
          <Button
            title={
              playback.playing ? 'Pause validated music preview' : 'Play validated music preview'
            }
            secondary
            disabled={!playback.isLoaded}
            onPress={() => {
              if (playback.playing) player.pause();
              else {
                if (playback.didJustFinish) void player.seekTo(0);
                player.play();
              }
            }}
          />
          <Button
            title="Use validated music in this Reel"
            disabled={disabled || busy}
            onPress={() => {
              player.pause();
              onSelect(assetId);
            }}
          />
        </>
      )}
    </>
  );
}
