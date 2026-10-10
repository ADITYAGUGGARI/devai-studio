import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Image, Linking, Modal, Switch, Text, View } from 'react-native';
import {
  useFocusEffect,
  useNavigation,
  usePreventRemove,
  useRoute,
  StackActions,
  type NavigationProp,
  type RouteProp,
} from '@react-navigation/native';
import { useAtomValue } from 'jotai';
import { useVideoPlayer, VideoView } from 'expo-video';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { API_URL, ApiError, request } from '../services/api';
import { sessionAtom } from '../app/state';
import type { Routes } from '../app/navigation';
import type { Topic } from '../types/posts';
import { Button, Card, ErrorText, Field, Screen, Segments, styles } from '../components/ui';
import {
  contentList,
  canEditStudio,
  canReviewStudio,
  defaultContentOptions,
  timelinePayload,
  type OutputFormat,
  type ProviderCapabilities,
  type Scene,
  type SetupData,
  type StudioContent,
  type StudioDocument,
  type StudioOutput,
} from '../../../shared/content';

export function StudioProjects() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const canEdit = canEditStudio(useAtomValue(sessionAtom)?.user || null);
  const [projects, setProjects] = useState<StudioContent[]>([]);
  const [error, setError] = useState('');
  useFocusEffect(
    useCallback(() => {
      let live = true;
      void request<{ items: StudioContent[] }>('/v1/content')
        .then(contentList)
        .then((value) => {
          if (live) {
            setProjects(value.items);
            setError('');
          }
        })
        .catch((cause) => {
          if (live) setError(cause.message);
        });
      return () => {
        live = false;
      };
    }, []),
  );
  return (
    <Card>
      <Text style={styles.heading}>Carousel & Reel projects</Text>
      <Button
        title="Create content"
        disabled={!canEdit}
        onPress={() => navigation.navigate('CreateContent', {})}
      />
      <ErrorText value={error} />
      {projects.map((project) => (
        <Button
          key={project.id}
          title={`${project.data.title} · ${project.outputs.map((output) => output.data.format).join(' + ')}`}
          secondary
          onPress={() => navigation.navigate('ContentProject', { id: project.id })}
        />
      ))}
      {!projects.length && !error && (
        <Text style={styles.muted}>
          New projects appear here. Your existing carousels remain below.
        </Text>
      )}
    </Card>
  );
}

export function CreateContent() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const canEdit = canEditStudio(useAtomValue(sessionAtom)?.user || null);
  const route = useRoute<RouteProp<Routes, 'CreateContent'>>();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [caps, setCaps] = useState<ProviderCapabilities | null>(null);
  const [saved, setSaved] = useState<StudioDocument<SetupData> | null>(null);
  const [draft, setDraft] = useState<SetupData>({
    topicId: route.params?.topicId || '',
    formats: ['carousel'],
    options: { ...defaultContentOptions },
  });
  const [step, setStep] = useState(1);
  const [topicSheet, setTopicSheet] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const key = useRef('');
  const generationKey = useRef('');
  const dirty = Boolean(saved && JSON.stringify(saved.data) !== JSON.stringify(draft));
  useEffect(() => {
    void Promise.all([
      request<Topic[]>('/topics'),
      request<ProviderCapabilities>('/v1/providers/capabilities'),
      route.params?.setupId
        ? request<StudioDocument<SetupData>>(`/v1/setups/${route.params.setupId}`)
        : Promise.resolve(null),
    ])
      .then(([values, capabilities, setup]) => {
        setTopics(values);
        setCaps(capabilities);
        if (setup) {
          setSaved(setup);
          setDraft(setup.data);
          setStep(2);
        }
      })
      .catch((cause) => setError(cause.message));
  }, [route.params?.setupId]);
  function edit(value: SetupData) {
    key.current = '';
    setDraft(value);
  }
  async function save(nextStep: number) {
    setBusy(true);
    setError('');
    key.current ||= `${Date.now()}-${Math.random()}`;
    try {
      const value = await request<StudioDocument<SetupData>>(
        saved ? `/v1/setups/${saved.id}` : '/v1/setups',
        saved ? 'PATCH' : 'POST',
        { ...draft, ...(saved ? { expectedRevision: saved.revision } : {}) },
        { 'Idempotency-Key': key.current },
      );
      setSaved(value);
      setDraft(value.data);
      setStep(nextStep);
      key.current = '';
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Save failed');
      if (
        cause instanceof ApiError &&
        cause.status === 409 &&
        typeof cause.detail === 'object' &&
        cause.detail &&
        'server' in cause.detail
      ) {
        const server = cause.detail.server as StudioDocument<SetupData>;
        Alert.alert(
          'Setup changed on another device',
          'Your choices are retained. Choose how to continue.',
          [
            { text: 'Stay', style: 'cancel' },
            {
              text: 'Keep my choices',
              onPress: () => {
                setSaved(server);
                key.current = '';
              },
            },
            {
              text: 'Use saved choices',
              onPress: () => {
                setSaved(server);
                setDraft(server.data);
                key.current = '';
              },
            },
          ],
        );
      }
      return false;
    } finally {
      setBusy(false);
    }
  }
  usePreventRemove(dirty, ({ data }) => {
    Alert.alert(
      'Keep your changes?',
      'Save your setup before leaving, discard local changes, or stay.',
      [
        { text: 'Stay', style: 'cancel' },
        {
          text: 'Discard local changes',
          style: 'destructive',
          onPress: () => navigation.dispatch(data.action),
        },
        {
          text: 'Save and leave',
          onPress: () => {
            void save(step).then((ok) => {
              if (ok) navigation.dispatch(data.action);
            });
          },
        },
      ],
    );
  });
  async function generate() {
    if (!saved || !caps) return;
    setBusy(true);
    setError('');
    generationKey.current ||= `${Date.now()}-${Math.random()}`;
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
      navigation.dispatch(StackActions.replace('ContentProject', { id: value.contentId }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not start generation');
    } finally {
      setBusy(false);
    }
  }
  const selected = topics.find((topic) => topic.id === draft.topicId);
  const approved = topics.filter(
    (topic) => topic.approved && topic.verification !== 'unverified' && topic.status !== 'archived',
  );
  const unavailable =
    draft.formats.some((format) => !caps?.formats[format].configured) ||
    (draft.formats.includes('reel') && draft.options.subtitles && !caps?.subtitlesSupported);
  return (
    <Screen
      title={step === 1 ? 'Choose your story' : step === 2 ? 'Make it useful' : 'Ready to create'}
      subtitle={`Step ${step} of3 · ${dirty ? 'Unsaved changes' : saved ? 'Saved setup' : 'New setup'}`}
      footer={
        <Button
          title={
            busy
              ? 'Working…'
              : step === 3
                ? 'Confirm & generate'
                : step === 2
                  ? 'Save & review'
                  : 'Continue'
          }
          disabled={
            busy ||
            !canEdit ||
            !draft.topicId ||
            !draft.formats.length ||
            (step === 3 && unavailable)
          }
          onPress={() => void (step === 3 ? generate() : save(step + 1))}
        />
      }
    >
      <ErrorText value={error} />
      {!canEdit && (
        <Text style={styles.muted}>
          An owner or editor must save setups and authorize generation. Your current role can
          inspect content.
        </Text>
      )}
      {!caps && !error && (
        <Text style={styles.text}>Loading source and provider configuration…</Text>
      )}
      {step === 1 && (
        <>
          <Card>
            <Text style={styles.heading}>Approved evidence first</Text>
            <Button
              title={selected?.title || 'Choose approved topic'}
              secondary
              onPress={() => setTopicSheet(true)}
            />
            {selected && (
              <Text style={styles.text}>
                {selected.source} · {selected.excerpt.slice(0, 300)}
              </Text>
            )}
            <Button
              title="Review topic queue"
              secondary
              onPress={() => navigation.navigate('Queue')}
            />
          </Card>
          <Card>
            <Text style={styles.heading}>Choose your outputs</Text>
            {(['carousel', 'reel'] as OutputFormat[]).map((format) => (
              <View
                key={format}
                style={{
                  flexDirection: 'row',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  minHeight: 52,
                }}
              >
                <Text style={styles.text}>
                  {format === 'carousel' ? 'Carousel ·6–8slides' : 'Reel ·30–40seconds'}
                </Text>
                <Switch
                  accessibilityLabel={`Generate ${format}`}
                  value={draft.formats.includes(format)}
                  onValueChange={(enabled) =>
                    edit({
                      ...draft,
                      formats: enabled
                        ? [...draft.formats, format]
                        : draft.formats.filter((value) => value !== format),
                    })
                  }
                />
              </View>
            ))}
            <Text style={styles.muted}>Separate output jobs, reviews and approvals.</Text>
          </Card>
        </>
      )}
      {step === 2 && (
        <>
          <Card>
            <Field
              label="Audience"
              value={draft.options.audience}
              onChange={(value) =>
                edit({ ...draft, options: { ...draft.options, audience: value } })
              }
            />
            <Text style={styles.muted}>Tone</Text>
            <Segments
              items={['Clear', 'Analytical', 'Conversational', 'Editorial'] as const}
              value={draft.options.tone}
              onChange={(value) => edit({ ...draft, options: { ...draft.options, tone: value } })}
            />
            <Text style={styles.text}>English · AI handles the complete visual design.</Text>
          </Card>
          <Card>
            {draft.formats.includes('carousel') && (
              <>
                <Text style={styles.muted}>Carousel slides</Text>
                <Segments
                  items={['6', '7', '8'] as const}
                  value={String(draft.options.slideCount) as '6' | '7' | '8'}
                  onChange={(value) =>
                    edit({ ...draft, options: { ...draft.options, slideCount: Number(value) } })
                  }
                />
              </>
            )}
            {draft.formats.includes('reel') && (
              <>
                <Field
                  label="Reel duration (30–40seconds)"
                  value={String(draft.options.durationSec)}
                  onChange={(value) =>
                    edit({ ...draft, options: { ...draft.options, durationSec: Number(value) } })
                  }
                />
                <Text style={styles.muted}>Narration voice · AI-generated</Text>
                <Segments
                  items={['coral', 'marin', 'cedar', 'None'] as const}
                  value={
                    draft.options.voiceId === 'marin' || draft.options.voiceId === 'cedar'
                      ? draft.options.voiceId
                      : draft.options.voiceId
                        ? 'coral'
                        : 'None'
                  }
                  onChange={(value) =>
                    edit({
                      ...draft,
                      options: { ...draft.options, voiceId: value === 'None' ? null : value },
                    })
                  }
                />
                <View
                  style={{
                    flexDirection: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    minHeight: 52,
                  }}
                >
                  <Text style={styles.text}>Burned-in subtitles</Text>
                  <Switch
                    accessibilityLabel="Burned-in subtitles"
                    value={draft.options.subtitles}
                    onValueChange={(value) =>
                      edit({ ...draft, options: { ...draft.options, subtitles: value } })
                    }
                  />
                </View>
              </>
            )}
          </Card>
        </>
      )}
      {step === 3 && (
        <Card>
          <Text style={styles.heading}>{selected?.title || 'Approved story'}</Text>
          <Text style={styles.text}>
            {draft.formats.join(' + ')} · {draft.options.audience}
          </Text>
          <Text style={styles.text}>
            Authorize up to {caps?.defaultBudgetPerOutput} provider requests per output, including
            retries. Actual requests are tracked. No monetary estimate is shown without configured
            pricing.
          </Text>
          <Text style={styles.muted}>
            Jobs continue on the server. Review, approval and publication are separate actions.
          </Text>
          {unavailable && (
            <ErrorText value="Configure the server-side AI provider and required FFmpeg worker codecs before generation." />
          )}
          <Button title="Back to settings" secondary onPress={() => setStep(2)} />
        </Card>
      )}
      {saved?.data.contentId && (
        <Button
          title="Continue existing outputs"
          onPress={() => navigation.navigate('ContentProject', { id: saved.data.contentId! })}
        />
      )}
      <Modal
        visible={topicSheet}
        presentationStyle="pageSheet"
        animationType="slide"
        onRequestClose={() => setTopicSheet(false)}
      >
        <Screen
          safeTop
          title="Choose an approved story"
          footer={<Button title="Done" onPress={() => setTopicSheet(false)} />}
        >
          <Text style={styles.muted}>
            Only topics with verified evidence and explicit approval are eligible.
          </Text>
          {approved.map((topic) => (
            <Button
              key={topic.id}
              secondary
              title={topic.title}
              onPress={() => {
                edit({ ...draft, topicId: topic.id });
                setTopicSheet(false);
              }}
            />
          ))}
        </Screen>
      </Modal>
    </Screen>
  );
}

function NativeReelPlayer({ id, onWatched }: { id: string; onWatched: () => void }) {
  const session = useAtomValue(sessionAtom);
  const player = useVideoPlayer({
    uri: `${API_URL}/v1/assets/${id}`,
    headers: { Authorization: `Bearer ${session?.token}` },
  });
  const [error, setError] = useState('');
  useEffect(() => {
    const end = player.addListener('playToEnd', onWatched);
    const status = player.addListener('statusChange', (event) => {
      if (event.status === 'error') setError(event.error?.message || 'Video playback failed');
    });
    return () => {
      end.remove();
      status.remove();
    };
  }, [player, onWatched]);
  return (
    <View>
      <VideoView
        player={player}
        style={{ width: '100%', height: 330, borderRadius: 16 }}
        nativeControls
        allowsFullscreen
        contentFit="contain"
      />
      <ErrorText value={error} />
    </View>
  );
}

export function ContentProject() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const route = useRoute<RouteProp<Routes, 'ContentProject'>>();
  const session = useAtomValue(sessionAtom);
  const canEdit = canEditStudio(session?.user || null);
  const canReview = canReviewStudio(session?.user || null);
  const [project, setProject] = useState<StudioContent | null>(null);
  const [selected, setSelected] = useState('');
  const [draft, setDraft] = useState<StudioOutput | null>(null);
  const [saved, setSaved] = useState<StudioOutput | null>(null);
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const savedRef = useRef(saved);
  savedRef.current = saved;
  const saving = useRef(false);
  const [status, setStatus] = useState('Saved');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [tool, setTool] = useState<
    'Scenes' | 'Script' | 'Audio' | 'Review' | 'Versions' | 'Sources' | null
  >(null);
  const [versions, setVersions] = useState<{ revision: number; reason: string; state: string }[]>(
    [],
  );
  const [sceneId, setSceneId] = useState('');
  const [checks, setChecks] = useState<Record<string, boolean>>({});
  const [watched, setWatched] = useState(false);
  const [notes, setNotes] = useState('');
  const [conflict, setConflict] = useState(false);
  const actionKey = useRef<{ fingerprint: string; key: string } | null>(null);
  const output = project?.outputs.find((item) => item.id === selected) || project?.outputs[0];
  const editable = (value: StudioOutput) =>
    JSON.stringify({ ...timelinePayload(value), expectedRevision: 0 });
  const dirty = Boolean(draft && saved && editable(draft) !== editable(saved));
  const active = Boolean(
    output?.job && ['queued', 'running', 'retry_wait'].includes(output.job.status),
  );
  const refresh = useCallback(async () => {
    try {
      const value = await request<StudioContent>(`/v1/content/${route.params.id}`);
      setProject(value);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Connection failed');
    }
  }, [route.params.id]);
  useFocusEffect(
    useCallback(() => {
      void refresh();
      const timer = setInterval(() => {
        void refresh();
      }, 2500);
      return () => clearInterval(timer);
    }, [refresh]),
  );
  useEffect(() => {
    if (
      output &&
      (savedRef.current?.id !== output.id ||
        !draftRef.current ||
        editable(draftRef.current) === editable(savedRef.current!))
    ) {
      setDraft(output);
      setSaved(output);
    }
  }, [output]);
  useEffect(() => {
    setChecks({});
    setWatched(false);
  }, [output?.revision, output?.id]);
  async function mutate(path: string, payload: unknown, method = 'POST') {
    const fingerprint = JSON.stringify([path, payload, method]);
    if (actionKey.current?.fingerprint !== fingerprint)
      actionKey.current = { fingerprint, key: `${Date.now()}-${Math.random()}` };
    return request<StudioOutput>(path, method, payload, {
      'Idempotency-Key': actionKey.current.key,
    });
  }
  async function save() {
    if (!draftRef.current || !savedRef.current || saving.current || conflict) return false;
    const value = draftRef.current;
    saving.current = true;
    setStatus('Autosaving…');
    try {
      const response = await mutate(
        `/v1/outputs/${value.id}/timeline`,
        { ...timelinePayload(value), expectedRevision: savedRef.current.revision },
        'PATCH',
      );
      setSaved(response);
      setDraft((current) =>
        current && editable(current) !== editable(value)
          ? { ...current, revision: response.revision }
          : response,
      );
      actionKey.current = null;
      setStatus('Saved');
      setError('');
      return true;
    } catch (cause) {
      setStatus('Save failed · Changes retained');
      setError(cause instanceof Error ? cause.message : 'Save failed');
      if (
        cause instanceof ApiError &&
        cause.status === 409 &&
        typeof cause.detail === 'object' &&
        cause.detail &&
        'server' in cause.detail
      ) {
        const server = cause.detail.server as StudioOutput;
        setConflict(true);
        Alert.alert(
          'Timeline changed on another device',
          'Your changes are retained. Compare the saved caption before choosing: ' +
            server.data.caption.slice(0, 200),
          [
            { text: 'Stay', style: 'cancel' },
            {
              text: 'Keep my changes',
              onPress: () => {
                setSaved(server);
                actionKey.current = null;
                setConflict(false);
              },
            },
            {
              text: 'Use server version',
              onPress: () => {
                setSaved(server);
                setDraft(server);
                actionKey.current = null;
                setConflict(false);
              },
            },
          ],
        );
      }
      return false;
    } finally {
      saving.current = false;
    }
  }
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    if (!dirty || active || conflict) return;
    setStatus('Unsaved changes');
    const timer = setTimeout(() => {
      void saveRef.current();
    }, 800);
    return () => clearTimeout(timer);
  }, [dirty, draft, active, conflict]);
  usePreventRemove(dirty, ({ data }) =>
    Alert.alert('Keep your changes?', 'Saved media and background work remain safe.', [
      { text: 'Stay', style: 'cancel' },
      {
        text: 'Discard local changes',
        style: 'destructive',
        onPress: () => navigation.dispatch(data.action),
      },
      {
        text: 'Save and leave',
        onPress: () => {
          void saveRef.current().then((ok) => {
            if (ok) navigation.dispatch(data.action);
          });
        },
      },
    ]),
  );
  async function run(operation: () => Promise<unknown>) {
    setBusy(true);
    setError('');
    try {
      await operation();
      await refresh();
      actionKey.current = null;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Operation failed');
    } finally {
      setBusy(false);
    }
  }
  function paid(action: string, scene?: string) {
    if (!output) return;
    Alert.alert(
      'Authorize AI provider work',
      `Authorize up to ${scene ? 6 : 32} additional provider requests. Previous media is retained; this output’s approval is invalidated.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm & start',
          onPress: () =>
            void run(() =>
              mutate(
                scene
                  ? `/v1/outputs/${output.id}/scenes/${scene}/generate`
                  : `/v1/outputs/${output.id}/${action}`,
                {
                  expectedRevision: output.revision,
                  confirmed: true,
                  confirmedBudget: scene ? 6 : 32,
                },
              ),
            ),
        },
      ],
    );
  }
  function editScene(id: string, patch: Partial<Scene>) {
    setDraft((value) =>
      value
        ? {
            ...value,
            data: {
              ...value.data,
              scenes: value.data.scenes.map((scene) =>
                scene.id === id ? { ...scene, ...patch } : scene,
              ),
            },
          }
        : value,
    );
  }
  async function exportZip() {
    if (!output || !session) return;
    const target = `${FileSystem.cacheDirectory}devai-${output.id}.zip`;
    const result = await FileSystem.downloadAsync(
      `${API_URL}/v1/outputs/${output.id}/export`,
      target,
      { headers: { Authorization: `Bearer ${session.token}` } },
    );
    if (result.status !== 200) throw new Error('Export failed; validate the current media first');
    if (!(await Sharing.isAvailableAsync()))
      throw new Error('File sharing is unavailable on this device');
    await Sharing.shareAsync(result.uri, {
      mimeType: 'application/zip',
      UTI: 'public.zip-archive',
    });
  }
  function reorderScene(id: string, delta: number) {
    if (active || busy || !canEdit) return;
    setDraft((value) => {
      if (!value) return value;
      const scenes = [...value.data.scenes];
      const at = scenes.findIndex((item) => item.id === id);
      const target = at + delta;
      if (at < 0 || target < 0 || target >= scenes.length) return value;
      [scenes[at], scenes[target]] = [scenes[target], scenes[at]];
      return { ...value, data: { ...value.data, scenes } };
    });
  }
  async function review(action: string) {
    if (!output) return;
    let assetIds = output.data.renderId ? [output.data.renderId] : [];
    if (output.data.postId) {
      const post = await request<{ slides: { id: string }[] }>(`/posts/${output.data.postId}`);
      assetIds = post.slides.map((scene) => scene.id);
    }
    await mutate(`/v1/outputs/${output.id}/review/${action}`, {
      expectedRevision: output.revision,
      confirmed: true,
      checklist: checks,
      reviewedAssetIds: assetIds,
    });
  }
  const onWatched = useCallback(() => setWatched(true), []);
  if (!project || !output || !draft)
    return (
      <Screen title="Opening your content">
        <ErrorText value={error} />
        <Button title="Retry" secondary onPress={() => void refresh()} />
      </Screen>
    );
  const scene = draft.data.scenes.find((value) => value.id === sceneId) || draft.data.scenes[0];
  return (
    <Screen
      title={project.data.title}
      compactTitle
      subtitle={`${output.data.format} · version${output.revision} · ${output.state.replaceAll('_', ' ')}`}
      onRefresh={refresh}
      footer={
        <View>
          <Text style={styles.muted} accessibilityLiveRegion="polite">
            {status}
          </Text>
          <Button
            title="Review this output"
            disabled={dirty || active || busy || !canEdit}
            onPress={() => setTool('Review')}
          />
        </View>
      }
    >
      <ErrorText value={error} />
      <View style={{ flexDirection: 'row', gap: 8 }}>
        {project.outputs.map((value) => (
          <Button
            key={value.id}
            title={value.data.format}
            secondary={value.id !== output.id}
            disabled={dirty}
            onPress={() => setSelected(value.id)}
          />
        ))}
      </View>
      {output.job && (
        <Card>
          <Text style={styles.heading}>{output.job.step}</Text>
          <Text style={styles.text}>
            {output.job.progress}/{output.job.total} completed units ·{' '}
            {output.job.status.replaceAll('_', ' ')}
          </Text>
          <ErrorText value={output.job.error || ''} />
          <Text style={styles.muted}>Jobs continue on the server when you leave.</Text>
          {active && (
            <Button
              title="Cancel at safe checkpoint"
              secondary
              disabled={busy || !canEdit || output.job.cancel_requested}
              onPress={() => void run(() => request(`/v1/jobs/${output.job!.id}/cancel`, 'POST'))}
            />
          )}{' '}
          {['failed', 'retry_wait'].includes(output.job.status) && (
            <Button
              title="Retry existing job"
              disabled={busy}
              onPress={() => void run(() => request(`/jobs/${output.job!.id}/retry`, 'POST'))}
            />
          )}
        </Card>
      )}
      {output.data.format === 'carousel' ? (
        <Card>
          <Text style={styles.heading}>Carousel slides</Text>
          <Text style={styles.text}>
            Inspect every complete AI-generated slide before returning here for independent
            approval.
          </Text>
          {output.data.postId && (
            <Button
              title="Edit & inspect carousel"
              onPress={() => navigation.navigate('Review', { id: output.data.postId! })}
            />
          )}
          <Button
            title="Synchronize current carousel"
            secondary
            disabled={active || busy || !canEdit}
            onPress={() =>
              void run(() =>
                mutate(`/v1/outputs/${output.id}/sync`, {
                  expectedRevision: output.revision,
                  confirmed: true,
                }),
              )
            }
          />
        </Card>
      ) : (
        <>
          <Card>
            {output.data.renderId ? (
              <NativeReelPlayer
                key={output.data.renderId}
                id={output.data.renderId}
                onWatched={onWatched}
              />
            ) : scene?.imageAssetId ? (
              <Image
                source={{
                  uri: `${API_URL}/v1/assets/${scene.imageAssetId}`,
                  headers: { Authorization: `Bearer ${session?.token}` },
                }}
                style={{ height: 330, width: '100%', borderRadius: 16 }}
                resizeMode="contain"
                accessibilityLabel="Saved AI-generated scene preview"
              />
            ) : (
              <Text style={styles.text}>
                No completed video yet. A storyboard becomes a Reel only after MP4 rendering and
                validation.
              </Text>
            )}
            {output.data.renderId && (!output.data.renderCurrent || dirty) && (
              <Text style={styles.muted}>
                Previous render retained · Current timeline needs rendering.
              </Text>
            )}
            <Text style={styles.text}>
              {output.data.renderValidation
                ? `${output.data.renderValidation.duration_seconds.toFixed(1)} seconds · 1080 × 1920`
                : 'MP4 not yet validated'}
            </Text>
            <Button
              title="Render current timeline"
              disabled={busy || active || dirty || !canEdit || !draft.data.scenes.length}
              onPress={() =>
                void run(() =>
                  mutate(`/v1/outputs/${output.id}/render`, {
                    expectedRevision: output.revision,
                    confirmed: true,
                  }),
                )
              }
            />
          </Card>
          <Card>
            <Text style={styles.heading}>Edit your Reel</Text>
            <Button title="Scenes & script" secondary onPress={() => setTool('Scenes')} />
            <Button title="Audio & subtitles" secondary onPress={() => setTool('Audio')} />
            {draft.data.scenes.map((value, index) => (
              <Button
                key={value.id}
                title={`Scene${index + 1} · ${value.headline} · ${value.durationSec}s`}
                secondary
                onPress={() => {
                  setSceneId(value.id);
                  setTool('Script');
                }}
              />
            ))}
          </Card>
        </>
      )}
      <Card>
        <Text style={styles.heading}>Caption & source</Text>
        <Text style={styles.text}>
          {output.data.caption || 'Caption appears after writing completes.'}
        </Text>
        <Text style={styles.muted}>{output.data.source.source}</Text>
        <Button title="Inspect sources & claims" secondary onPress={() => setTool('Sources')} />
        <Button
          title="Export ZIP"
          secondary
          disabled={active || busy || dirty}
          onPress={() => void run(exportZip)}
        />
        <Button
          title="Version history"
          secondary
          disabled={busy || dirty}
          onPress={() =>
            void run(async () => {
              const value = await request<{ items: typeof versions }>(
                `/v1/outputs/${output.id}/versions`,
              );
              setVersions(value.items);
              setTool('Versions');
            })
          }
        />
        <Text style={styles.muted}>
          {output.data.budgetRemaining} authorized provider requests remain.
        </Text>
      </Card>
      <Modal
        visible={tool !== null}
        presentationStyle="pageSheet"
        animationType="slide"
        onRequestClose={() => setTool(null)}
      >
        <Screen
          safeTop
          title={tool === 'Review' ? 'Review this version' : tool || 'Reel tools'}
          footer={
            <Button
              title={dirty ? 'Save & close' : 'Done'}
              disabled={busy}
              onPress={() => {
                if (dirty)
                  void save().then((ok) => {
                    if (ok) setTool(null);
                  });
                else setTool(null);
              }}
            />
          }
        >
          <ErrorText value={error} />
          {tool === 'Sources' && (
            <>
              <Card>
                <Text style={styles.heading}>{output.data.source.title}</Text>
                <Text style={styles.muted}>
                  Saved source evidence · {output.data.source.source}
                </Text>
                <Text style={styles.text}>{output.data.source.excerpt}</Text>
                <Button
                  title="Open original source"
                  secondary
                  onPress={() => void run(() => Linking.openURL(output.data.source.url))}
                />
              </Card>
              <Card>
                <Text style={styles.heading}>Claim grounding</Text>
                <Text style={styles.text}>
                  {output.data.grounding?.supported
                    ? 'Claims supported by the saved evidence. Human source review is still required.'
                    : 'Current copy needs source verification before review.'}
                </Text>
                {output.data.grounding?.claims?.map((claim, index) => (
                  <View key={index} style={{ gap: 8, marginVertical: 12 }}>
                    <Text style={styles.text}>{claim.claim}</Text>
                    <Text style={styles.muted}>Evidence quote: {claim.evidence_quote}</Text>
                  </View>
                ))}
                {output.data.grounding?.issues?.map((issue, index) => (
                  <Text key={index} style={styles.text}>
                    {issue}
                  </Text>
                ))}
                <Text style={styles.muted}>
                  AI editorial interpretation is not an independently verified fact.
                </Text>
              </Card>
            </>
          )}
          {tool === 'Versions' &&
            versions.map((version) => (
              <Card key={version.revision}>
                <Text style={styles.heading}>Version {version.revision}</Text>
                <Text style={styles.text}>
                  {version.reason} · {version.state}
                </Text>
                {output.data.format === 'reel' && (
                  <Button
                    title={`Restore version ${version.revision}`}
                    secondary
                    disabled={
                      busy || active || dirty || !canEdit || version.revision === output.revision
                    }
                    onPress={() =>
                      Alert.alert(
                        'Restore as a new draft?',
                        'Approval is cleared. Previous media, history and your current remaining provider budget are preserved.',
                        [
                          { text: 'Keep current version', style: 'cancel' },
                          {
                            text: 'Restore draft',
                            onPress: () =>
                              void run(async () => {
                                await mutate(`/v1/outputs/${output.id}/versions/restore`, {
                                  expectedRevision: output.revision,
                                  targetRevision: version.revision,
                                  confirmed: true,
                                });
                                setTool(null);
                              }),
                          },
                        ],
                      )
                    }
                  />
                )}
              </Card>
            ))}
          {tool === 'Scenes' && (
            <Button
              title="Add a scene"
              secondary
              disabled={active || busy || !canEdit || draft.data.scenes.length >= 12}
              onPress={() => {
                const id = `scene-${Date.now()}-${Math.random().toString(36).slice(2)}`;
                setDraft({
                  ...draft,
                  data: {
                    ...draft.data,
                    scenes: [
                      ...draft.data.scenes,
                      { id, headline: 'New scene', body: '', script: '', durationSec: 3 },
                    ],
                  },
                });
                setSceneId(id);
                setTool('Script');
              }}
            />
          )}
          {(tool === 'Scenes' || tool === 'Script') && scene && (
            <Card>
              <Text style={styles.text}>
                Timeline:{' '}
                {draft.data.scenes.reduce((total, item) => total + item.durationSec, 0).toFixed(1)}s
                · must total 30–40s
              </Text>
              <Button
                title="Move scene earlier"
                secondary
                disabled={active || busy || !canEdit || draft.data.scenes[0].id === scene.id}
                onPress={() => reorderScene(scene.id, -1)}
              />
              <Button
                title="Move scene later"
                secondary
                disabled={active || busy || !canEdit || draft.data.scenes.at(-1)?.id === scene.id}
                onPress={() => reorderScene(scene.id, 1)}
              />
              <Button
                title="Remove this scene"
                secondary
                disabled={active || busy || !canEdit || draft.data.scenes.length <= 3}
                onPress={() =>
                  Alert.alert(
                    'Remove this scene?',
                    'Saved media remains available in version history. Adjust the remaining durations to 30–40 seconds before saving.',
                    [
                      { text: 'Keep scene', style: 'cancel' },
                      {
                        text: 'Remove scene',
                        style: 'destructive',
                        onPress: () =>
                          setDraft({
                            ...draft,
                            data: {
                              ...draft.data,
                              scenes: draft.data.scenes.filter((item) => item.id !== scene.id),
                            },
                          }),
                      },
                    ],
                  )
                }
              />
              <Field
                disabled={active || busy || !canEdit}
                label="Scene headline"
                value={scene.headline}
                onChange={(value) => editScene(scene.id, { headline: value })}
              />
              <Text style={styles.muted}>
                {scene.imageAssetId
                  ? scene.imageCurrent
                    ? 'Saved scene artwork is current.'
                    : 'Previous artwork retained; regenerate after changing visible copy.'
                  : 'Scene artwork has not been generated.'}
              </Text>
              {scene.lastImageFailure?.map((issue, index) => (
                <Text key={index} style={styles.text}>
                  {issue}
                </Text>
              ))}
              <Field
                disabled={active || busy || !canEdit}
                label="Visible scene body"
                value={scene.body}
                multiline
                onChange={(value) => editScene(scene.id, { body: value })}
              />
              <Field
                disabled={active || busy || !canEdit}
                label="Narration & subtitles"
                value={scene.script}
                multiline
                onChange={(value) => editScene(scene.id, { script: value })}
              />
              <Field
                disabled={active || busy || !canEdit}
                label="Scene duration in seconds"
                value={String(scene.durationSec)}
                onChange={(value) => editScene(scene.id, { durationSec: Number(value) })}
              />
              <Button
                title="Regenerate this scene"
                secondary
                disabled={dirty || active || busy || !canEdit}
                onPress={() => paid('scene', scene.id)}
              />
              <Field
                disabled={active || busy || !canEdit}
                label="Caption"
                value={draft.data.caption}
                multiline
                onChange={(value) =>
                  setDraft({ ...draft, data: { ...draft.data, caption: value } })
                }
              />
            </Card>
          )}
          {tool === 'Audio' && (
            <Card>
              <Text style={styles.muted}>AI narration voice</Text>
              <Segments
                items={['coral', 'marin', 'cedar', 'None'] as const}
                value={
                  draft.data.voiceId === 'marin' || draft.data.voiceId === 'cedar'
                    ? draft.data.voiceId
                    : draft.data.voiceId
                      ? 'coral'
                      : 'None'
                }
                onChange={(value) => {
                  if (active || busy || !canEdit) return;
                  setDraft({
                    ...draft,
                    data: { ...draft.data, voiceId: value === 'None' ? null : value },
                  });
                }}
              />
              <Button
                title="Generate current voiceover"
                disabled={dirty || active || busy || !canEdit || !draft.data.voiceId}
                onPress={() => paid('voiceover')}
              />
              <View
                style={{
                  flexDirection: 'row',
                  justifyContent: 'space-between',
                  minHeight: 52,
                  alignItems: 'center',
                }}
              >
                <Text style={styles.text}>Burned-in subtitles</Text>
                <Switch
                  accessibilityLabel="Burned-in subtitles"
                  disabled={active || busy || !canEdit}
                  value={draft.data.subtitles}
                  onValueChange={(value) =>
                    setDraft({ ...draft, data: { ...draft.data, subtitles: value } })
                  }
                />
              </View>
              <Text style={styles.muted}>
                Changing a voice does not generate audio. Old audio and renders remain preserved.
              </Text>
            </Card>
          )}
          {tool === 'Review' && (
            <>
              <Card>
                <Text style={styles.text}>
                  Approval applies only to this {output.data.format}, version {output.revision}. It
                  does not publish.
                </Text>
                {output.data.format === 'reel' && (
                  <Text style={styles.muted}>
                    {watched
                      ? 'Complete playback inspected.'
                      : 'Play the complete rendered Reel before approval.'}
                  </Text>
                )}
                {['sources', 'claims', 'assets', 'caption'].map((name) => (
                  <View
                    key={name}
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      minHeight: 52,
                    }}
                  >
                    <Text style={styles.text}>Reviewed {name}</Text>
                    <Switch
                      accessibilityLabel={`Reviewed ${name}`}
                      value={checks[name] || false}
                      onValueChange={(value) => setChecks({ ...checks, [name]: value })}
                    />
                  </View>
                ))}
                <Button
                  title="Submit for review"
                  disabled={
                    busy ||
                    active ||
                    !canEdit ||
                    !['sources', 'claims', 'assets', 'caption'].every((name) => checks[name])
                  }
                  onPress={() => void run(() => review('submit'))}
                />
                <Button
                  title="Approve this version"
                  disabled={
                    busy ||
                    active ||
                    !canReview ||
                    output.state !== 'pending_review' ||
                    !['sources', 'claims', 'assets', 'caption'].every((name) => checks[name]) ||
                    (output.data.format === 'reel' && !watched)
                  }
                  onPress={() => void run(() => review('approve'))}
                />
                <Field label="Revision request" value={notes} multiline onChange={setNotes} />
                <Button
                  title="Request changes"
                  secondary
                  disabled={busy || active || !canReview || notes.trim().length < 3}
                  onPress={() =>
                    void run(() =>
                      mutate(`/v1/outputs/${output.id}/changes`, {
                        expectedRevision: output.revision,
                        notes,
                      }),
                    )
                  }
                />
              </Card>
              <Card>
                <Text style={styles.heading}>Grounding report</Text>
                {output.data.grounding?.claims?.map((claim, index) => (
                  <View key={index}>
                    <Text style={styles.text}>{claim.claim}</Text>
                    <Text style={styles.muted}>{claim.evidence_quote}</Text>
                  </View>
                ))}
              </Card>
            </>
          )}
        </Screen>
      </Modal>
    </Screen>
  );
}
