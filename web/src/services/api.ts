const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
// Development-only credential: Vite values are visible in the browser bundle.
const API_KEY = import.meta.env.VITE_ADMIN_API_KEY || 'local-dev-only';

async function fetchApi(path: string, method = 'GET', body?: unknown): Promise<Response> {
  const response = await fetch(API_URL + path, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`);
  }
  return response;
}

export async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetchApi(path, method, body);
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
