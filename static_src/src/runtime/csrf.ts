// CSRF + fetch (LOGIC-NOTES LN-R01). Consolidates the duplicated helpers from
// the source: token from an explicit override or the `csrftoken` cookie, sent
// as `X-CSRFToken` on unsafe methods.

export function getCsrfToken(explicit?: string): string {
  if (explicit) return explicit;
  const m = typeof document !== "undefined" && document.cookie
    ? document.cookie.match(/csrftoken=([^;]+)/)
    : null;
  return m ? m[1] : "";
}

/** Envelope for a structured StapelError response (LN-R02). */
export interface ErrorEnvelope {
  localizable_error?: string;
  error?: string;
  params?: Record<string, unknown>;
}

/** POST JSON with CSRF; parse the `{localizable_error, error, params}` envelope
 *  on non-2xx and throw it (so the caller renders it, never `alert()`). */
export async function postJson<T = unknown>(
  url: string,
  body: unknown,
  opts: { csrfToken?: string } = {},
): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(opts.csrfToken),
    },
    body: JSON.stringify(body),
    credentials: "same-origin",
  });
  const text = await res.text();
  const data = text ? safeParse(text) : null;
  if (!res.ok) {
    const env: ErrorEnvelope = (data && typeof data === "object" ? data : {}) as ErrorEnvelope;
    throw new StapelError(env, res.status);
  }
  return data as T;
}

export class StapelError extends Error {
  readonly envelope: ErrorEnvelope;
  readonly status: number;
  constructor(envelope: ErrorEnvelope, status: number) {
    super(envelope.localizable_error || envelope.error || `HTTP ${status}`);
    this.name = "StapelError";
    this.envelope = envelope;
    this.status = status;
  }
}

function safeParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
