import { useEffect, useState, type ReactNode } from 'react';
import { useAtom } from 'jotai';
import { accountAtom, type Account } from '../app/state';
import { request } from '../services/api';
export function AccountGate({ children }: { children: ReactNode }) {
  const [account, setAccount] = useAtom(accountAtom);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
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
      <form
        className="panel auth-card"
        onSubmit={async (e) => {
          e.preventDefault();
          setError('');
          setLoading(true);
          const data = new FormData(e.currentTarget);
          try {
            const result = await request<{ user: Account }>('/auth/login', 'POST', {
              email: data.get('email'),
              password: data.get('password'),
            });
            setAccount(result.user);
          } catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Sign in failed');
          } finally {
            setLoading(false);
          }
        }}
      >
        <div className="eyebrow">✳ DEVAΙ STUDIO</div>
        <h1>Welcome back.</h1>
        <p className="hint">Sign in to your content workspace.</p>
        <label>
          Email
          <input name="email" type="email" autoComplete="username" required />
        </label>
        <label>
          Password
          <input name="password" type="password" autoComplete="current-password" required />
        </label>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="primary" type="submit">
          Sign in
        </button>
      </form>
    </main>
  );
}
