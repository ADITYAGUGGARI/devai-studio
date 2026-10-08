import { atom } from 'jotai';
import type { Post, Topic, Job } from '../types/posts';
export interface Session {
  token: string;
  user: { id: string; email: string; role: string };
}
export const sessionAtom = atom<Session | null>(null);
export const postsAtom = atom<Post[]>([]);
export const topicsAtom = atom<Topic[]>([]);
export const jobsAtom = atom<Job[]>([]);
