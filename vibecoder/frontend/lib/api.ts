const PUBLIC_API_BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const INTERNAL_API_BASE =
  process.env.BACKEND_INTERNAL_URL || PUBLIC_API_BASE;

function resolveApiBase() {
  return typeof window === "undefined" ? INTERNAL_API_BASE : PUBLIC_API_BASE;
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

export async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const apiBase = resolveApiBase();
  const res = await fetch(`${apiBase}${path.startsWith("/") ? path : `/${path}`}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  return handleResponse(res);
}

export async function postJSON<T>(path: string, body: unknown): Promise<T> {
  return fetchJSON<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
