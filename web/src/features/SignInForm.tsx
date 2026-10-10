import { useEffect, useState, useRef } from 'react';
import type { Account } from '../app/state';
import { ApiError, request } from '../services/api';

interface Challenge {
  challengeId: string;
  expiresAt: string;
  resendAfter: string;
}

export function SignInForm({ onSignedIn }: { onSignedIn: (account: Account) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [method, setMethod] = useState<'email' | 'password'>('email');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [capabilities, setCapabilities] = useState<{
    emailConfigured: boolean;
    passwordLoginAvailable: boolean;
  } | null>(null);
  const [now, setNow] = useState(Date.now());
  const pendingKey = useRef('');
  useEffect(() => {
    void request<{ emailConfigured: boolean; passwordLoginAvailable: boolean }>(
      '/v1/auth/capabilities',
    )
      .then(setCapabilities)
      .catch(() => setError('Cannot reach the studio. Check your connection and retry.'));
  }, []);
  useEffect(() => {
    if (!challenge) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [challenge]);
  async function sendCode() {
    if (!pendingKey.current) pendingKey.current = crypto.randomUUID();
    setBusy(true);
    setError('');
    try {
      const result = await request<Challenge>(
        '/v1/auth/email/challenges',
        'POST',
        {
          email,
          replaceChallengeId: challenge?.challengeId,
        },
        { 'Idempotency-Key': pendingKey.current },
      );
      pendingKey.current = '';
      setChallenge(result);
      setCode('');
      setNow(Date.now());
    } catch (cause) {
      // A received failure is a completed action; network uncertainty retains the retry key.
      if (cause instanceof ApiError) pendingKey.current = '';
      setError(cause instanceof Error ? cause.message : 'The code could not be sent. Try again.');
    } finally {
      setBusy(false);
    }
  }
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (method === 'email' && !challenge) {
      await sendCode();
      return;
    }
    setBusy(true);
    setError('');
    try {
      const result = await request<{ user: Account }>(
        method === 'password' ? '/auth/login' : '/v1/auth/email/verify',
        'POST',
        method === 'password' ? { email, password } : { challengeId: challenge!.challengeId, code },
      );
      onSignedIn(result.user);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Sign-in failed. Your input is preserved.');
    } finally {
      setBusy(false);
    }
  }
  const wait = challenge
    ? Math.max(0, Math.ceil((Date.parse(challenge.resendAfter) - now) / 1000))
    : 0;
  const expired = challenge && Date.parse(challenge.expiresAt) <= now;
  return (
    <form className="panel auth-card" onSubmit={(event) => void submit(event)}>
      <div className="eyebrow">✳ DEVAΙ STUDIO</div>
      <h1>{challenge ? 'Check your email' : 'Your next great story starts here.'}</h1>
      <p className="hint">
        {challenge
          ? `Enter the six-digit code sent to ${email}.`
          : 'Research with confidence. Create with purpose.'}
      </p>
      {!challenge && (
        <label>
          Email address
          <input
            name="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => {
              pendingKey.current = '';
              setEmail(event.target.value);
            }}
          />
        </label>
      )}
      {method === 'password' && (
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
      )}
      {challenge && (
        <>
          <label>
            Six-digit code
            <input
              name="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))}
            />
          </label>
          <p role="status">
            {expired ? 'The code expired. Request a new code.' : 'This code expires in 10 minutes.'}
          </p>
        </>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {method === 'email' && capabilities && !capabilities.emailConfigured && (
        <p className="run-warning">
          Email sign-in is unavailable. Ask your studio administrator to enable it, or use an
          existing local account below.
        </p>
      )}
      <button
        className="primary"
        type="submit"
        disabled={
          busy ||
          Boolean(expired) ||
          (method === 'email' && capabilities?.emailConfigured === false)
        }
      >
        {busy
          ? 'Please wait…'
          : method === 'password'
            ? 'Sign in'
            : challenge
              ? 'Verify code'
              : 'Continue with email'}
      </button>
      {challenge && (
        <div className="actions">
          <button
            type="button"
            className="secondary"
            disabled={busy || wait > 0}
            onClick={() => void sendCode()}
          >
            {wait > 0 ? `Resend in ${wait}s` : 'Resend code'}
          </button>
          <button
            type="button"
            className="ghost"
            onClick={() => {
              setChallenge(null);
              setCode('');
              setError('');
            }}
          >
            Change email
          </button>
        </div>
      )}
      {!challenge && (
        <button
          className="ghost"
          type="button"
          onClick={() => {
            setMethod(method === 'password' ? 'email' : 'password');
            setError('');
          }}
        >
          {method === 'password' ? 'Use an email code' : 'Use an existing local account'}
        </button>
      )}
    </form>
  );
}
