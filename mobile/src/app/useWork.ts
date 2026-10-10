import { useCallback, useState } from 'react';
import { useSetAtom } from 'jotai';
import { postsAtom, topicsAtom, jobsAtom } from './state';
import { request } from '../services/api';
import type { Post, Topic, Job } from '../types/posts';
export function useWork() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const setPosts = useSetAtom(postsAtom),
    setTopics = useSetAtom(topicsAtom),
    setJobs = useSetAtom(jobsAtom);
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
