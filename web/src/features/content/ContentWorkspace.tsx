import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAtomValue } from 'jotai';
import { accountAtom } from '../../app/state';
import { ApiError, downloadOutput, loadAsset, request } from '../../services/api';
import { Modal } from '../../components/Modal';
import { AudioUpload } from './AudioUpload';
import { SubtitleEditor } from './SubtitleEditor';
import {
  contentList,
  canEditStudio,
  canReviewStudio,
  timelinePayload,
  type StudioContent,
  type StudioOutput,
  type Scene,
} from '../../../../shared/content';

function editable(value: StudioOutput) {
  return JSON.stringify({ ...timelinePayload(value), expectedRevision: 0 });
}

export function StudioAsset({
  id,
  video = false,
  onInspected,
}: {
  id: string;
  video?: boolean;
  onInspected?: () => void;
}) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let live = true,
      objectUrl = '';
    setUrl('');
    setError('');
    void loadAsset(id)
      .then((value) => {
        if (live) {
          objectUrl = value;
          setUrl(value);
        } else URL.revokeObjectURL(value);
      })
      .catch((cause) => {
        if (live) setError(cause.message);
      });
    return () => {
      live = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [id, retry]);
  if (error)
    return (
      <div role="alert">
        <p>{error}</p>
        <button className="secondary" onClick={() => setRetry(retry + 1)}>
          Retry media
        </button>
      </div>
    );
  if (!url) return <p role="status">Loading saved media…</p>;
  return video ? (
    <video
      className="reel-player"
      controls
      playsInline
      preload="metadata"
      src={url}
      onEnded={onInspected}
      aria-label="Rendered Reel preview"
    />
  ) : (
    <img className="scene-image" src={url} alt="Generated Reel scene" onLoad={onInspected} />
  );
}

export function ContentWorkspace({
  contentId,
  outputFormat,
  editorTool,
  initialSceneId,
  onDirtyChange,
}: {
  contentId: string;
  outputFormat?: 'reel';
  editorTool?: string;
  initialSceneId?: string;
  onDirtyChange: (value: boolean) => void;
}) {
  const cache = useQueryClient();
  const account = useAtomValue(accountAtom);
  const canEdit = canEditStudio(account);
  const canReview = canReviewStudio(account);
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const {
    data: content,
    error: readError,
    isPending,
    refetch,
  } = useQuery({
    queryKey: ['studio-content', contentId],
    queryFn: () => request<StudioContent>(`/v1/content/${contentId}`),
    refetchInterval: 2000,
  });
  const output =
    content?.outputs.find(
      (item) =>
        item.id === params.get('output') && (!outputFormat || item.data.format === outputFormat),
    ) ||
    (outputFormat
      ? content?.outputs.find((item) => item.data.format === outputFormat)
      : content?.outputs[0]);
  const [draft, setDraft] = useState<StudioOutput | null>(null);
  const [base, setBase] = useState<StudioOutput | null>(null);
  const baseRef = useRef<StudioOutput | null>(null);
  const draftRef = useRef<StudioOutput | null>(null);
  draftRef.current = draft;
  const [selectedScene, setSelectedScene] = useState(initialSceneId || '');
  const [section, setSection] = useState<
    'Scenes' | 'Script' | 'Audio' | 'Subtitles' | 'Review' | 'Versions'
  >(
    editorTool === 'script'
      ? 'Script'
      : editorTool === 'subtitles'
        ? 'Subtitles'
        : editorTool === 'audio'
          ? 'Audio'
          : 'Scenes',
  );
  useEffect(() => {
    if (outputFormat)
      setSection(
        editorTool === 'script'
          ? 'Script'
          : editorTool === 'subtitles'
            ? 'Subtitles'
            : editorTool === 'audio'
              ? 'Audio'
              : 'Scenes',
      );
    if (initialSceneId) setSelectedScene(initialSceneId);
  }, [outputFormat, editorTool, initialSceneId]);
  const [error, setError] = useState('');
  const [saveStatus, setSaveStatus] = useState('Saved');
  const [busy, setBusy] = useState(false);
  const saving = useRef(false);
  const [conflict, setConflict] = useState<StudioOutput | null>(null);
  const [paid, setPaid] = useState<{ action: string; sceneId?: string } | null>(null);
  const [checks, setChecks] = useState<Record<string, boolean>>({});
  const [watched, setWatched] = useState(false);
  const [notes, setNotes] = useState('');
  const [restoreRevision, setRestoreRevision] = useState<number | null>(null);
  const [versions, setVersions] = useState<{ revision: number; reason: string; state: string }[]>(
    [],
  );
  const pendingAction = useRef<{ fingerprint: string; key: string } | null>(null);
  const dirty = Boolean(draft && base && editable(draft) !== editable(base));
  const active = Boolean(
    output?.job && ['queued', 'running', 'retry_wait'].includes(output.job.status),
  );
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  useEffect(() => {
    if (!output) return;
    if (
      baseRef.current?.id !== output.id ||
      !draftRef.current ||
      editable(draftRef.current) === editable(baseRef.current!)
    ) {
      baseRef.current = output;
      setBase(output);
      setDraft(output);
    }
  }, [output]);
  useEffect(() => {
    setChecks({});
    setWatched(false);
  }, [output?.id, output?.revision]);
  async function mutate(path: string, payload: unknown, method = 'POST') {
    const fingerprint = JSON.stringify([path, payload, method]);
    if (pendingAction.current?.fingerprint !== fingerprint)
      pendingAction.current = { fingerprint, key: crypto.randomUUID() };
    return request<StudioOutput>(path, method, payload, {
      'Idempotency-Key': pendingAction.current.key,
    });
  }
  async function save() {
    const value = draftRef.current,
      original = baseRef.current;
    if (!value || !original || saving.current || conflict || !dirty) return false;
    saving.current = true;
    setSaveStatus('Autosaving…');
    setError('');
    try {
      const saved = await mutate(
        `/v1/outputs/${value.id}/timeline`,
        { ...timelinePayload(value), expectedRevision: original.revision },
        'PATCH',
      );
      baseRef.current = saved;
      setBase(saved);
      setDraft((current) =>
        current && editable(current) !== editable(value)
          ? { ...current, revision: saved.revision }
          : saved,
      );
      setSaveStatus('Saved');
      pendingAction.current = null;
      await cache.invalidateQueries({ queryKey: ['studio-content', contentId] });
      return true;
    } catch (cause) {
      setSaveStatus('Save failed · Edits retained');
      setError(cause instanceof Error ? cause.message : 'Save failed');
      if (
        cause instanceof ApiError &&
        cause.status === 409 &&
        typeof cause.detail === 'object' &&
        cause.detail &&
        'server' in cause.detail
      )
        setConflict(cause.detail.server as StudioOutput);
      return false;
    } finally {
      saving.current = false;
    }
  }
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    if (!dirty || active || conflict) return;
    setSaveStatus('Unsaved changes');
    const timer = window.setTimeout(() => {
      void saveRef.current();
    }, 800);
    return () => window.clearTimeout(timer);
  }, [dirty, draft, active, conflict]);
  function editScene(id: string, values: Partial<Scene>) {
    setDraft((value) =>
      value
        ? {
            ...value,
            data: {
              ...value.data,
              scenes: value.data.scenes.map((scene) =>
                scene.id === id ? { ...scene, ...values } : scene,
              ),
            },
          }
        : value,
    );
  }
  function reorder(id: string, delta: number) {
    setDraft((value) => {
      if (!value) return value;
      const scenes = [...value.data.scenes];
      const at = scenes.findIndex((scene) => scene.id === id);
      const target = at + delta;
      if (target < 0 || target >= scenes.length) return value;
      [scenes[at], scenes[target]] = [scenes[target], scenes[at]];
      return { ...value, data: { ...value.data, scenes } };
    });
  }
  async function run(operation: () => Promise<unknown>) {
    setBusy(true);
    setError('');
    try {
      await operation();
      await refetch();
      pendingAction.current = null;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Operation failed');
    } finally {
      setBusy(false);
    }
  }
  async function paidAction() {
    if (!output || !paid) return;
    const path = paid.sceneId
      ? `/v1/outputs/${output.id}/scenes/${paid.sceneId}/generate`
      : `/v1/outputs/${output.id}/${paid.action}`;
    await run(async () => {
      await mutate(path, {
        expectedRevision: output.revision,
        confirmed: true,
        confirmedBudget: paid.sceneId ? 6 : 32,
      });
      setPaid(null);
    });
  }
  async function review(action: 'submit' | 'approve') {
    if (!output) return;
    let assets = output.data.renderId ? [output.data.renderId] : [];
    if (output.data.format === 'carousel' && output.data.postId) {
      const post = await request<{ slides: { id: string }[] }>(`/posts/${output.data.postId}`);
      assets = post.slides.map((slide) => slide.id);
    }
    await mutate(`/v1/outputs/${output.id}/review/${action}`, {
      expectedRevision: output.revision,
      confirmed: true,
      checklist: checks,
      reviewedAssetIds: assets,
    });
  }
  if (isPending) return <p role="status">Opening your saved content…</p>;
  if (!content || !output || !draft)
    return (
      <div role="alert">
        <h2>Content unavailable</h2>
        <p>
          {readError instanceof Error
            ? readError.message
            : 'The content may have been removed or access changed.'}
        </p>
        <button className="secondary" onClick={() => void refetch()}>
          Retry
        </button>
      </div>
    );
  const scene =
    draft.data.scenes.find((item) => item.id === selectedScene) ||
    (!selectedScene ? draft.data.scenes[0] : undefined);
  const totalDuration = draft.data.scenes.reduce((total, item) => total + item.durationSec, 0);
  const changed = draft.data.format === 'reel' && (!output.data.renderCurrent || dirty);
  const readOnly = active || busy || !canEdit;
  return (
    <section className="content-workspace" aria-label="Content editing workspace">
      <header className="editor-heading">
        <div>
          <div className="eyebrow">YOUR CONTENT · VERSION {output.revision}</div>
          <h2>{content.data.title}</h2>
        </div>
        <button className="secondary" disabled={dirty} onClick={() => navigate('/content')}>
          Done
        </button>
      </header>
      <div className="view-tabs" role="tablist" aria-label="Independent output formats">
        {content.outputs.map((item) => (
          <button
            key={item.id}
            role="tab"
            aria-selected={item.id === output.id}
            disabled={dirty}
            onClick={() =>
              outputFormat && item.data.format !== outputFormat
                ? navigate(`/studio-content/${contentId}?output=${item.id}`)
                : setParams({ output: item.id })
            }
          >
            {item.data.format} · {item.state.replaceAll('_', ' ')}
          </button>
        ))}
      </div>
      {(error || readError) && (
        <p role="alert" className="error">
          {error ||
            (readError instanceof Error
              ? readError.message
              : 'Connection failed; saved work is preserved')}
        </p>
      )}
      <div className="editor-status">
        <span role="status">
          {dirty && saveStatus === 'Saved' ? 'Unsaved changes' : saveStatus}
        </span>
        <span>
          {output.data.stage.replaceAll('_', ' ')} · {output.data.budgetRemaining} authorized
          requests remaining
        </span>
      </div>
      {selectedScene && !scene && (
        <p role="alert">
          This scene is unavailable in the current revision. Select an available scene in the
          timeline.
        </p>
      )}
      {output.job && (
        <div className="output-job panel">
          <strong>{output.job.step}</strong>
          <span>
            {output.job.progress}/{output.job.total} completed units ·{' '}
            {output.job.status.replaceAll('_', ' ')}
          </span>
          {output.job.error && <p role="alert">{output.job.error}</p>}
          {active && (
            <button
              className="secondary"
              disabled={busy || output.job.cancel_requested}
              onClick={() => void run(() => request(`/v1/jobs/${output.job!.id}/cancel`, 'POST'))}
            >
              Cancel at safe checkpoint
            </button>
          )}
          {['failed', 'retry_wait'].includes(output.job.status) && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void run(() => request(`/jobs/${output.job!.id}/retry`, 'POST'))}
            >
              Retry existing job
            </button>
          )}
          <p>Work continues on the server when you leave. Successful assets are retained.</p>
        </div>
      )}
      {conflict && (
        <div className="panel conflict-panel" role="alert">
          <h3>This timeline changed on another device</h3>
          <p>Your scene copy is retained. Saved caption:</p>
          <pre>{conflict.data.caption}</pre>
          <button
            className="secondary"
            onClick={() => {
              baseRef.current = conflict;
              setBase(conflict);
              setConflict(null);
            }}
          >
            Keep my changes and save against this version
          </button>
          <button
            className="secondary"
            onClick={() => {
              baseRef.current = conflict;
              setBase(conflict);
              setDraft(conflict);
              setConflict(null);
            }}
          >
            Use server version
          </button>
        </div>
      )}
      {output.data.format === 'carousel' ? (
        <div className="panel">
          <h3>Carousel editor</h3>
          <p>
            Inspect every full AI-generated slide in the carousel workspace. Return here to review
            this output independently.
          </p>
          {output.data.postId && (
            <button
              className="primary"
              onClick={() => navigate(`/content/${output.data.postId}/carousel`)}
            >
              Edit & inspect carousel slides
            </button>
          )}
          <button
            className="secondary"
            disabled={active || busy}
            onClick={() =>
              void run(() =>
                mutate(`/v1/outputs/${output.id}/sync`, {
                  expectedRevision: output.revision,
                  confirmed: true,
                }),
              )
            }
          >
            Synchronize current carousel copy
          </button>
        </div>
      ) : (
        <div className="reel-editor-grid">
          <section className="panel reel-preview-panel">
            <div className="eyebrow">VERTICAL PREVIEW</div>
            {output.data.renderId ? (
              <StudioAsset
                key={output.data.renderId}
                id={output.data.renderId}
                video
                onInspected={() => setWatched(true)}
              />
            ) : scene?.imageAssetId ? (
              <StudioAsset id={scene.imageAssetId} />
            ) : (
              <div className="no-render">
                <h3>No completed video yet</h3>
                <p>
                  Scripts and scene images become a Reel only after a rendered MP4 passes
                  validation.
                </p>
              </div>
            )}
            {changed && output.data.renderId && (
              <p className="status-warning">
                Previous render preserved · This timeline needs a new render.
              </p>
            )}
            <p>
              {output.data.renderValidation?.duration_seconds.toFixed(1) || 'Unvalidated duration'}{' '}
              seconds · 1080 × 1920 ·{' '}
              {output.data.renderValidation?.decoded
                ? 'Previous/current MP4 decoded successfully'
                : 'Awaiting MP4 validation'}
            </p>
            <button
              className="primary"
              disabled={
                readOnly ||
                dirty ||
                !draft.data.scenes.length ||
                totalDuration < 30 ||
                totalDuration > 40
              }
              onClick={() =>
                void run(() =>
                  mutate(`/v1/outputs/${output.id}/render`, {
                    expectedRevision: output.revision,
                    confirmed: true,
                  }),
                )
              }
            >
              Render current timeline
            </button>
          </section>
          <section className="panel reel-inspector">
            <div className="view-tabs" role="tablist" aria-label="Reel editing tools">
              {(['Scenes', 'Script', 'Audio', 'Subtitles'] as const).map((item) => (
                <button
                  role="tab"
                  aria-selected={section === item}
                  key={item}
                  onClick={() => setSection(item)}
                >
                  {item}
                </button>
              ))}
            </div>
            {section === 'Audio' ? (
              <fieldset disabled={readOnly}>
                <legend>Audio & subtitles</legend>
                <label>
                  Narration voice
                  <select
                    value={draft.data.voiceId || ''}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        data: {
                          ...draft.data,
                          voiceId: (event.target.value as StudioOutput['data']['voiceId']) || null,
                        },
                      })
                    }
                  >
                    <option value="">No narration · deliberate silence</option>
                    {['coral', 'marin', 'cedar', 'alloy', 'nova', 'sage'].map((voice) => (
                      <option key={voice}>{voice}</option>
                    ))}
                  </select>
                </label>
                <AudioUpload
                  key={draft.id}
                  outputId={draft.id}
                  disabled={readOnly}
                  onSelect={(id) =>
                    setDraft({ ...draft, data: { ...draft.data, musicAssetId: id } })
                  }
                />
                {draft.data.musicAssetId && (
                  <>
                    <p>Validated music is selected. Render again to hear the current mix.</p>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        setDraft({ ...draft, data: { ...draft.data, musicAssetId: null } })
                      }
                    >
                      Remove music
                    </button>
                  </>
                )}
                {(['voiceGainDb', 'musicGainDb'] as const).map((key) => (
                  <label key={key}>
                    {key === 'voiceGainDb' ? 'Voice gain (dB)' : 'Music gain (dB)'}
                    <input
                      type="number"
                      min={-60}
                      max={6}
                      step={1}
                      value={draft.data[key] ?? (key === 'voiceGainDb' ? 0 : -18)}
                      onChange={(event) =>
                        setDraft({
                          ...draft,
                          data: { ...draft.data, [key]: Number(event.target.value) },
                        })
                      }
                    />
                  </label>
                ))}
                <label className="choice-row">
                  <input
                    type="checkbox"
                    checked={draft.data.ducking ?? true}
                    onChange={(event) =>
                      setDraft({ ...draft, data: { ...draft.data, ducking: event.target.checked } })
                    }
                  />
                  Lower music during narration
                </label>
                <label className="choice-row">
                  <input
                    type="checkbox"
                    checked={draft.data.subtitles}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        data: { ...draft.data, subtitles: event.target.checked },
                      })
                    }
                  />
                  Burned-in subtitles
                </label>
                <p>Changing the voice does not generate audio. Narration is AI-generated.</p>
                <button type="button" className="secondary" onClick={() => setSection('Subtitles')}>
                  Edit subtitle cues
                </button>
                <button
                  className="secondary"
                  disabled={dirty || !draft.data.voiceId}
                  onClick={() => setPaid({ action: 'voiceover' })}
                >
                  Generate current voiceover
                </button>
              </fieldset>
            ) : section === 'Subtitles' ? (
              <fieldset>
                <legend>Subtitles</legend>
                <label className="choice-row">
                  <input
                    type="checkbox"
                    disabled={readOnly}
                    checked={draft.data.subtitles}
                    onChange={(event) =>
                      setDraft({
                        ...draft,
                        data: { ...draft.data, subtitles: event.target.checked },
                      })
                    }
                  />
                  Burned-in subtitles
                </label>
                {draft.data.subtitles && (
                  <SubtitleEditor output={draft} disabled={readOnly} onChange={setDraft} />
                )}
              </fieldset>
            ) : scene ? (
              <fieldset disabled={readOnly}>
                <legend>Scene {draft.data.scenes.indexOf(scene) + 1}</legend>
                <label>
                  Headline
                  <input
                    maxLength={100}
                    value={scene.headline}
                    onChange={(event) => editScene(scene.id, { headline: event.target.value })}
                  />
                </label>
                <label>
                  Visible body
                  <textarea
                    maxLength={200}
                    value={scene.body}
                    onChange={(event) => editScene(scene.id, { body: event.target.value })}
                  />
                </label>
                <label>
                  Narration & subtitle script
                  <textarea
                    maxLength={1000}
                    value={scene.script}
                    onChange={(event) => editScene(scene.id, { script: event.target.value })}
                  />
                </label>
                <label>
                  Scene duration in seconds
                  <input
                    type="number"
                    min={1}
                    max={15}
                    step={0.1}
                    value={scene.durationSec}
                    onChange={(event) =>
                      editScene(scene.id, { durationSec: Number(event.target.value) })
                    }
                  />
                </label>
                <button
                  className="secondary"
                  disabled={dirty}
                  onClick={() => setPaid({ action: 'scene', sceneId: scene.id })}
                >
                  Regenerate this scene with AI
                </button>
              </fieldset>
            ) : (
              <p>Scenes appear when the grounded storyboard is ready.</p>
            )}
          </section>
          {['Scenes', 'Script'].includes(section) && (
            <section className="panel scene-timeline">
              <div className="timeline-heading">
                <h3>Scene timeline</h3>
                <strong>{totalDuration.toFixed(1)}s / 30–40s</strong>
              </div>
              <div className="scene-cards">
                {draft.data.scenes.map((item, index) => (
                  <div
                    key={item.id}
                    className={scene?.id === item.id ? 'scene-card selected' : 'scene-card'}
                  >
                    <button
                      className="scene-select"
                      aria-pressed={scene?.id === item.id}
                      onClick={() => {
                        setSelectedScene(item.id);
                        setSection('Scenes');
                      }}
                    >
                      <span>SCENE {index + 1}</span>
                      <strong>{item.headline}</strong>
                      <small>
                        {item.durationSec}s ·{' '}
                        {item.imageAssetId
                          ? item.imageCurrent
                            ? 'Image saved'
                            : 'Image needs regeneration'
                          : 'Image pending'}
                      </small>
                    </button>
                    <div className="actions">
                      <button
                        className="ghost"
                        aria-label={`Move scene ${index + 1} earlier`}
                        disabled={readOnly || index === 0}
                        onClick={() => reorder(item.id, -1)}
                      >
                        ←
                      </button>
                      <button
                        className="ghost"
                        aria-label={`Move scene ${index + 1} later`}
                        disabled={readOnly || index === draft.data.scenes.length - 1}
                        onClick={() => reorder(item.id, 1)}
                      >
                        →
                      </button>
                      <button
                        className="ghost"
                        disabled={readOnly || draft.data.scenes.length <= 3}
                        onClick={() =>
                          setDraft({
                            ...draft,
                            data: {
                              ...draft.data,
                              scenes: draft.data.scenes.filter((value) => value.id !== item.id),
                            },
                          })
                        }
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <button
                className="secondary"
                disabled={readOnly || draft.data.scenes.length >= 12}
                onClick={() => {
                  const id = crypto.randomUUID();
                  setDraft({
                    ...draft,
                    data: {
                      ...draft.data,
                      scenes: [
                        ...draft.data.scenes,
                        {
                          id,
                          headline: 'New scene',
                          body: '',
                          script: 'Add source-grounded narration.',
                          durationSec: 3,
                        },
                      ],
                    },
                  });
                  setSelectedScene(id);
                }}
              >
                Add scene
              </button>
              <button
                className="secondary"
                disabled={!dirty || readOnly || saving.current}
                onClick={() => void save()}
              >
                Save now
              </button>
            </section>
          )}
        </div>
      )}
      {!['Audio', 'Subtitles'].includes(section) && (
        <section className="panel caption-panel">
          <h3>Caption & source attribution</h3>
          {output.data.format === 'reel' ? (
            <label>
              Caption
              <textarea
                disabled={readOnly}
                maxLength={2200}
                value={draft.data.caption}
                onChange={(event) =>
                  setDraft({ ...draft, data: { ...draft.data, caption: event.target.value } })
                }
              />
            </label>
          ) : (
            <p>{output.data.caption}</p>
          )}
          <details>
            <summary>Saved source evidence · {output.data.source.source}</summary>
            <p>{output.data.source.excerpt}</p>
            <a href={output.data.source.url} target="_blank" rel="noreferrer">
              Open primary source
            </a>
          </details>
          <details>
            <summary>Claim grounding report</summary>
            {output.data.grounding?.claims?.map((claim, index) => (
              <div key={index}>
                <strong>{claim.claim}</strong>
                <blockquote>{claim.evidence_quote}</blockquote>
              </div>
            ))}
            <p>
              {output.data.grounding?.supported
                ? 'Supported by the saved evidence; human review still required.'
                : 'Grounding needs verification before review.'}
            </p>
          </details>
          {output.data.format === 'reel' && (
            <button
              className="secondary"
              disabled={readOnly || dirty}
              onClick={() => setPaid({ action: 'grounding' })}
            >
              Recheck current script and caption
            </button>
          )}
        </section>
      )}
      <div className="actions">
        <button className="secondary" onClick={() => setSection('Review')}>
          Review this output
        </button>
        <button
          className="secondary"
          onClick={() =>
            void run(async () => {
              const value = await request<{ items: typeof versions }>(
                `/v1/outputs/${output.id}/versions`,
              );
              setVersions(value.items);
              setSection('Versions');
            })
          }
        >
          Version history
        </button>
        <button
          className="secondary"
          disabled={active || dirty || busy}
          onClick={() => void run(() => downloadOutput(output.id))}
        >
          Export ZIP
        </button>
      </div>
      {section === 'Review' && (
        <section className="panel review-checklist">
          <h3>Independent {output.data.format} review</h3>
          <p>
            Review applies to version {output.revision}. Approval does not authorize publication.
          </p>
          {output.data.format === 'reel' && (
            <p>
              {watched
                ? 'Playback inspected.'
                : 'Play the complete rendered video before approving.'}
            </p>
          )}
          {['sources', 'claims', 'assets', 'caption'].map((name) => (
            <label className="choice-row" key={name}>
              <input
                type="checkbox"
                checked={checks[name] || false}
                onChange={(event) => setChecks({ ...checks, [name]: event.target.checked })}
              />
              I reviewed {name === 'assets' ? 'every image / the complete rendered video' : name}
            </label>
          ))}
          <div className="actions">
            <button
              className="primary"
              disabled={
                readOnly ||
                dirty ||
                !['sources', 'claims', 'assets', 'caption'].every((name) => checks[name])
              }
              onClick={() => void run(() => review('submit'))}
            >
              Submit for review
            </button>
            <button
              className="primary"
              disabled={
                active ||
                busy ||
                !canReview ||
                dirty ||
                output.state !== 'pending_review' ||
                !['sources', 'claims', 'assets', 'caption'].every((name) => checks[name]) ||
                (output.data.format === 'reel' && !watched)
              }
              onClick={() => void run(() => review('approve'))}
            >
              Approve this version
            </button>
          </div>
          <label>
            Revision request
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              maxLength={2000}
            />
          </label>
          <button
            className="secondary"
            disabled={active || busy || !canReview || notes.trim().length < 3}
            onClick={() =>
              void run(() =>
                mutate(`/v1/outputs/${output.id}/changes`, {
                  expectedRevision: output.revision,
                  notes,
                }),
              )
            }
          >
            Request changes
          </button>
          {output.data.revisionRequests?.map((item, index) => (
            <p key={index}>
              Version {item.revision}: {item.notes}
            </p>
          ))}
        </section>
      )}
      {section === 'Versions' && (
        <section className="panel">
          <h3>Saved versions</h3>
          {versions.map((version) => (
            <div className="version-row" key={version.revision}>
              <strong>Version {version.revision}</strong>
              <span>
                {version.reason} · {version.state}
              </span>
              {output.data.format === 'reel' && (
                <button
                  className="secondary"
                  disabled={readOnly || dirty || version.revision === output.revision}
                  onClick={() => setRestoreRevision(version.revision)}
                >
                  Restore version {version.revision}
                </button>
              )}
            </div>
          ))}
        </section>
      )}
      {restoreRevision !== null && (
        <Modal
          title={`Restore version ${restoreRevision}?`}
          onClose={() => setRestoreRevision(null)}
        >
          <p>
            This creates a new draft revision. Existing assets and history are preserved. Approval
            is cleared, and your remaining provider budget stays unchanged.
          </p>
          <div className="actions">
            <button className="secondary" disabled={busy} onClick={() => setRestoreRevision(null)}>
              Keep current version
            </button>
            <button
              disabled={busy}
              onClick={() => {
                void run(async () => {
                  await mutate(`/v1/outputs/${output.id}/versions/restore`, {
                    expectedRevision: output.revision,
                    targetRevision: restoreRevision,
                    confirmed: true,
                  });
                  setRestoreRevision(null);
                });
              }}
            >
              Restore as a new draft
            </button>
          </div>
        </Modal>
      )}
      {paid && (
        <Modal
          title={paid.sceneId ? 'Regenerate this scene?' : 'Authorize provider work'}
          onClose={() => setPaid(null)}
        >
          <p>
            Authorize up to {paid.sceneId ? 6 : 32} additional provider requests. Previous assets
            are preserved. This output’s approval is invalidated. Other outputs remain unchanged.
          </p>
          <div className="actions">
            <button className="secondary" onClick={() => setPaid(null)}>
              Cancel
            </button>
            <button className="primary" disabled={busy} onClick={() => void paidAction()}>
              Confirm & start
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}

export function StudioContentLibrary() {
  const navigate = useNavigate();
  const canEdit = canEditStudio(useAtomValue(accountAtom));
  const [query, setQuery] = useState('');
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['studio-content-list', query],
    queryFn: () =>
      request<{ items: StudioContent[] }>(`/v1/content?q=${encodeURIComponent(query)}`).then(
        contentList,
      ),
    refetchInterval: 3000,
  });
  return (
    <section className="studio-content-library" aria-label="Carousel and Reel projects">
      <div className="library-toolbar">
        <h2>Content projects</h2>
        <button className="primary" disabled={!canEdit} onClick={() => navigate('/create')}>
          Create carousel or Reel
        </button>
      </div>
      <label>
        Search projects
        <input value={query} onChange={(event) => setQuery(event.target.value)} />
      </label>
      {isPending ? (
        <p role="status">Loading saved projects…</p>
      ) : error ? (
        <p role="alert">
          {error.message}
          <button className="secondary" onClick={() => void refetch()}>
            Retry
          </button>
        </p>
      ) : !data?.items.length ? (
        <p>Your new multi-format projects will appear here. Existing carousels remain below.</p>
      ) : (
        <div className="cards">
          {data.items.map((content) => (
            <button
              className="postcard content-project"
              key={content.id}
              onClick={() => navigate(`/studio-content/${content.id}`)}
            >
              <span className="eyebrow">
                {content.outputs.map((output) => output.data.format).join(' + ')}
              </span>
              <strong>{content.data.title}</strong>
              <span>
                {content.outputs
                  .map((output) => `${output.data.format}: ${output.state.replaceAll('_', ' ')}`)
                  .join(' · ')}
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
