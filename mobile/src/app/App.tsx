import { ProfileSettings } from '../features/ProfileSettings';
import React, { useEffect, useState, useRef } from 'react';
import { View, Text, Pressable, ScrollView, Image, Switch, Linking, Alert } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import {
  NavigationContainer,
  DefaultTheme,
  type NavigationProp,
  useNavigation,
  useRoute,
  type RouteProp,
} from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAtomValue } from 'jotai';
import { sessionAtom, postsAtom, jobsAtom } from './state';
import { API_URL, request, saveSession, restoreSession, exportPost } from '../services/api';
import type { Routes, WorkspaceTabs } from './navigation';
import { useWork } from './useWork';
import {
  Button,
  Field,
  Screen,
  Card,
  ErrorText,
  Segments,
  styles,
  palette,
} from '../components/ui';
import {
  Today,
  Research,
  SearchSources,
  AddSource,
  TopicDetail,
  Activity,
} from '../features/Discovery';

import { ResearchDiscovery } from '../features/ResearchDiscovery';
import { EmailAuthentication } from '../features/EmailAuthentication';

const Stack = createNativeStackNavigator<Routes>();
const Tabs = createBottomTabNavigator<WorkspaceTabs>();
function Library() {
  const posts = useAtomValue(postsAtom);
  const session = useAtomValue(sessionAtom);
  const navigation = useNavigation<NavigationProp<Routes>>();
  const { error, run, refresh } = useWork();
  const [filter, setFilter] = useState<'All' | 'Drafts' | 'Review' | 'Approved'>('All');
  const visible = posts.filter(
    (p) =>
      filter === 'All' ||
      (filter === 'Drafts'
        ? ['draft', 'rejected'].includes(p.status)
        : filter === 'Review'
          ? p.status === 'pending_review'
          : p.status === 'approved'),
  );
  return (
    <Screen
      title="Content library"
      subtitle="Your stories, from first draft to final carousel."
      onRefresh={() => run(refresh)}
    >
      <Button
        title="Publishing workspace"
        secondary
        onPress={() => navigation.navigate('Publishing')}
      />
      <Segments
        items={['All', 'Drafts', 'Review', 'Approved'] as const}
        value={filter}
        onChange={setFilter}
      />
      <ErrorText value={error} />
      {visible.map((post) => (
        <Pressable
          key={post.id}
          accessibilityRole="button"
          accessibilityLabel={`Review ${post.title}`}
          onPress={() => navigation.navigate('Review', { id: post.id })}
        >
          <Card>
            {post.slides[0]?.has_artwork && (
              <Image
                source={{
                  uri: `${API_URL}/posts/${post.id}/slides/${post.slides[0].id}/image?v=${post.version}`,
                  headers: { Authorization: `Bearer ${session?.token}` },
                }}
                style={{ width: '100%', height: 160, borderRadius: 12 }}
                resizeMode="cover"
                accessibilityLabel={`Cover: ${post.title}`}
              />
            )}
            <Text style={styles.muted}>
              {post.status.replaceAll('_', ' ').toUpperCase()} · VERSION {post.version}
            </Text>
            <Text style={styles.heading}>{post.title}</Text>
            <Text style={styles.muted}>
              {post.slides.length} slides · {post.slides.filter((s) => s.validation?.passed).length}{' '}
              validated →
            </Text>
          </Card>
        </Pressable>
      ))}
      {!visible.length && (
        <Card>
          <Text style={styles.heading}>A space for your next idea</Text>
          <Text style={styles.muted}>
            Choose a story in Discover and approve it to create a carousel.
          </Text>
          <Button
            secondary
            title="Explore research"
            onPress={() => navigation.navigate('Workspace', { screen: 'Research' })}
          />
        </Card>
      )}
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
  const [section, setSection] = useState<'Slides' | 'Copy' | 'Approval' | 'History'>('Slides');
  const [showEvidence, setShowEvidence] = useState(false);
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
    <Screen
      title={post.title}
      compactTitle
      footer={
        section === 'Slides' ? (
          <Button title="Review copy and sources" onPress={() => setSection('Copy')} />
        ) : section === 'Copy' ? (
          <Button title="Continue to approval" onPress={() => setSection('Approval')} />
        ) : undefined
      }
    >
      <Text style={styles.muted}>
        {post.status} · version {post.version}
      </Text>
      <Segments
        items={['Slides', 'Copy', 'Approval', 'History'] as const}
        value={section}
        onChange={setSection}
      />
      <ErrorText value={error} />
      {section === 'Slides' && (
        <>
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
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: 8 }}
          >
            {post.slides.map((item, position) => (
              <Pressable
                key={item.id}
                accessibilityRole="button"
                accessibilityLabel={`View slide ${position + 1}`}
                accessibilityState={{ selected: index === position }}
                onPress={() => setIndex(position)}
                style={{
                  width: 54,
                  borderWidth: 2,
                  borderColor: index === position ? palette.accent : palette.border,
                  borderRadius: 10,
                  padding: 4,
                }}
              >
                {item.has_artwork ? (
                  <Image
                    source={{
                      uri: `${API_URL}/posts/${post.id}/slides/${item.id}/image?v=${post.version}`,
                      headers: { Authorization: `Bearer ${session?.token}` },
                    }}
                    style={{ width: 42, height: 52, borderRadius: 6 }}
                  />
                ) : (
                  <View style={{ height: 52, justifyContent: 'center' }}>
                    <Text style={styles.muted}>Slide</Text>
                  </View>
                )}
                <Text style={[styles.muted, { textAlign: 'center' }]}>{position + 1}</Text>
              </Pressable>
            ))}
          </ScrollView>
          <View style={styles.row}>
            <Button
              title="Previous slide"
              secondary
              disabled={index === 0}
              onPress={() => setIndex(index - 1)}
            />
            <Text style={styles.muted}>
              {index + 1}/{post.slides.length}
            </Text>
            <Button
              title="Next slide"
              secondary
              disabled={index >= post.slides.length - 1}
              onPress={() => setIndex(index + 1)}
            />
          </View>
          <ErrorText value={slide?.validation?.issues.join('; ') || ''} />
          <Button
            title={`Regenerate slide ${index + 1}`}
            disabled={locked || !slide}
            onPress={() =>
              void run(() => request(`/posts/${post.id}/slides/${slide.id}/regenerate`, 'POST'))
            }
          />
          <Button
            secondary
            title="Generate all slide images"
            disabled={locked}
            onPress={() => void run(() => request(`/posts/${post.id}/artwork`, 'POST'))}
          />
        </>
      )}
      {section === 'Copy' && (
        <>
          <Card>
            <Text style={styles.heading}>Caption</Text>
            <Text style={styles.text}>{post.caption}</Text>
            <Button
              secondary
              title={showEvidence ? 'Hide source evidence' : 'Review source evidence'}
              onPress={() => setShowEvidence(!showEvidence)}
            />
            {post.evidence && showEvidence && (
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
        </>
      )}
      {section === 'Approval' && (
        <>
          <Card>
            <Text style={styles.heading}>Ready to share?</Text>
            <Text style={styles.muted}>
              Review all eight images, the caption and source evidence before approving this
              version.
            </Text>
            <Text style={styles.text}>
              {post.verification?.supported
                ? '✓ Copy grounded in saved evidence'
                : '○ Copy needs source verification'}
            </Text>
            <Text style={styles.text}>
              {post.slides.filter((s) => s.artwork_current && s.validation?.passed).length}/8
              current images validated
            </Text>
          </Card>
          <Button
            secondary
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
        </>
      )}
      {section === 'History' && (
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
      )}
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
  section,
}: {
  section: 'Schedule' | 'Accounts';
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
      {section === 'Schedule' && (
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
      )}
      {section === 'Accounts' && (
        <Card>
          <Text style={styles.heading}>Create workspace account</Text>
          <Field label="Account email" value={email} onChange={setEmail} />
          <Field label="Initial password" value={password} onChange={setPassword} secure />
          <Text style={styles.muted}>Account role</Text>
          <Segments
            items={['editor', 'reviewer', 'viewer', 'admin'] as const}
            value={role}
            onChange={setRole}
          />
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
      )}
    </>
  );
}
function Operations() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const session = useAtomValue(sessionAtom);
  const { error, run } = useWork();
  const [ops, setOps] = useState<Ops | null>(null);
  const [section, setSection] = useState<'Summary' | 'Schedule' | 'Accounts' | 'Usage'>('Summary');
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
    <Screen title="Settings">
      <Button
        title="Profile & preferences"
        secondary
        onPress={() => navigation.navigate('Profile')}
      />
      <ErrorText value={error} />
      <Text style={styles.muted}>
        {session?.user.email} · {session?.user.role}
      </Text>
      <Segments
        items={
          session?.user.role === 'admin'
            ? (['Summary', 'Schedule', 'Accounts', 'Usage'] as const)
            : (['Summary', 'Usage'] as const)
        }
        value={section}
        onChange={setSection}
      />
      {ops && (
        <>
          {section === 'Summary' && (
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
                      ops.settings.daily_enabled
                        ? 'Disable daily research'
                        : 'Enable daily research'
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
            </>
          )}
          {session?.user.role === 'admin' && (section === 'Schedule' || section === 'Accounts') && (
            <AdminControls
              section={section}
              key={JSON.stringify(ops.settings)}
              settings={ops.settings}
              reload={async () => setOps(await request<Ops>('/ops/summary'))}
            />
          )}
          {section === 'Usage' &&
            ops.usage.map((u) => (
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
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ color }) => (
            <Text accessibilityElementsHidden style={{ color, fontSize: 23 }}>
              {
                { Today: '⌂', Research: '⌕', Library: '▤', Activity: '◷', Settings: '⚙' }[
                  route.name
                ]
              }
            </Text>
          ),
          tabBarStyle: { backgroundColor: palette.card, borderTopColor: palette.border },
          tabBarActiveTintColor: palette.accent,
          tabBarInactiveTintColor: palette.muted,
        })}
      >
        <Tabs.Screen name="Today" component={Today} options={{ title: 'Home' }} />
        <Tabs.Screen
          name="Research"
          component={ResearchDiscovery}
          options={{ title: 'Discover' }}
        />
        <Tabs.Screen name="Library" component={Library} options={{ title: 'Content' }} />
        <Tabs.Screen name="Activity" component={Activity} />
        <Tabs.Screen name="Settings" component={Operations} />
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
      <StatusBar style="dark" />
      <NavigationContainer
        theme={{
          ...DefaultTheme,
          colors: {
            ...DefaultTheme.colors,
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
              headerBackButtonDisplayMode: 'minimal',
              headerTitleStyle: { fontSize: 18 },
            }}
          >
            <Stack.Screen
              name="Workspace"
              component={Workspace}
              options={{ title: 'DevAI Studio' }}
            />
            <Stack.Screen
              name="Publishing"
              component={Publishing}
              options={{ title: 'Publishing' }}
            />
            <Stack.Screen
              name="Profile"
              component={ProfileSettings}
              options={{ title: 'Profile & preferences' }}
            />
            <Stack.Screen name="Review" component={Review} options={{ title: 'Review carousel' }} />
            <Stack.Screen
              name="Queue"
              component={Research}
              options={{ title: 'Editorial queue' }}
            />
            <Stack.Screen
              name="Topic"
              component={TopicDetail}
              options={{ title: 'Story details' }}
            />
            <Stack.Screen
              name="Search"
              component={SearchSources}
              options={{ title: 'Search sources' }}
            />
            <Stack.Screen
              name="AddSource"
              component={AddSource}
              options={{ title: 'Add source' }}
            />
            <Stack.Screen name="Activity" component={Activity} options={{ title: 'Activity' }} />
            <Stack.Screen
              name="Operations"
              component={Operations}
              options={{ title: 'Settings' }}
            />
          </Stack.Navigator>
        ) : (
          <EmailAuthentication />
        )}
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
