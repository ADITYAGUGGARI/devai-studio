import { atom } from 'jotai';
export interface Account {
  id: string;
  email: string;
  role: 'admin' | 'reviewer' | 'editor' | 'viewer';
  workspace_role?: 'owner' | 'editor' | 'reviewer' | 'viewer';
}
export const accountAtom = atom<Account | null>(null);
export const selectedPostAtom = atom<string | null>(null);
export const navigationAtom = atom('Overview');
