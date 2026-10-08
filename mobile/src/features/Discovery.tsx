import { useState } from 'react';
import { Text, View, Pressable, Linking } from 'react-native';
import { useAtomValue } from 'jotai';
import {
  useNavigation,
  useRoute,
  type NavigationProp,
  type RouteProp,
} from '@react-navigation/native';
import { postsAtom, topicsAtom, jobsAtom, sessionAtom } from '../app/state';
import type { Routes } from '../app/navigation';
import { useWork } from '../app/useWork';
import { request } from '../services/api';
import {
  Screen,
  Card,
  Button,
  Field,
  ErrorText,
  Segments,
  styles,
  palette,
} from '../components/ui';

export function Today() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const topics = useAtomValue(topicsAtom),
    posts = useAtomValue(postsAtom),
    jobs = useAtomValue(jobsAtom);
  const { refresh, error, run } = useWork();
  const nextPost =
    posts.find((p) => p.status === 'pending_review') || posts.find((p) => p.status === 'draft');
  const nextTopic = [...topics]
    .filter((t) => t.status === 'queued')
    .sort((a, b) => b.priority - a.priority)[0];
  const active = jobs.filter((j) => ['queued', 'running', 'retry_wait'].includes(j.status));
  return (
    <Screen
      title="Your studio, today"
      subtitle="One story. One carousel. One clear next step."
      onRefresh={() => run(refresh)}
    >
      <View style={styles.row}>
        <Button title="Activity" secondary onPress={() => navigation.navigate('Activity')} />
        <Button title="Settings" secondary onPress={() => navigation.navigate('Operations')} />
      </View>
      <ErrorText value={error} />
      <Card>
        <Text style={styles.muted}>YOUR NEXT STEP</Text>
        <Text style={styles.heading}>
          {nextPost
            ? 'Continue your carousel'
            : nextTopic
              ? 'Choose your next story'
              : 'Discover a fresh story'}
        </Text>
        <Text style={styles.text}>
          {nextPost?.title ||
            nextTopic?.title ||
            'Find credible AI news and turn it into something useful for developers.'}
        </Text>
        <Button
          title={nextPost ? 'Open carousel' : nextTopic ? 'Review story' : 'Explore research'}
          onPress={() =>
            nextPost
              ? navigation.navigate('Review', { id: nextPost.id })
              : nextTopic
                ? navigation.navigate('Topic', { id: nextTopic.id })
                : navigation.navigate('Workspace', { screen: 'Research' })
          }
        />
      </Card>
      <View style={styles.row}>
        {[
          ['In queue', topics.filter((t) => t.status === 'queued').length],
          ['In review', posts.filter((p) => p.status === 'pending_review').length],
          ['Approved', posts.filter((p) => p.status === 'approved').length],
        ].map(([label, count]) => (
          <View
            key={label}
            style={{ flex: 1, backgroundColor: palette.card, padding: 14, borderRadius: 14 }}
          >
            <Text style={styles.title}>{count}</Text>
            <Text style={styles.muted}>{label}</Text>
          </View>
        ))}
      </View>
      {active.length > 0 && (
        <Button
          secondary
          title={`${active.length} background ${active.length === 1 ? 'task' : 'tasks'} in progress`}
          onPress={() => navigation.navigate('Activity')}
        />
      )}
      <View style={[styles.row, { justifyContent: 'space-between' }]}>
        <Text style={styles.heading}>Recent drafts</Text>
        <Button
          secondary
          title="View library"
          onPress={() => navigation.navigate('Workspace', { screen: 'Library' })}
        />
      </View>
      {posts.slice(0, 2).map((post) => (
        <Pressable
          key={post.id}
          accessibilityRole="button"
          accessibilityLabel={`Open ${post.title}`}
          onPress={() => navigation.navigate('Review', { id: post.id })}
        >
          <Card>
            <Text style={styles.muted}>
              {post.status.replaceAll('_', ' ')} · {post.slides.length} slides
            </Text>
            <Text style={styles.heading}>{post.title}</Text>
          </Card>
        </Pressable>
      ))}
      {!posts.length && (
        <Text style={styles.muted}>
          Your first carousel will appear here after you approve a topic.
        </Text>
      )}
    </Screen>
  );
}
export function Research() {
  const topics = useAtomValue(topicsAtom),
    session = useAtomValue(sessionAtom);
  const { busy, error, run, refresh } = useWork();
  const navigation = useNavigation<NavigationProp<Routes>>();
  const [filter, setFilter] = useState<'Queue' | 'Approved' | 'Archived'>('Queue');
  const rows = [...topics]
    .filter((t) =>
      filter === 'Archived'
        ? t.status === 'archived'
        : filter === 'Approved'
          ? t.status !== 'archived' && t.approved
          : t.status !== 'archived' && !t.approved,
    )
    .sort((a, b) => b.priority - a.priority);
  const readOnly = session?.user.role === 'viewer';
  return (
    <Screen
      title="Discover"
      subtitle="Fresh AI stories, ranked for developer impact."
      onRefresh={() => run(refresh)}
    >
      <View style={styles.row}>
        <Button title="Search" disabled={readOnly} onPress={() => navigation.navigate('Search')} />
        <Button
          secondary
          title="Add source to queue"
          disabled={readOnly}
          onPress={() => navigation.navigate('AddSource')}
        />
      </View>
      <Segments
        items={['Queue', 'Approved', 'Archived'] as const}
        value={filter}
        onChange={setFilter}
      />
      <ErrorText value={error} />
      {rows.map((topic, index) => (
        <Pressable
          key={topic.id}
          accessibilityRole="button"
          accessibilityLabel={`Review topic: ${topic.title}`}
          onPress={() => navigation.navigate('Topic', { id: topic.id })}
        >
          <Card>
            <Text style={styles.muted}>
              {String(index + 1).padStart(2, '0')} · {topic.category} ·{' '}
              {topic.status.replaceAll('_', ' ')}
            </Text>
            <Text style={styles.heading}>{topic.title}</Text>
            <Text style={styles.muted}>
              {topic.source} ·{' '}
              {topic.approved
                ? 'Approved'
                : topic.verification === 'unverified'
                  ? 'Needs source review'
                  : 'Source evidence saved'}{' '}
              →
            </Text>
          </Card>
        </Pressable>
      ))}
      {!rows.length && (
        <Card>
          <Text style={styles.heading}>
            {filter === 'Queue'
              ? 'A little inspiration starts here'
              : `No ${filter.toLowerCase()} stories yet`}
          </Text>
          <Text style={styles.muted}>
            {filter === 'Queue'
              ? 'Refresh research to find recent sources, or add an article you want to explain.'
              : 'Review stories in your queue to move them through the workflow.'}
          </Text>
        </Card>
      )}
      <Button
        secondary
        title={busy ? 'Refreshing…' : 'Refresh research'}
        disabled={busy || readOnly}
        onPress={() =>
          void run(async () => {
            await request('/research/refresh', 'POST');
            navigation.navigate('Activity');
          })
        }
      />
    </Screen>
  );
}
export function SearchSources() {
  const [query, setQuery] = useState('');
  const { busy, error, run } = useWork();
  const navigation = useNavigation<NavigationProp<Routes>>();
  return (
    <Screen
      title="Find a story"
      subtitle="Search primary sources for a specific tool, release or engineering question."
    >
      <Field label="Search primary sources" value={query} onChange={setQuery} />
      <ErrorText value={error} />
      <Button
        title={busy ? 'Starting search…' : 'Search developer news'}
        disabled={busy || query.trim().length < 5}
        onPress={() =>
          void run(async () => {
            await request('/research/search', 'POST', { query });
            navigation.navigate('Activity');
          })
        }
      />
      <Text style={styles.muted}>
        Research runs in the background. Readable, verified source evidence is added to Discover
        when the job finishes.
      </Text>
    </Screen>
  );
}
export function AddSource() {
  const [title, setTitle] = useState(''),
    [url, setUrl] = useState(''),
    [excerpt, setExcerpt] = useState('');
  const { busy, error, run } = useWork();
  const navigation = useNavigation<NavigationProp<Routes>>();
  const validUrl = /^https?:\/\/\S+$/i.test(url);
  return (
    <Screen title="Add a source" subtitle="Save an article for a focused source review.">
      <Field label="Story headline" value={title} onChange={setTitle} />
      <Field label="Primary source URL" value={url} onChange={setUrl} />
      <Field label="Source excerpt" value={excerpt} onChange={setExcerpt} multiline />
      <Text style={styles.muted}>
        Include at least 240 characters of factual evidence. You’ll verify it before approving the
        topic.
      </Text>
      <ErrorText value={error} />
      <Button
        title={busy ? 'Saving…' : 'Save source'}
        disabled={busy || excerpt.trim().length < 240 || title.trim().length < 5 || !validUrl}
        onPress={() =>
          void run(async () => {
            const topic = await request<{ id: string }>('/topics', 'POST', { title, url, excerpt });
            navigation.navigate('Topic', { id: topic.id });
          })
        }
      />
    </Screen>
  );
}
export function TopicDetail() {
  const route = useRoute<RouteProp<Routes, 'Topic'>>();
  const topic = useAtomValue(topicsAtom).find((t) => t.id === route.params.id);
  const session = useAtomValue(sessionAtom);
  const navigation = useNavigation<NavigationProp<Routes>>();
  const { busy, error, run } = useWork();
  const [evidence, setEvidence] = useState(false),
    [tools, setTools] = useState(false);
  if (!topic)
    return (
      <Screen title="Story unavailable">
        <Text style={styles.muted}>Return to Discover and refresh your queue.</Text>
      </Screen>
    );
  const locked = busy || session?.user.role === 'viewer';
  const reviewer = ['admin', 'reviewer'].includes(session?.user.role || '');
  const action =
    topic.status === 'queued' ? (
      topic.verification === 'unverified' ? (
        <Button
          title="I reviewed and verified this evidence"
          disabled={locked || !evidence}
          onPress={() => void run(() => request(`/topics/${topic.id}/verify`, 'POST'))}
        />
      ) : !topic.approved ? (
        <Button
          title="Approve topic"
          disabled={locked || !reviewer}
          onPress={() => void run(() => request(`/topics/${topic.id}/approve`, 'POST'))}
        />
      ) : (
        <Button
          title="Generate eight-slide carousel"
          disabled={locked}
          onPress={() =>
            void run(async () => {
              await request(`/topics/${topic.id}/generate`, 'POST', {
                slide_count: 8,
                artwork: true,
              });
              navigation.navigate('Activity');
            })
          }
        />
      )
    ) : topic.post_id ? (
      <Button
        title="Review draft"
        onPress={() => navigation.navigate('Review', { id: topic.post_id! })}
      />
    ) : topic.status === 'archived' ? (
      <Button
        title="Restore topic"
        disabled={locked}
        onPress={() =>
          void run(() => request(`/topics/${topic.id}`, 'PATCH', { status: 'queued' }))
        }
      />
    ) : (
      <Button
        secondary
        title="View generation progress"
        onPress={() => navigation.navigate('Activity')}
      />
    );
  return (
    <Screen
      title={topic.title}
      compactTitle
      subtitle={`${topic.category} · ${topic.status.replaceAll('_', ' ')} · priority ${topic.priority}`}
      footer={action}
    >
      <Button
        secondary
        title="Open primary source"
        onPress={() => void Linking.openURL(topic.url)}
      />
      <Card>
        <Text style={styles.heading}>Why this story?</Text>
        <Text
          style={styles.text}
        >{`This ${topic.category} story is saved from ${topic.source}. Review the original evidence and choose the developer lesson you want to explain.`}</Text>
      </Card>
      <Button
        secondary
        title={evidence ? 'Hide source evidence' : 'Review saved evidence'}
        onPress={() => setEvidence(!evidence)}
      />
      {evidence && (
        <Card>
          <Text style={styles.heading}>Source evidence</Text>
          <Text selectable style={styles.text}>
            {topic.excerpt}
          </Text>
        </Card>
      )}
      {topic.verification === 'unverified' && !evidence && (
        <Text style={styles.muted}>Read the saved evidence before confirming it is accurate.</Text>
      )}
      <ErrorText value={error || topic.error || ''} />
      {topic.approved && topic.status === 'queued' && (
        <Text style={styles.muted}>
          Creates original copy and eight complete AI-generated images. This uses your configured
          provider and may take several minutes. Publishing always needs your approval.
        </Text>
      )}
      <Button
        secondary
        title={tools ? 'Hide topic options' : 'Topic options'}
        onPress={() => setTools(!tools)}
      />
      {tools && topic.status === 'queued' && (
        <View style={styles.row}>
          <Button
            secondary
            title="Raise priority"
            disabled={locked}
            onPress={() =>
              void run(() =>
                request(`/topics/${topic.id}`, 'PATCH', {
                  priority: Math.min(100, topic.priority + 5),
                }),
              )
            }
          />
          <Button
            secondary
            title="Archive"
            disabled={locked}
            onPress={() =>
              void run(() => request(`/topics/${topic.id}`, 'PATCH', { status: 'archived' }))
            }
          />
        </View>
      )}
    </Screen>
  );
}
export function Activity() {
  const jobs = useAtomValue(jobsAtom),
    session = useAtomValue(sessionAtom);
  const { busy, error, run, refresh } = useWork();
  const navigation = useNavigation<NavigationProp<Routes>>();
  const [filter, setFilter] = useState<'Active' | 'Needs attention' | 'History'>('Active');
  const rows = jobs.filter((j) =>
    filter === 'Active'
      ? ['queued', 'running', 'retry_wait'].includes(j.status)
      : filter === 'Needs attention'
        ? ['failed', 'completed_with_warnings', 'needs_reconciliation'].includes(j.status)
        : !['queued', 'running', 'retry_wait'].includes(j.status),
  );
  const [expanded, setExpanded] = useState<string | null>(null);
  return (
    <Screen
      title="Activity"
      subtitle="Work continues here while you explore the studio."
      onRefresh={() => run(refresh)}
    >
      <Segments
        items={['Active', 'Needs attention', 'History'] as const}
        value={filter}
        onChange={setFilter}
      />
      <ErrorText value={error} />
      {!rows.length && (
        <Card>
          <Text style={styles.heading}>
            {filter === 'Active' ? 'Nothing running right now' : 'All clear'}
          </Text>
          <Text style={styles.muted}>New research and generation tasks appear here.</Text>
        </Card>
      )}
      {rows.map((job) => (
        <Card key={job.id}>
          <Text style={styles.heading}>{job.kind.replaceAll('_', ' ')}</Text>
          <Text style={styles.muted}>
            {job.status.replaceAll('_', ' ')} · {job.step || 'Waiting'} · {job.progress}/{job.total}
          </Text>
          <View style={{ height: 4, backgroundColor: palette.border, borderRadius: 4 }}>
            <View
              style={{
                height: 4,
                backgroundColor: palette.accent,
                borderRadius: 4,
                width: `${Math.min(100, job.total > 0 ? (job.progress / job.total) * 100 : 0)}%`,
              }}
            />
          </View>
          {job.result?.post_id && (
            <Button
              title="Review draft"
              onPress={() => navigation.navigate('Review', { id: job.result!.post_id! })}
            />
          )}
          {(job.error || job.result?.warnings?.length || job.result?.grounding) && (
            <Button
              secondary
              title={expanded === job.id ? 'Hide details' : 'View details'}
              onPress={() => setExpanded(expanded === job.id ? null : job.id)}
            />
          )}
          {expanded === job.id && (
            <>
              <ErrorText value={job.error || ''} />
              {job.result?.warnings?.map((w, i) => (
                <Text key={i} style={styles.warning}>
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
            </>
          )}
          {job.status === 'failed' && job.kind !== 'publish' && (
            <Button
              title="Retry job"
              disabled={busy || session?.user.role === 'viewer'}
              onPress={() => void run(() => request(`/jobs/${job.id}/retry`, 'POST'))}
            />
          )}
        </Card>
      ))}
    </Screen>
  );
}
