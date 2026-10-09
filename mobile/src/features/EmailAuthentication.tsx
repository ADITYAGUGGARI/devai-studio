import { useEffect, useRef, useState } from 'react';
import { Text } from 'react-native';
import {
  createNativeStackNavigator,
  type NativeStackScreenProps,
} from '@react-navigation/native-stack';
import { request, saveSession } from '../services/api';
import type { Session } from '../app/state';
import { Screen, Card, Field, Button, ErrorText, styles } from '../components/ui';

type Challenge = { challengeId: string; expiresAt: string; resendAfter: string };
type AuthenticationRoutes = { SignIn: undefined; Verify: { email: string; challenge: Challenge } };
const Stack = createNativeStackNavigator<AuthenticationRoutes>();

function SignIn({ navigation }: NativeStackScreenProps<AuthenticationRoutes, 'SignIn'>) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [local, setLocal] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const pendingKey = useRef('');
  useEffect(() => {
    void request<{ emailConfigured: boolean }>('/v1/auth/capabilities')
      .then((result) => setConfigured(result.emailConfigured))
      .catch(() => setError('Cannot reach the studio. Check your connection.'));
  }, []);
  async function submit() {
    setBusy(true);
    setError('');
    try {
      if (local) {
        await saveSession(await request<Session>('/auth/login', 'POST', { email, password }));
      } else {
        if (!pendingKey.current)
          pendingKey.current = `ios-email-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const challenge = await request<Challenge>(
          '/v1/auth/email/challenges',
          'POST',
          { email },
          { 'Idempotency-Key': pendingKey.current },
        );
        pendingKey.current = '';
        navigation.navigate('Verify', { email, challenge });
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Sign-in failed. Your input is preserved.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <Screen
      title="Your next great story starts here."
      subtitle="Research with confidence. Create with purpose."
    >
      <Card>
        <Field
          label="Email address"
          value={email}
          onChange={(value) => {
            setEmail(value);
            pendingKey.current = '';
          }}
        />
        {local && <Field label="Password" value={password} onChange={setPassword} secure />}
        <ErrorText value={error} />
        {!local && configured === false && (
          <Text style={styles.warning}>
            Email delivery is not configured. An administrator needs to configure SMTP and
            APP_SECRET on the server. Existing local accounts can use password sign-in.
          </Text>
        )}
        <Button
          title={busy ? 'Please wait…' : local ? 'Sign in' : 'Continue with email'}
          disabled={busy || !email || (local ? !password : configured === false)}
          onPress={() => void submit()}
        />
        <Button
          title={local ? 'Use an email code' : 'Use an existing local account'}
          secondary
          onPress={() => {
            setLocal(!local);
            setError('');
          }}
        />
      </Card>
    </Screen>
  );
}

function Verify({ route, navigation }: NativeStackScreenProps<AuthenticationRoutes, 'Verify'>) {
  const { email, challenge } = route.params;
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [now, setNow] = useState(Date.now());
  const pendingKey = useRef('');
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const wait = Math.max(0, Math.ceil((Date.parse(challenge.resendAfter) - now) / 1000));
  const expired = Date.parse(challenge.expiresAt) <= now;
  async function verify() {
    setBusy(true);
    setError('');
    try {
      await saveSession(
        await request<Session>('/v1/auth/email/verify', 'POST', {
          challengeId: challenge.challengeId,
          code,
        }),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : 'Verification failed. Check the code and retry.',
      );
    } finally {
      setBusy(false);
    }
  }
  async function resend() {
    setBusy(true);
    setError('');
    try {
      if (!pendingKey.current)
        pendingKey.current = `ios-email-resend-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const replacement = await request<Challenge>(
        '/v1/auth/email/challenges',
        'POST',
        { email, replaceChallengeId: challenge.challengeId },
        { 'Idempotency-Key': pendingKey.current },
      );
      pendingKey.current = '';
      navigation.setParams({ challenge: replacement });
      setCode('');
      setNow(Date.now());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The code could not be resent. Try again.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <Screen title="Check your email" subtitle={`Enter the six-digit code sent to ${email}.`}>
      <Card>
        <Field
          label="Six-digit code"
          value={code}
          onChange={(value) => setCode(value.replace(/\D/g, ''))}
          oneTimeCode
        />
        <Text accessibilityLiveRegion="polite" style={styles.muted}>
          {expired ? 'Your code expired. Request a new code.' : 'Codes expire in 10 minutes.'}
        </Text>
        <ErrorText value={error} />
        <Button
          title="Verify code"
          disabled={busy || expired || code.length !== 6}
          onPress={() => void verify()}
        />
        <Button
          title={wait > 0 ? `Resend in ${wait}s` : 'Resend code'}
          secondary
          disabled={busy || wait > 0}
          onPress={() => void resend()}
        />
        <Button title="Change email" secondary onPress={() => navigation.goBack()} />
      </Card>
    </Screen>
  );
}

export function EmailAuthentication() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="SignIn" component={SignIn} options={{ title: 'DevAI Studio' }} />
      <Stack.Screen
        name="Verify"
        component={Verify}
        options={{ title: 'Check your email', headerBackTitle: 'Sign in' }}
      />
    </Stack.Navigator>
  );
}
