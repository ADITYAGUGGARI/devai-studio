/** SecureStore permits only alphanumeric characters, dots, dashes and underscores. */
export function sessionStorageKey(apiUrl: string): string {
  const url = new URL(apiUrl);
  const identity = url.origin + url.pathname.replace(/\/+$/, '');
  const encoded = Array.from(identity)
    .map((character) => character.codePointAt(0)!.toString(16).padStart(6, '0'))
    .join('');
  return `devai-session-v2-${encoded}`;
}

export function isStoredSession(value: unknown): value is {
  token: string;
  user: { id: string; email: string; role: string };
} {
  if (!value || typeof value !== 'object') return false;
  const session = value as Record<string, unknown>;
  if (typeof session.token !== 'string' || !session.token) return false;
  if (!session.user || typeof session.user !== 'object') return false;
  const user = session.user as Record<string, unknown>;
  return ['id', 'email', 'role'].every((key) => typeof user[key] === 'string' && !!user[key]);
}
