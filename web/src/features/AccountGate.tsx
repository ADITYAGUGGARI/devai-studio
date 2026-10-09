import { useEffect, useState, type ReactNode } from 'react';
import { SignInForm } from './SignInForm';
import { useAtom } from 'jotai';
import { accountAtom, type Account } from '../app/state';
import { request } from '../services/api';
export function AccountGate({ children }: { children: ReactNode }) {
  const [account, setAccount] = useAtom(accountAtom);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    request<Account>('/auth/me')
      .then(setAccount)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [setAccount]);
  if (loading)
    return (
      <main className="auth-page">
        <p role="status">Opening your workspace…</p>
      </main>
    );
  if (account) return <>{children}</>;
  return (
    <main className="auth-page">
      <SignInForm onSignedIn={setAccount} />
    </main>
  );
}
