// Tiny typed fetch helper over the generated contract types (src/api/*.ts, from `pnpm gen:api`).
// Every call goes to a relative /api/<service>/... URL:
//   - in the cluster the gateway routes it to the service
//   - with `pnpm dev` next.config.ts forwards it to the gateway on localhost:8080

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`HTTP ${status}`);
  }
}

export type Served<T> = { data: T; servedBy: string | null };

export async function api<T>(service: string, path: string, init?: RequestInit): Promise<Served<T>> {
  const res = await fetch(`/api/${service}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  // X-Served-By shows which pod@node answered — useful for watching load balancing and failover
  return { data: body as T, servedBy: res.headers.get("x-served-by") };
}
