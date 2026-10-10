import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, request } from '../../services/api';
import type { Topic } from '../../types/posts';
import {
  defaultContentOptions,
  type SetupData,
  type StudioDocument,
  type ProviderCapabilities,
  type OutputFormat,
} from '../../../../shared/content';

export function CreateWizard({
  setupId,
  onDirtyChange,
}: {
  setupId: string | null;
  onDirtyChange: (value: boolean) => void;
}) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [caps, setCaps] = useState<ProviderCapabilities | null>(null);
  const [saved, setSaved] = useState<StudioDocument<SetupData> | null>(null);
  const [draft, setDraft] = useState<SetupData>({
    topicId: params.get('topic') || '',
    formats: ['carousel'],
    options: { ...defaultContentOptions },
  });
  const [step, setStep] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [conflict, setConflict] = useState<StudioDocument<SetupData> | null>(null);
  const key = useRef('');
  const generationKey = useRef('');
  const dirty = Boolean(saved && JSON.stringify(saved.data) !== JSON.stringify(draft));
  useEffect(() => {
    onDirtyChange(dirty);
    return () => onDirtyChange(false);
  }, [dirty, onDirtyChange]);
  useEffect(() => {
    let live = true;
    setError('');
    void Promise.all([
      request<Topic[]>('/topics'),
      request<ProviderCapabilities>('/v1/providers/capabilities'),
      setupId ? request<StudioDocument<SetupData>>(`/v1/setups/${setupId}`) : Promise.resolve(null),
    ])
      .then(([values, capabilities, existing]) => {
        if (!live) return;
        setTopics(values);
        setCaps(capabilities);
        if (existing) {
          setSaved(existing);
          setDraft(existing.data);
          setStep(2);
        }
      })
      .catch((cause) => {
        if (live) setError(cause.message);
      });
    return () => {
      live = false;
    };
  }, [setupId]);
  function edit(value: SetupData) {
    key.current = '';
    setDraft(value);
  }
  async function save(nextStep: number) {
    key.current ||= crypto.randomUUID();
    setBusy(true);
    setError('');
    try {
      const value = await request<StudioDocument<SetupData>>(
        saved ? `/v1/setups/${saved.id}` : '/v1/setups',
        saved ? 'PATCH' : 'POST',
        { ...draft, ...(saved ? { expectedRevision: saved.revision } : {}) },
        { 'Idempotency-Key': key.current },
      );
      setSaved(value);
      setDraft(value.data);
      key.current = '';
      setConflict(null);
      setStep(nextStep);
      if (!setupId) navigate(`/create/${value.id}/configure`, { replace: true });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not save setup');
      if (
        cause instanceof ApiError &&
        cause.status === 409 &&
        typeof cause.detail === 'object' &&
        cause.detail &&
        'server' in cause.detail
      )
        setConflict(cause.detail.server as StudioDocument<SetupData>);
    } finally {
      setBusy(false);
    }
  }
  async function generate() {
    if (!saved || !caps) return;
    generationKey.current ||= crypto.randomUUID();
    setBusy(true);
    setError('');
    try {
      const value = await request<{ contentId: string }>(
        `/v1/setups/${saved.id}/generate`,
        'POST',
        {
          expectedRevision: saved.revision,
          confirmedFormats: saved.data.formats,
          capabilityRevision: caps.revision,
          confirmedBudget: caps.defaultBudgetPerOutput,
          confirmed: true,
        },
        { 'Idempotency-Key': generationKey.current },
      );
      navigate(`/studio-content/${value.contentId}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not start generation');
    } finally {
      setBusy(false);
    }
  }
  const approved = topics.filter(
    (topic) => topic.approved && topic.verification !== 'unverified' && topic.status !== 'archived',
  );
  const topic = topics.find((value) => value.id === draft.topicId);
  const unavailable =
    draft.formats.some((format) => !caps?.formats[format].configured) ||
    (draft.formats.includes('reel') && draft.options.subtitles && !caps?.subtitlesSupported);
  return (
    <section className="creation-workspace" aria-label="Create content">
      <nav className="creation-steps" aria-label="Creation steps">
        {['Topic & format', 'Editorial settings', 'Review & generate'].map((label, index) => (
          <span key={label} aria-current={step === index + 1 ? 'step' : undefined}>
            {index + 1} · {label}
          </span>
        ))}
      </nav>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {conflict && (
        <div className="panel">
          <h2>This setup changed on another device</h2>
          <p>Your choices are retained. Compare them with the saved setup before continuing.</p>
          <pre>{JSON.stringify(conflict.data.options, null, 2)}</pre>
          <button
            className="secondary"
            onClick={() => {
              setSaved(conflict);
              setConflict(null);
            }}
          >
            Keep my choices
          </button>
          <button
            className="secondary"
            onClick={() => {
              setSaved(conflict);
              setDraft(conflict.data);
              setConflict(null);
            }}
          >
            Use saved choices
          </button>
        </div>
      )}
      {!caps && !error ? (
        <p role="status">Loading topics and provider capabilities…</p>
      ) : (
        <>
          {step === 1 && (
            <div className="creation-columns">
              <section className="panel">
                <h2>Start with a story worth explaining</h2>
                <p>
                  Verified evidence and topic approval come first. AI handles the visual design.
                </p>
                <label>
                  Approved topic
                  <select
                    value={draft.topicId}
                    onChange={(event) => edit({ ...draft, topicId: event.target.value })}
                  >
                    <option value="">Choose a topic</option>
                    {approved.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.title}
                      </option>
                    ))}
                  </select>
                </label>
                {!approved.length && (
                  <p>No approved topics yet. Review source evidence in your editorial queue.</p>
                )}
                <button className="secondary" onClick={() => navigate('/discover/queue')}>
                  Review topic queue
                </button>
                {topic && (
                  <div className="source-context">
                    <h3>{topic.title}</h3>
                    <p>
                      {topic.source} · {topic.category}
                    </p>
                    <p>{topic.excerpt.slice(0, 400)}</p>
                  </div>
                )}
              </section>
              <section className="panel">
                <h2>Choose your outputs</h2>
                {(['carousel', 'reel'] as OutputFormat[]).map((format) => (
                  <label className="choice-row" key={format}>
                    <input
                      type="checkbox"
                      checked={draft.formats.includes(format)}
                      onChange={(event) =>
                        edit({
                          ...draft,
                          formats: event.target.checked
                            ? [...draft.formats, format]
                            : draft.formats.filter((value) => value !== format),
                        })
                      }
                    />
                    <span>
                      <strong>
                        {format === 'carousel' ? 'Instagram carousel' : 'Vertical Reel'}
                      </strong>
                      <small>
                        {format === 'carousel'
                          ? '6–8 complete AI-designed slides'
                          : '30–40 second video with scenes and narration'}
                      </small>
                    </span>
                  </label>
                ))}
                <p>Each output has its own progress, review and approval.</p>
                <button
                  className="primary"
                  disabled={busy || !draft.topicId || !draft.formats.length}
                  onClick={() => void save(2)}
                >
                  Continue
                </button>
              </section>
            </div>
          )}
          {step === 2 && (
            <form
              className="creation-columns"
              onSubmit={(event) => {
                event.preventDefault();
                void save(3);
              }}
            >
              <fieldset className="panel" disabled={busy}>
                <legend>Editorial intent</legend>
                <label>
                  Audience
                  <input
                    maxLength={160}
                    required
                    value={draft.options.audience}
                    onChange={(event) =>
                      edit({
                        ...draft,
                        options: { ...draft.options, audience: event.target.value },
                      })
                    }
                  />
                </label>
                <label htmlFor="creation-tone">
                  Tone
                  <select
                    id="creation-tone"
                    aria-label="Tone"
                    value={draft.options.tone}
                    onChange={(event) =>
                      edit({
                        ...draft,
                        options: {
                          ...draft.options,
                          tone: event.target.value as SetupData['options']['tone'],
                        },
                      })
                    }
                  >
                    {['Clear', 'Analytical', 'Conversational', 'Editorial'].map((tone) => (
                      <option key={tone}>{tone}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Language
                  <input value="English" readOnly />
                </label>
                <p>English is supported in this release.</p>
                <div className="source-context">
                  <h2>AI handles the visual design</h2>
                  <p>
                    The model composes each complete image. You don’t need a layout, template or
                    visual prompt.
                  </p>
                </div>
              </fieldset>
              <fieldset className="panel" disabled={busy}>
                <legend>Output settings</legend>
                {draft.formats.includes('carousel') && (
                  <label>
                    Carousel slides
                    <select
                      value={draft.options.slideCount}
                      onChange={(event) =>
                        edit({
                          ...draft,
                          options: { ...draft.options, slideCount: Number(event.target.value) },
                        })
                      }
                    >
                      {[6, 7, 8].map((count) => (
                        <option key={count}>{count}</option>
                      ))}
                    </select>
                  </label>
                )}
                {draft.formats.includes('reel') && (
                  <>
                    <label>
                      Reel duration in seconds
                      <input
                        type="number"
                        min={30}
                        max={40}
                        required
                        value={draft.options.durationSec}
                        onChange={(event) =>
                          edit({
                            ...draft,
                            options: { ...draft.options, durationSec: Number(event.target.value) },
                          })
                        }
                      />
                    </label>
                    <label>
                      Narration voice
                      <select
                        value={draft.options.voiceId || ''}
                        onChange={(event) =>
                          edit({
                            ...draft,
                            options: {
                              ...draft.options,
                              voiceId:
                                (event.target.value as SetupData['options']['voiceId']) || null,
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
                    <label className="choice-row">
                      <input
                        type="checkbox"
                        checked={draft.options.subtitles}
                        onChange={(event) =>
                          edit({
                            ...draft,
                            options: { ...draft.options, subtitles: event.target.checked },
                          })
                        }
                      />
                      Burned-in subtitles
                    </label>
                    <p>Narration is AI-generated and disclosed in the caption.</p>
                  </>
                )}
                <p role="status">{dirty ? 'Unsaved changes' : 'Saved setup'}</p>
                <button className="primary" type="submit">
                  Save & review generation
                </button>
              </fieldset>
            </form>
          )}
          {step === 3 && (
            <div className="panel generation-confirm">
              <div className="eyebrow">READY TO CREATE</div>
              <h2>{topic?.title || 'Your approved story'}</h2>
              <p>
                {draft.formats.join(' + ')} · {draft.options.audience} · {draft.options.tone}
              </p>
              <p>
                This action authorizes up to {caps?.defaultBudgetPerOutput} provider requests per
                output, including retries. Actual usage is recorded. No monetary estimate is shown
                until pricing is configured.
              </p>
              <p>
                Generation continues in the background. Review, approval and publication are
                separate actions.
              </p>
              {!caps?.providerLiveVerified && (
                <p>
                  Provider configuration has not been live-verified. Invalid credentials produce a
                  recoverable job error.
                </p>
              )}
              {unavailable && (
                <p className="error">
                  Generation is unavailable. Configure the server-side provider and required worker
                  codecs.{' '}
                  {draft.formats
                    .flatMap((format) => caps?.formats[format].issues || [])
                    .join(' · ')}
                  {draft.formats.includes('reel') &&
                  draft.options.subtitles &&
                  !caps?.subtitlesSupported
                    ? ' · Worker needs libass subtitle support.'
                    : ''}
                </p>
              )}
              <div className="actions">
                <button className="secondary" onClick={() => setStep(2)}>
                  Back to settings
                </button>
                <button
                  className="primary"
                  disabled={busy || unavailable || dirty}
                  onClick={() => void generate()}
                >
                  {busy ? 'Starting…' : 'Confirm & generate'}
                </button>
              </div>
            </div>
          )}
          {saved?.data.contentId && (
            <button
              className="primary"
              onClick={() => navigate(`/studio-content/${saved.data.contentId}`)}
            >
              Continue existing outputs
            </button>
          )}
        </>
      )}
    </section>
  );
}
