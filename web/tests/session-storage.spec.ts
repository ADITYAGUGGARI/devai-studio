import { expect, test } from '@playwright/test';
import { isStoredSession, sessionStorageKey } from '../../shared/sessionStorage';

test('native sessions are isolated by API origin and deployment path', () => {
  const normal = sessionStorageKey('http://127.0.0.1:8125');
  expect(normal).not.toBe(sessionStorageKey('http://127.0.0.1:8124'));
  expect(normal).not.toBe(sessionStorageKey('https://127.0.0.1:8125'));
  expect(normal).not.toBe(sessionStorageKey('http://127.0.0.1:8125/other'));
  expect(normal).toBe(sessionStorageKey('http://127.0.0.1:8125/'));
  expect(normal).toMatch(/^[a-zA-Z0-9._-]+$/);
});

test('corrupt or incomplete stored sessions cannot become bearer credentials', () => {
  for (const value of [null, [], {}, { token: '' }, { token: 'token', user: {} }])
    expect(isStoredSession(value)).toBe(false);
  expect(
    isStoredSession({
      token: 'token',
      user: { id: 'id', email: 'editor@test.local', role: 'editor' },
    }),
  ).toBe(true);
});
