const apiOrigin = new URL(import.meta.env.VITE_API_URL || 'http://localhost:8000');
// Keep local cookie sessions same-site whichever loopback URL opens the dashboard.
const loopbackHosts = ['localhost', '127.0.0.1', '[::1]'];
if (
  import.meta.env.DEV &&
  loopbackHosts.includes(apiOrigin.hostname) &&
  loopbackHosts.includes(window.location.hostname)
) {
  apiOrigin.hostname = window.location.hostname;
}
const API_URL = apiOrigin.toString().replace(/\/$/, '');
// Development-only credential: Vite values are visible in the browser bundle.
const API_KEY =
  import.meta.env.VITE_DEV_API_KEY_ENABLED === 'true'
    ? import.meta.env.VITE_ADMIN_API_KEY
    : undefined;

async function fetchApi(
  path: string,
  method = 'GET',
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<Response> {
  const response = await fetch(API_URL + path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
      ...headers,
    },
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    const validation = Array.isArray(detail)
      ? detail
          .map(
            (item: { loc?: unknown[]; msg?: string }) =>
              `${item.loc?.filter((part) => part !== 'body').join(' → ') || 'Input'}: ${item.msg || 'Invalid value'}`,
          )
          .join('; ')
      : null;
    throw new Error(
      typeof detail === 'string'
        ? detail
        : validation ||
            (response.status === 401
              ? 'Your session expired. Sign in again to continue; saved work is safe.'
              : `Request failed (${response.status}). Please try again.`),
    );
  }
  return response;
}

export async function request<T>(
  path: string,
  method = 'GET',
  body?: unknown,
  headers: Record<string, string> = {},
): Promise<T> {
  const response = await fetchApi(path, method, body, headers);
  return response.json() as Promise<T>;
}

export async function downloadPost(postId: string): Promise<void> {
  const response = await fetchApi(`/posts/${postId}/export`);
  const href = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a');
  anchor.href = href;
  anchor.download = `devai-${postId}.zip`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export async function loadSlidePreview(postId: string, slideId: string): Promise<string> {
  const response = await fetchApi(`/posts/${postId}/slides/${slideId}/image`);
  return URL.createObjectURL(await response.blob());
}
