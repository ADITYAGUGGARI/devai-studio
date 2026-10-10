import { useEffect, useRef, useState } from 'react';
import { ApiError, loadAsset, request, uploadAudioBytes } from '../../services/api';
import type { StudioDocument } from '../../../../shared/content';

interface UploadedAudio {
  assetId?: string;
  validation?: { trimmed?: boolean };
  jobId?: string;
}
export function AudioUpload({
  outputId,
  disabled,
  onSelect,
}: {
  outputId: string;
  disabled: boolean;
  onSelect: (id: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [basis, setBasis] = useState('owned');
  const [reference, setReference] = useState('');
  const [rights, setRights] = useState(false);
  const [uploadId, setUploadId] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [assetId, setAssetId] = useState('');
  const [audio, setAudio] = useState('');
  const intent = useRef<{ fingerprint: string; key: string } | null>(null);
  useEffect(() => {
    if (!assetId) return;
    let live = true,
      url = '';
    void loadAsset(assetId)
      .then((value) => {
        url = value;
        if (live) setAudio(value);
        else URL.revokeObjectURL(value);
      })
      .catch(() => setError('Audio preview unavailable. Retry the validated upload.'));
    return () => {
      live = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [assetId]);
  useEffect(() => {
    if (!uploadId) return;
    let live = true;
    const read = async () => {
      try {
        const value = await request<
          StudioDocument<UploadedAudio> & { job?: { status: string; error?: string } }
        >(`/v1/uploads/${uploadId}`);
        if (!live) return;
        if (value.data.assetId) {
          setAssetId(value.data.assetId);
          setStatus(
            value.data.validation?.trimmed
              ? 'Validated. The first 40 seconds are available.'
              : 'Audio decoded and validated.',
          );
          setUploadId('');
          setBusy(false);
        } else if (value.job && ['failed', 'cancelled'].includes(value.job.status)) {
          setError(value.job.error || 'Audio validation cancelled. Upload again to recover.');
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
          setError(cause instanceof Error ? cause.message : 'Cannot read upload status');
          setBusy(false);
        }
      }
    };
    void read();
    const timer = window.setInterval(() => void read(), 2000);
    return () => {
      live = false;
      window.clearInterval(timer);
    };
  }, [uploadId]);
  async function upload() {
    if (!file) return;
    setBusy(true);
    setError('');
    setStatus('Uploading original audio bytes…');
    try {
      const mime =
        file.type ||
        (file.name.toLowerCase().endsWith('.wav')
          ? 'audio/wav'
          : file.name.toLowerCase().endsWith('.mp3')
            ? 'audio/mpeg'
            : 'audio/mp4');
      const fingerprint = JSON.stringify([
        file.name,
        file.size,
        file.lastModified,
        mime,
        basis,
        reference,
        rights,
      ]);
      if (intent.current?.fingerprint !== fingerprint)
        intent.current = { fingerprint, key: crypto.randomUUID() };
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
          sizeBytes: file.size,
          license: { acknowledged: rights, basis, reference },
        },
        { 'Idempotency-Key': key },
      );
      const bytes = await uploadAudioBytes(prepared.uploadPath, prepared.token, file);
      await request(
        prepared.completePath,
        'POST',
        { sha256: bytes.sha256 },
        { 'Idempotency-Key': `${key}-complete` },
      );
      setUploadId(prepared.upload.id);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 410) intent.current = null;
      setError(cause instanceof Error ? cause.message : 'Upload failed');
      setBusy(false);
    }
  }
  return (
    <section aria-label="Licensed music upload">
      <h3>Licensed music</h3>
      <p>
        WAV, MP3 or M4A, up to 50 MiB. Short tracks repeat to fill the Reel. Uploading does not
        change the current mix.
      </p>
      <label>
        Audio file
        <input
          type="file"
          accept=".wav,.mp3,.m4a"
          disabled={disabled || busy}
          onChange={(event) => {
            setFile(event.target.files?.[0] || null);
            setError('');
          }}
        />
      </label>
      <label>
        Usage rights
        <select
          value={basis}
          disabled={disabled || busy}
          onChange={(event) => setBasis(event.target.value)}
        >
          <option value="owned">I own this audio</option>
          <option value="licensed">I have a license</option>
        </select>
      </label>
      <label>
        Rights reference
        <input
          value={reference}
          maxLength={1000}
          disabled={disabled || busy}
          onChange={(event) => setReference(event.target.value)}
          placeholder="Owner or license reference"
        />
      </label>
      <label className="choice-row">
        <input
          type="checkbox"
          checked={rights}
          disabled={disabled || busy}
          onChange={(event) => setRights(event.target.checked)}
        />
        I have permission to use this audio in this post
      </label>
      <button
        type="button"
        className="secondary"
        disabled={
          disabled ||
          busy ||
          !file ||
          file.size > 50 * 1024 * 1024 ||
          !rights ||
          reference.trim().length < 3
        }
        onClick={() => void upload()}
      >
        Upload & validate audio
      </button>
      {status && <p role="status">{status}</p>}
      {error && <p role="alert">{error}</p>}
      {audio && <audio controls src={audio} aria-label="Validated music preview" />}
      {assetId && (
        <button type="button" disabled={disabled || busy} onClick={() => onSelect(assetId)}>
          Use validated music in this Reel
        </button>
      )}
    </section>
  );
}
