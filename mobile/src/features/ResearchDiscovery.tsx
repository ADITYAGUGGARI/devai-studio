import { useCallback, useState, useRef } from 'react';
import { Text, Linking } from 'react-native';
import { useFocusEffect, useNavigation, type NavigationProp } from '@react-navigation/native';
import { request } from '../services/api';
import { Screen, Card, Button, Field, ErrorText, Segments, styles } from '../components/ui';
import type { Routes } from '../app/navigation';

interface Run {
  id: string;
  jobId: string;
  status: string;
  windowStartUTC: string;
  windowEndUTC: string;
  job: { step: string; progress: number; total: number; cancel_requested: boolean };
  coverage: Record<string, { status: string; error?: string; captured?: number }>;
}
interface Finding {
  id: string;
  title: string;
  source: string;
  score: number;
  url: string;
  disposition: string;
  publishedAt: string | null;
  evidence: { excerpt: string };
  dimensions: Record<string, number>;
}

export function ResearchDiscovery() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const [runs, setRuns] = useState<Run[]>([]);
  const [selected, setSelected] = useState('');
  const [findings, setFindings] = useState<Finding[]>([]);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<'Current' | 'All'>('Current');
  const [cursor, setCursor] = useState('');
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [expanded, setExpanded] = useState('');
  const pendingKey = useRef('');
  const refreshSequence = useRef(0);
  const run = runs.find((item) => item.id === selected) || runs[0];
  const refresh = useCallback(async () => {
    const sequence = ++refreshSequence.current;
    try {
      const history = await request<{ items: Run[] }>('/v1/research/runs');
      if (sequence !== refreshSequence.current) return;
      setRuns(history.items);
      const current = history.items.find((item) => item.id === selected) || history.items[0];
      if (current) {
        const page = await request<{ items: Finding[]; nextCursor: string | null }>(
          `/v1/research/runs/${current.id}/findings?${new URLSearchParams({ q: query, disposition: filter === 'Current' ? 'usable' : '', cursor })}`,
        );
        if (sequence !== refreshSequence.current) return;
        setFindings(page.items);
        setNextCursor(page.nextCursor);
      }
      setError('');
    } catch (cause) {
      if (sequence !== refreshSequence.current) return;
      setError(
        cause instanceof Error
          ? cause.message
          : 'Cannot reach the studio. Saved server work is safe; retry when connected.',
      );
    }
  }, [selected, query, filter, cursor]);
  useFocusEffect(
    useCallback(() => {
      void refresh();
      const timer = setInterval(() => void refresh(), 5000);
      return () => {
        clearInterval(timer);
        refreshSequence.current++;
      };
    }, [refresh]),
  );
  async function start() {
    if (!pendingKey.current)
      pendingKey.current = `ios-research-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setBusy(true);
    try {
      const result = await request<{ runId: string }>(
        '/v1/research/runs',
        'POST',
        {},
        { 'Idempotency-Key': pendingKey.current },
      );
      setSelected(result.runId);
      setCursor('');
      pendingKey.current = '';
      await refresh();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : 'Research could not start. Retry this action.',
      );
    } finally {
      setBusy(false);
    }
  }
  const active = run && ['queued', 'running', 'retry_wait'].includes(run.status);
  return (
    <Screen title="Discover" subtitle="Developer AI news · Last 24 hours" onRefresh={refresh}>
      <ErrorText value={error} />
      <Button
        title="Run research"
        disabled={busy || Boolean(active)}
        onPress={() => void start()}
      />
      <Button
        title="Editorial topic queue"
        secondary
        onPress={() => navigation.navigate('Queue')}
      />
      {run ? (
        <Card>
          <Text style={styles.heading}>Research window</Text>
          <Text style={styles.text}>
            {new Date(run.windowStartUTC).toLocaleString()} —{' '}
            {new Date(run.windowEndUTC).toLocaleString()}
          </Text>
          <Text accessibilityLiveRegion="polite" style={styles.text}>
            {run.job.cancel_requested ? 'Cancelling at a safe checkpoint' : run.status} ·{' '}
            {run.job.step} · {run.job.progress}/{run.job.total}
          </Text>
          {active && (
            <Button
              title="Cancel research"
              secondary
              disabled={run.job.cancel_requested}
              onPress={() =>
                void request(`/v1/jobs/${run.jobId}/cancel`, 'POST')
                  .then(refresh)
                  .catch((cause) => setError(cause.message))
              }
            />
          )}
        </Card>
      ) : (
        <Card>
          <Text style={styles.heading}>Find your next story</Text>
          <Text style={styles.text}>
            Start research to capture source findings. No sample stories are presented as news.
          </Text>
        </Card>
      )}
      <Field
        label="Search captured findings"
        value={query}
        onChange={(value) => {
          setQuery(value);
          setCursor('');
        }}
      />
      <Segments
        items={['Current', 'All'] as const}
        value={filter}
        onChange={(value) => {
          setFilter(value);
          setCursor('');
        }}
      />
      {findings.map((finding) => (
        <Card key={finding.id}>
          <Text style={styles.muted}>
            {finding.source} · {finding.disposition.replaceAll('_', ' ')}
          </Text>
          <Text accessibilityRole="header" style={styles.heading}>
            {finding.title}
          </Text>
          <Text style={styles.text}>
            Priority {finding.score}/100 ·{' '}
            {finding.publishedAt
              ? new Date(finding.publishedAt).toLocaleString()
              : 'Publication date unverified'}
          </Text>
          <Button
            title={
              expanded === finding.id ? 'Hide source and ranking' : 'Inspect source and ranking'
            }
            secondary
            onPress={() => setExpanded(expanded === finding.id ? '' : finding.id)}
          />
          {expanded === finding.id && (
            <>
              <Text style={styles.text}>
                {finding.evidence.excerpt || 'No readable excerpt was supplied.'}
              </Text>
              <Text style={styles.warning}>
                Feed evidence; factual claims need verification before review.
              </Text>
              {Object.entries(finding.dimensions).map(([name, value]) => (
                <Text key={name} style={styles.text}>
                  {name.replaceAll('_', ' ')}: {Math.round(value * 100)}%
                </Text>
              ))}
              <Button
                title="Open original source"
                secondary
                onPress={() =>
                  void Linking.openURL(finding.url).catch(() =>
                    setError('The source could not open. Try again.'),
                  )
                }
              />
            </>
          )}
        </Card>
      ))}
      {run && findings.length === 0 && (
        <Text style={styles.muted}>
          No matching findings. Switch to All to inspect stale, excluded and date-unverified
          results.
        </Text>
      )}
      {cursor && <Button title="Return to first page" secondary onPress={() => setCursor('')} />}
      {nextCursor && (
        <Button title="Next findings" secondary onPress={() => setCursor(nextCursor)} />
      )}
      {run && (
        <Card>
          <Text style={styles.heading}>Research history & coverage</Text>
          {runs.map((item) => (
            <Button
              key={item.id}
              title={`${new Date(item.windowEndUTC).toLocaleString()} · ${item.status}`}
              secondary
              onPress={() => {
                setSelected(item.id);
                setCursor('');
              }}
            />
          ))}
          {Object.entries(run.coverage).map(([name, item]) => (
            <Text key={name} style={styles.text}>
              {name}: {item.status} {item.error || `${item.captured ?? 0} captured`}
            </Text>
          ))}
          <Text style={styles.muted}>Configured feeds only; not exhaustive internet coverage.</Text>
        </Card>
      )}
    </Screen>
  );
}
