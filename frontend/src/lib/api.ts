const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export function encodeBasicAuth(username: string, password: string): string {
  return `Basic ${btoa(`${username}:${password}`)}`;
}

export async function apiRequest<T = unknown>(
  path: string,
  auth?: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (auth) headers.set("Authorization", auth);

  const response = await fetch(`${backendUrl}${path.startsWith("/") ? path : `/${path}`}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.text();
    let message = body || response.statusText || `Request failed with status ${response.status}.`;
    if (body) {
      try {
        const parsed: unknown = JSON.parse(body);
        if (typeof parsed === "object" && parsed !== null && "detail" in parsed) {
          const detail = parsed.detail;
          if (typeof detail === "string") message = detail;
        }
      } catch {
        message = body;
      }
    }
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
