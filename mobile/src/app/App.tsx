import React, { useEffect, useState, useCallback, useRef, type ReactNode } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  Image,
  Switch,
  StyleSheet,
  Linking,
  Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import {
  NavigationContainer,
  DarkTheme,
  type NavigationProp,
  useNavigation,
  useRoute,
  type RouteProp,
} from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAtom, useAtomValue } from 'jotai';
import { sessionAtom, postsAtom, topicsAtom, jobsAtom } from './state';
import { API_URL, request, saveSession, restoreSession, exportPost } from '../services/api';
import type { Post, Job, Topic } from '../types/posts';

type Routes = { Workspace: undefined; Review: { id: string } };
const Stack = createNativeStackNavigator<Routes>();
const Tabs = createBottomTabNavigator();
const palette = {
  bg: '#0c0e1b',
  card: '#191c31',
  border: '#343956',
  text: '#f4f4ff',
  muted: '#b4bdd9',
  accent: '#ae9cff',
  warning: '#ffd192',
};
function Button({
  title,
  onPress,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={[styles.button, disabled && { opacity: 0.4 }]}
    >
      <Text style={styles.buttonText}>{title}</Text>
    </Pressable>
  );
}
function Field({
  label,
  value,
  onChange,
  multiline = false,
  secure = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
  secure?: boolean;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.muted}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        value={value}
        onChangeText={onChange}
        multiline={multiline}
        secureTextEntry={secure}
        autoCapitalize="none"
        placeholderTextColor={palette.muted}
        style={[styles.input, multiline && { minHeight: 100, textAlignVertical: 'top' }]}
      />
    </View>
  );
}
function Screen({ title, children }: { title: string; children: ReactNode }) {
  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: palette.bg }}
      edges={['left', 'right', 'bottom']}
    >
      <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled">
        <Text accessibilityRole="header" style={styles.title}>
          {title}
        </Text>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}
function Card({ children }: { children: ReactNode }) {
  return <View style={styles.card}>{children}</View>;
}
function useWork() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [, setPosts] = useAtom(postsAtom);
  const [, setTopics] = useAtom(topicsAtom);
  const [, setJobs] = useAtom(jobsAtom);
  const refresh = useCallback(async () => {
    const [posts, topics, jobs] = await Promise.all([
      request<Post[]>('/posts'),
      request<Topic[]>('/topics'),
      request<Job[]>('/jobs'),
    ]);
    setPosts(posts);
    setTopics(topics);
    setJobs(jobs);
  }, [setPosts, setTopics, setJobs]);
  async function run(operation: () => Promise<unknown>) {
    setBusy(true);
    setError('');
    try {
      await operation();
      await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Request failed');
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, run, refresh };
}
function ErrorText({ value }: { value: string }) {
  return value ? (
    <Text accessibilityRole="alert" style={styles.warning}>
      {value}
    </Text>
  ) : null;
}
function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <Screen title="✳ DevAI Studio">
      <Text style={styles.muted}>Your developer content workspace</Text>
      <Card>
        <Text style={styles.heading}>Welcome back</Text>
        <Field label="Email" value={email} onChange={setEmail} />
        <Field label="Password" value={password} onChange={setPassword} secure />
        <ErrorText value={error} />
        <Button
          title="Sign in"
          disabled={busy || !email || !password}
          onPress={() => {
            setBusy(true);
            void request<{ token: string; user: { id: string; email: string; role: string } }>(
              '/auth/login',
              'POST',
              { email, password },
            )
              .then(saveSession)
              .catch((e) => setError(String(e.message)))
              .finally(() => setBusy(false));
          }}
        />
      </Card>
    </Screen>
  );
}
function Research() {
  const topics = useAtomValue(topicsAtom);
  const { busy, error, run } = useWork();
  const [query, setQuery] = useState('');
  const [manual, setManual] = useState(false);
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const navigation = useNavigation<NavigationProp<Routes>>();
  return (
    <Screen title="Research">
      <Text style={styles.muted}>Primary sources → approved topics → original carousels</Text>
      <ErrorText value={error} />
      <Button
        title="Refresh research"
        disabled={busy}
        onPress={() => void run(() => request('/research/refresh', 'POST'))}
      />
      <Card>
        <Field label="Search primary sources" value={query} onChange={setQuery} />
        <Button
          title="Search developer news"
          disabled={busy || query.length < 5}
          onPress={() => void run(() => request('/research/search', 'POST', { query }))}
        />
      </Card>
      <Button
        title={manual ? 'Close manual source' : 'Add source to queue'}
        onPress={() => setManual(!manual)}
      />
      {manual && (
        <Card>
          <Field label="Story headline" value={title} onChange={setTitle} />
          <Field label="Primary source URL" value={url} onChange={setUrl} />
          <Field label="Source excerpt" value={excerpt} onChange={setExcerpt} multiline />
          <Button
            title="Save source"
            disabled={busy || excerpt.length < 240 || title.length < 5}
            onPress={() =>
              void run(async () => {
                await request('/topics', 'POST', { title, url, excerpt });
                setManual(false);
              })
            }
          />
        </Card>
      )}
      {topics.map((topic) => (
        <Card key={topic.id}>
          <Text style={styles.heading}>{topic.title}</Text>
          <Text style={styles.muted}>
            {topic.category} · priority {topic.priority} · {topic.status}
          </Text>
          <Button title="Open primary source" onPress={() => void Linking.openURL(topic.url)} />
          <Text style={styles.text}>{topic.excerpt}</Text>
          <ErrorText value={topic.error || ''} />
          {topic.status === 'queued' && (
            <>
              <View style={styles.row}>
                <Button
                  title="Raise priority"
                  disabled={busy}
                  onPress={() =>
                    void run(() =>
                      request(`/topics/${topic.id}`, 'PATCH', {
                        priority: Math.min(100, topic.priority + 5),
                      }),
                    )
                  }
                />
                <Button
                  title="Archive"
                  disabled={busy}
                  onPress={() =>
                    void run(() => request(`/topics/${topic.id}`, 'PATCH', { status: 'archived' }))
                  }
                />
              </View>
              {topic.verification === 'unverified' ? (
                <Button
                  title="I reviewed and verified this evidence"
                  disabled={busy}
                  onPress={() => void run(() => request(`/topics/${topic.id}/verify`, 'POST'))}
                />
              ) : !topic.approved ? (
                <Button
                  title="Approve topic"
                  disabled={busy}
                  onPress={() => void run(() => request(`/topics/${topic.id}/approve`, 'POST'))}
                />
              ) : (
                <Button
                  title="Generate eight-slide carousel"
                  disabled={busy}
                  onPress={() =>
                    void run(() =>
                      request(`/topics/${topic.id}/generate`, 'POST', {
                        slide_count: 8,
                        artwork: true,
                      }),
                    )
                  }
                />
              )}
            </>
          )}
          {topic.status === 'archived' && (
            <Button
              title="Restore topic"
              onPress={() =>
                void run(() => request(`/topics/${topic.id}`, 'PATCH', { status: 'queued' }))
              }
            />
          )}{' '}
          {topic.post_id && (
            <Button
              title="Review draft"
              onPress={() => navigation.navigate('Review', { id: topic.post_id! })}
            />
          )}
        </Card>
      ))}
    </Screen>
  );
}
function Library() {
  const posts = useAtomValue(postsAtom);
  const jobs = useAtomValue(jobsAtom);
  const { busy, error, run } = useWork();
  const navigation = useNavigation<NavigationProp<Routes>>();
  return (
    <Screen title="Content library">
      <ErrorText value={error} />
      {posts.map((post) => (
        <Pressable
          key={post.id}
          accessibilityRole="button"
          accessibilityLabel={`Review ${post.title}`}
          onPress={() => navigation.navigate('Review', { id: post.id })}
        >
          <Card>
            <Text style={styles.muted}>
              {post.status.toUpperCase()} · VERSION {post.version}
            </Text>
            <Text style={styles.heading}>{post.title}</Text>
            <Text style={styles.muted}>
              {post.slides.length} slides · {post.slides.filter((s) => s.validation?.passed).length}{' '}
              validated
            </Text>
          </Card>
        </Pressable>
      ))}
      {!posts.length && (
        <Text style={styles.muted}>Approve a researched topic to create your first carousel.</Text>
      )}
      <Text accessibilityRole="header" style={styles.heading}>
        Background work
      </Text>
      {jobs.map((job) => (
        <Card key={job.id}>
          <Text style={styles.heading}>
            {job.kind.replaceAll('_', ' ')} · {job.status.replaceAll('_', ' ')}
          </Text>
          <Text style={styles.muted}>
            {job.step} · {job.progress}/{job.total}
          </Text>
          <ErrorText value={job.error || ''} />
          {job.result?.warnings?.map((w) => (
            <Text key={w} style={styles.warning}>
              {w}
            </Text>
          ))}
          {job.result?.grounding?.claims
            ?.filter((c) => c.evidence_matched === false)
            .map((c, i) => (
              <Text key={i} style={styles.warning}>
                {c.claim}: {c.evidence_quote || 'No supporting evidence'}
              </Text>
            ))}
          {job.status === 'failed' && job.kind !== 'publish' && (
            <Button
              title="Retry job"
              disabled={busy}
              onPress={() => void run(() => request(`/jobs/${job.id}/retry`, 'POST'))}
            />
          )}
        </Card>
      ))}
    </Screen>
  );
}
function Review() {
  const route = useRoute<RouteProp<Routes, 'Review'>>();
  const post = useAtomValue(postsAtom).find((p) => p.id === route.params.id);
  const session = useAtomValue(sessionAtom);
  const activeJob = useAtomValue(jobsAtom).some(
    (j) =>
      j.payload.post_id === route.params.id &&
      ['queued', 'running', 'retry_wait'].includes(j.status),
  );
  const { busy, error, run } = useWork();
  const [index, setIndex] = useState(0);
  const [reviewed, setReviewed] = useState(false);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState('');
  const [caption, setCaption] = useState('');
  const [headline, setHeadline] = useState('');
  const [body, setBody] = useState('');
  const [versions, setVersions] = useState<
    { id: string | null; version: string; reason: string }[]
  >([]);
  const [due, setDue] = useState('');
  const [external, setExternal] = useState('');
  const [note, setNote] = useState('');
  const [published, setPublished] = useState(false);
  const previousVersion = useRef('');
  useEffect(() => {
    if (!post || previousVersion.current === post.version) return;
    previousVersion.current = post.version;
    setReviewed(false);
    setEditing(false);
    if (post) {
      setTitle(post.title);
      setCaption(post.caption);
    }
    void request<typeof versions>(`/posts/${route.params.id}/versions`)
      .then(setVersions)
      .catch(() => {});
  }, [post, route.params.id]);
  if (!post)
    return (
      <Screen title="Loading draft">
        <Text style={styles.muted}>Refresh the library to retrieve this post.</Text>
      </Screen>
    );
  const slide = post.slides[index];
  const locked =
    busy ||
    session?.user.role === 'viewer' ||
    ['publishing', 'published'].includes(post.status) ||
    activeJob;
  const ready =
    post.verification?.supported &&
    post.slides.length === 8 &&
    post.slides.every((s) => s.artwork_current && s.validation?.passed);
  const reviewer = ['admin', 'reviewer'].includes(session?.user.role || '');
  return (
    <Screen title={post.title}>
      <Text style={styles.muted}>
        {post.status} · version {post.version}
      </Text>
      <ErrorText value={error} />
      {slide?.has_artwork ? (
        <Image
          accessibilityLabel={`Slide ${index + 1}: ${slide.headline}`}
          source={{
            uri: `${API_URL}/posts/${post.id}/slides/${slide.id}/image?v=${post.version}`,
            headers: { Authorization: `Bearer ${session?.token}` },
          }}
          resizeMode="contain"
          style={styles.artwork}
        />
      ) : (
        <Card>
          <Text style={styles.heading}>{slide?.headline}</Text>
          <Text style={styles.text}>{slide?.body}</Text>
          <Text style={styles.warning}>
            Generate this slide’s complete image to preview artwork.
          </Text>
        </Card>
      )}
      <View style={styles.row}>
        <Button title="Previous slide" disabled={index === 0} onPress={() => setIndex(index - 1)} />
        <Text style={styles.muted}>
          {index + 1}/{post.slides.length}
        </Text>
        <Button
          title="Next slide"
          disabled={index >= post.slides.length - 1}
          onPress={() => setIndex(index + 1)}
        />
      </View>
      <ErrorText value={slide?.validation?.issues.join('; ') || ''} />
      <Card>
        <Text style={styles.heading}>Source and caption</Text>
        <Text style={styles.text}>{post.caption}</Text>
        {post.evidence && (
          <>
            <Button
              title="Read source"
              onPress={() => void Linking.openURL(post.evidence!.source_url)}
            />
            <Text style={styles.text}>{post.evidence.excerpt}</Text>
          </>
        )}
      </Card>
      <Button
        title={editing ? 'Close editor' : 'Edit copy'}
        disabled={locked}
        onPress={() => {
          setEditing(!editing);
          setHeadline(slide?.headline || '');
          setBody(slide?.body || '');
        }}
      />
      {editing && (
        <Card>
          <Field label="Post title" value={title} onChange={setTitle} />
          <Field label="Caption" value={caption} onChange={setCaption} multiline />
          <Button
            title="Save post"
            disabled={locked}
            onPress={() =>
              void run(() => request(`/posts/${post.id}`, 'PATCH', { title, caption }))
            }
          />
          <Field label="Slide headline" value={headline} onChange={setHeadline} />
          <Field label="Slide body" value={body} onChange={setBody} multiline />
          <Button
            title="Save slide"
            disabled={locked}
            onPress={() =>
              void run(() =>
                request(`/posts/${post.id}/slides/${slide.id}`, 'PATCH', { headline, body }),
              )
            }
          />
        </Card>
      )}
      <Button
        title="Verify current copy"
        disabled={locked}
        onPress={() => void run(() => request(`/posts/${post.id}/verify`, 'POST'))}
      />
      <Button
        title="Generate all slide images"
        disabled={locked}
        onPress={() => void run(() => request(`/posts/${post.id}/artwork`, 'POST'))}
      />
      <Button
        title={`Regenerate slide ${index + 1}`}
        disabled={locked}
        onPress={() =>
          void run(() => request(`/posts/${post.id}/slides/${slide.id}/regenerate`, 'POST'))
        }
      />
      <Button
        title="Export carousel ZIP"
        disabled={busy}
        onPress={() => void run(() => exportPost(post.id))}
      />
      {['draft', 'rejected'].includes(post.status) && (
        <Button
          title="Submit for review"
          disabled={locked}
          onPress={() => void run(() => request(`/posts/${post.id}/submit`, 'POST'))}
        />
      )}
      {post.status === 'pending_review' && reviewer && (
        <Card>
          <View style={styles.row}>
            <Switch
              accessibilityLabel="I reviewed sources, copy and every image"
              value={reviewed}
              onValueChange={setReviewed}
            />
            <Text style={styles.text}>I reviewed sources, copy and every image</Text>
          </View>
          <Button
            title="Approve version"
            disabled={locked || !ready || !reviewed}
            onPress={() => void run(() => request(`/posts/${post.id}/approve`, 'POST'))}
          />
          <Button
            title="Reject version"
            disabled={locked}
            onPress={() => void run(() => request(`/posts/${post.id}/reject`, 'POST'))}
          />
        </Card>
      )}
      {post.status === 'approved' && reviewer && (
        <Card>
          <Button
            title="Publish approved carousel"
            disabled={locked}
            onPress={() =>
              Alert.alert('Publish to Instagram', 'Publish this approved version now?', [
                { text: 'Cancel' },
                {
                  text: 'Publish',
                  onPress: () => void run(() => request(`/posts/${post.id}/publish`, 'POST')),
                },
              ])
            }
          />
          <Field label="Publication time (ISO with timezone)" value={due} onChange={setDue} />
          <Button
            title="Schedule approved version"
            disabled={busy || !due}
            onPress={() =>
              void run(() => request(`/posts/${post.id}/schedule`, 'POST', { due_at: due }))
            }
          />
        </Card>
      )}
      {post.status === 'publishing' && reviewer && !activeJob && (
        <Card>
          <Text style={styles.warning}>
            Check Meta activity before reconciling an uncertain publication.
          </Text>
          <Switch
            accessibilityLabel="Confirmed published on Instagram"
            value={published}
            onValueChange={setPublished}
          />
          <Field label="Instagram media ID" value={external} onChange={setExternal} />
          <Field label="Reconciliation notes" value={note} onChange={setNote} />
          <Button
            title="Reconcile publication"
            disabled={busy || note.length < 10 || (published && !external)}
            onPress={() =>
              void run(() =>
                request(`/posts/${post.id}/reconcile`, 'POST', {
                  published,
                  external_id: external || null,
                  note,
                }),
              )
            }
          />
        </Card>
      )}
      <Card>
        <Text style={styles.heading}>Version history</Text>
        {versions.map((v) => (
          <View key={v.version}>
            <Text style={styles.text}>
              Version {v.version} · {v.reason}
            </Text>
            {v.id && v.version !== post.version && (
              <Button
                title={`Restore version ${v.version}`}
                disabled={locked}
                onPress={() =>
                  void run(() => request(`/posts/${post.id}/versions/${v.id}/restore`, 'POST'))
                }
              />
            )}
          </View>
        ))}
      </Card>
    </Screen>
  );
}
function Publishing() {
  const posts = useAtomValue(postsAtom);
  const navigation = useNavigation<NavigationProp<Routes>>();
  const { error, run } = useWork();
  const [rows, setRows] = useState<
    { id: string; post_id: string; due_at: string; status: string; error: string | null }[]
  >([]);
  useEffect(() => {
    const refresh = () =>
      request<typeof rows>('/publishing/schedules')
        .then(setRows)
        .catch(() => {});
    void refresh();
    const timer = setInterval(() => void refresh(), 5000);
    return () => clearInterval(timer);
  }, []);
  return (
    <Screen title="Publishing">
      <ErrorText value={error} />
      <Text style={styles.muted}>
        Review or schedule approved versions. Export is available in each draft.
      </Text>
      {posts
        .filter((p) => ['approved', 'publishing', 'published', 'pending_review'].includes(p.status))
        .map((p) => (
          <Card key={p.id}>
            <Text style={styles.heading}>{p.title}</Text>
            <Text style={styles.muted}>{p.status}</Text>
            <Button
              title="Open publication"
              onPress={() => navigation.navigate('Review', { id: p.id })}
            />
          </Card>
        ))}
      {rows.map((row) => (
        <Card key={row.id}>
          <Text style={styles.text}>
            {posts.find((p) => p.id === row.post_id)?.title || row.post_id}
          </Text>
          <Text style={styles.muted}>
            {new Date(row.due_at).toLocaleString()} · {row.status}
          </Text>
          <ErrorText value={row.error || ''} />
          {row.status === 'scheduled' && (
            <Button
              title="Cancel schedule"
              onPress={() =>
                void run(async () => {
                  await request(`/publishing/schedules/${row.id}/cancel`, 'POST');
                  setRows(await request<typeof rows>('/publishing/schedules'));
                })
              }
            />
          )}
        </Card>
      ))}
    </Screen>
  );
}
interface Ops {
  database: string;
  jobs: Record<string, number>;
  estimated_cost_usd: number;
  unpriced_calls: number;
  settings: {
    daily_enabled: boolean;
    daily_hour: number;
    timezone: string;
    daily_generate_carousel: boolean;
  };
  usage: {
    id: string;
    model: string;
    operation: string;
    images: number;
    input_tokens: number;
    output_tokens: number;
  }[];
}
function AdminControls({
  settings,
  reload,
}: {
  settings: Ops['settings'];
  reload: () => Promise<void>;
}) {
  const { busy, error, run } = useWork();
  const [hour, setHour] = useState(String(settings.daily_hour));
  const [timezone, setTimezone] = useState(settings.timezone);
  const [enabled, setEnabled] = useState(settings.daily_enabled);
  const [draft, setDraft] = useState(settings.daily_generate_carousel);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('editor');
  return (
    <>
      <Card>
        <Text style={styles.heading}>Research schedule</Text>
        <ErrorText value={error} />
        <Text style={styles.muted}>Enable daily research</Text>
        <Switch
          accessibilityLabel="Enable daily research"
          value={enabled}
          onValueChange={setEnabled}
        />
        <Field label="Daily hour (0–23)" value={hour} onChange={setHour} />
        <Field label="Timezone" value={timezone} onChange={setTimezone} />
        <Text style={styles.muted}>Automatically draft from an approved topic</Text>
        <Switch
          accessibilityLabel="Automatically draft from an approved topic"
          value={draft}
          onValueChange={setDraft}
        />
        <Button
          title="Save research schedule"
          disabled={busy || !timezone || !/^([0-9]|1[0-9]|2[0-3])$/.test(hour)}
          onPress={() =>
            void run(async () => {
              await request('/ops/settings', 'PATCH', {
                daily_enabled: enabled,
                daily_hour: Number(hour),
                timezone,
                daily_generate_carousel: draft,
              });
              await reload();
            })
          }
        />
      </Card>
      <Card>
        <Text style={styles.heading}>Create workspace account</Text>
        <Field label="Account email" value={email} onChange={setEmail} />
        <Field label="Initial password" value={password} onChange={setPassword} secure />
        <Text style={styles.muted}>Role: {role}</Text>
        {['editor', 'reviewer', 'viewer', 'admin'].map((value) => (
          <Button key={value} title={'Use ' + value + ' role'} onPress={() => setRole(value)} />
        ))}
        <Button
          title="Create account"
          disabled={busy || !email.includes('@') || password.length < 12}
          onPress={() =>
            void run(async () => {
              await request('/auth/users', 'POST', { email, password, role });
              setEmail('');
              setPassword('');
              await reload();
            })
          }
        />
      </Card>
    </>
  );
}
function Operations() {
  const session = useAtomValue(sessionAtom);
  const { error, run } = useWork();
  const [ops, setOps] = useState<Ops | null>(null);
  useEffect(() => {
    const refresh = () =>
      request<Ops>('/ops/summary')
        .then(setOps)
        .catch(() => {});
    void refresh();
    const timer = setInterval(() => void refresh(), 5000);
    return () => clearInterval(timer);
  }, []);
  return (
    <Screen title="Operations">
      <ErrorText value={error} />
      <Text style={styles.muted}>
        {session?.user.email} · {session?.user.role}
      </Text>
      {ops && (
        <>
          <Card>
            <Text style={styles.heading}>Database · {ops.database}</Text>
            <Text style={styles.text}>Estimated cost ${ops.estimated_cost_usd.toFixed(4)}</Text>
            <Text style={styles.muted}>
              {ops.unpriced_calls} unpriced calls; estimates require configured provider rates.
            </Text>
            {Object.entries(ops.jobs).map(([k, n]) => (
              <Text key={k} style={styles.text}>
                {k}: {n}
              </Text>
            ))}
          </Card>
          <Card>
            <Text style={styles.heading}>
              Daily research · {ops.settings.daily_enabled ? 'enabled' : 'disabled'}
            </Text>
            <Text style={styles.muted}>
              {ops.settings.daily_hour}:00 · {ops.settings.timezone}
            </Text>
            {session?.user.role === 'admin' && (
              <Button
                title={
                  ops.settings.daily_enabled ? 'Disable daily research' : 'Enable daily research'
                }
                onPress={() =>
                  void run(async () => {
                    await request('/ops/settings', 'PATCH', {
                      ...ops.settings,
                      daily_enabled: !ops.settings.daily_enabled,
                    });
                    setOps(await request<Ops>('/ops/summary'));
                  })
                }
              />
            )}
          </Card>
          {session?.user.role === 'admin' && (
            <AdminControls
              key={JSON.stringify(ops.settings)}
              settings={ops.settings}
              reload={async () => setOps(await request<Ops>('/ops/summary'))}
            />
          )}
          {ops.usage.map((u) => (
            <Card key={u.id}>
              <Text style={styles.text}>
                {u.model} · {u.operation}
              </Text>
              <Text style={styles.muted}>
                {u.input_tokens} / {u.output_tokens} tokens · {u.images} images
              </Text>
            </Card>
          ))}
        </>
      )}
      <Button
        title="Sign out"
        onPress={() => void request('/auth/logout', 'POST').finally(() => saveSession(null))}
      />
    </Screen>
  );
}
function Workspace() {
  const { refresh } = useWork();
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    const load = () =>
      refresh().catch((e) => {
        if (active) setError(String(e.message));
      });
    void load();
    const timer = setInterval(() => void load(), 3000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [refresh]);
  return (
    <>
      <ErrorText value={error} />
      <Tabs.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: { backgroundColor: palette.card, borderTopColor: palette.border },
          tabBarActiveTintColor: palette.accent,
          tabBarInactiveTintColor: palette.muted,
        }}
      >
        <Tabs.Screen name="Research" component={Research} />
        <Tabs.Screen name="Library" component={Library} />
        <Tabs.Screen name="Publishing" component={Publishing} />
        <Tabs.Screen name="Operations" component={Operations} />
      </Tabs.Navigator>
    </>
  );
}
export default function App() {
  const session = useAtomValue(sessionAtom);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    void restoreSession().finally(() => setLoading(false));
  }, []);
  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <NavigationContainer
        theme={{
          ...DarkTheme,
          colors: {
            ...DarkTheme.colors,
            background: palette.bg,
            card: palette.card,
            text: palette.text,
            primary: palette.accent,
            border: palette.border,
          },
        }}
      >
        {loading ? (
          <View style={styles.screen}>
            <Text style={styles.text}>Opening your workspace…</Text>
          </View>
        ) : session ? (
          <Stack.Navigator
            screenOptions={{
              headerStyle: { backgroundColor: palette.card },
              headerTintColor: palette.text,
            }}
          >
            <Stack.Screen
              name="Workspace"
              component={Workspace}
              options={{ title: '✳ DevAI Studio' }}
            />
            <Stack.Screen name="Review" component={Review} options={{ title: 'Review carousel' }} />
          </Stack.Navigator>
        ) : (
          <Login />
        )}
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
const styles = StyleSheet.create({
  screen: { padding: 20, gap: 16, paddingBottom: 40, backgroundColor: palette.bg },
  title: { fontSize: 30, fontWeight: '800', color: palette.text },
  heading: { fontSize: 19, fontWeight: '700', color: palette.text },
  text: { color: palette.text, fontSize: 15, lineHeight: 23, flexShrink: 1 },
  muted: { color: palette.muted, fontSize: 13, lineHeight: 20 },
  warning: { color: palette.warning, fontSize: 14, lineHeight: 21 },
  card: {
    padding: 18,
    gap: 12,
    borderRadius: 18,
    backgroundColor: palette.card,
    borderWidth: 1,
    borderColor: palette.border,
  },
  input: {
    padding: 14,
    color: palette.text,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 12,
    backgroundColor: palette.bg,
    fontSize: 16,
  },
  field: { gap: 6 },
  button: {
    paddingHorizontal: 14,
    paddingVertical: 13,
    backgroundColor: '#51428d',
    borderRadius: 12,
    minHeight: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: { color: palette.text, fontSize: 14, fontWeight: '700' },
  row: { flexDirection: 'row', gap: 10, alignItems: 'center', flexWrap: 'wrap' },
  artwork: { width: '100%', aspectRatio: 0.8, borderRadius: 16, backgroundColor: palette.card },
});
