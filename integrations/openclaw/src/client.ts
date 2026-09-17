import { performance } from "node:perf_hooks";

import { FinanceProbeError } from "./errors.js";

export const DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000";
export const DEFAULT_TIMEOUT_MS = 5_000;

export type ProbeHealth = {
  status: "ok";
  service: "wife-system";
};

export type ProbeResponse = {
  request_id: string;
  challenge: string;
  receipt: string;
  created_at: string;
  replayed: boolean;
};

export type ProbeLogger = {
  info(message: string): void;
  warn(message: string): void;
};

export type FinanceProbeClientOptions = {
  baseUrl?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
  logger?: ProbeLogger;
};

type RequestOptions = {
  method: "GET" | "POST";
  idempotencyKey?: string;
  body?: string;
  signal?: AbortSignal;
};

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const RECEIPT_PATTERN = /^POC-[A-Za-z0-9_-]+$/;
const TIMEZONE_PATTERN = /(?:Z|[+-]\d{2}:\d{2})$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function isSafeRequestId(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}

function parseHealth(value: unknown): ProbeHealth | null {
  if (!isRecord(value) || !hasExactKeys(value, ["status", "service"])) {
    return null;
  }
  return value.status === "ok" && value.service === "wife-system"
    ? { status: "ok", service: "wife-system" }
    : null;
}

function parseProbe(value: unknown, expectedChallenge: string): ProbeResponse | null {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, [
      "request_id",
      "challenge",
      "receipt",
      "created_at",
      "replayed",
    ]) ||
    !isSafeRequestId(value.request_id) ||
    value.challenge !== expectedChallenge ||
    typeof value.receipt !== "string" ||
    !RECEIPT_PATTERN.test(value.receipt) ||
    typeof value.created_at !== "string" ||
    !TIMEZONE_PATTERN.test(value.created_at) ||
    !Number.isFinite(Date.parse(value.created_at)) ||
    typeof value.replayed !== "boolean"
  ) {
    return null;
  }
  return {
    request_id: value.request_id,
    challenge: value.challenge,
    receipt: value.receipt,
    created_at: value.created_at,
    replayed: value.replayed,
  };
}

function parseErrorRequestId(value: unknown): string | undefined {
  if (!isRecord(value) || !isSafeRequestId(value.request_id)) {
    return undefined;
  }
  return value.request_id;
}

function validateBaseUrl(value: string): URL {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new FinanceProbeError("invalid_request");
  }
  if (
    (url.protocol !== "http:" && url.protocol !== "https:") ||
    !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname.toLowerCase()) ||
    url.username !== "" ||
    url.password !== "" ||
    url.search !== "" ||
    url.hash !== ""
  ) {
    throw new FinanceProbeError("invalid_request");
  }
  url.pathname = url.pathname.endsWith("/") ? url.pathname : `${url.pathname}/`;
  return url;
}

function validateTimeout(value: number): number {
  if (!Number.isFinite(value) || value <= 0 || !Number.isInteger(value)) {
    throw new FinanceProbeError("invalid_request");
  }
  return value;
}

function validateChallenge(challenge: string): void {
  if (challenge.length < 1 || challenge.length > 128 || challenge.trim().length === 0) {
    throw new FinanceProbeError("invalid_request");
  }
}

function validateIdempotencyKey(idempotencyKey: string): void {
  if (
    idempotencyKey.length < 1 ||
    idempotencyKey.length > 256 ||
    idempotencyKey.trim().length === 0
  ) {
    throw new FinanceProbeError("invalid_request");
  }
}

export class FinanceProbeClient {
  readonly #baseUrl: URL;
  readonly #timeoutMs: number;
  readonly #fetch: typeof fetch;
  readonly #logger: ProbeLogger | undefined;

  constructor(options: FinanceProbeClientOptions = {}) {
    this.#baseUrl = validateBaseUrl(options.baseUrl ?? DEFAULT_BACKEND_BASE_URL);
    this.#timeoutMs = validateTimeout(options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    this.#fetch = options.fetchImpl ?? fetch;
    this.#logger = options.logger;
  }

  async health(signal?: AbortSignal): Promise<ProbeHealth> {
    const startedAt = performance.now();
    try {
      const response = await this.#request("healthz", {
        method: "GET",
        ...(signal ? { signal } : {}),
      });
      if (!response.ok) {
        throw this.#statusError(response.status);
      }
      const result = parseHealth(await this.#readJson(response));
      if (result === null) {
        throw new FinanceProbeError("invalid_backend_response");
      }
      this.#log("finance_probe_health_ok", { duration_ms: this.#duration(startedAt) });
      return result;
    } catch (error) {
      const safeError = this.#normalizeError(error);
      this.#logFailure(safeError, startedAt);
      throw safeError;
    }
  }

  async createProbe(
    challenge: string,
    idempotencyKey: string,
    signal?: AbortSignal,
  ): Promise<ProbeResponse> {
    validateChallenge(challenge);
    validateIdempotencyKey(idempotencyKey);
    const startedAt = performance.now();
    try {
      const response = await this.#request("api/v1/probes", {
        method: "POST",
        idempotencyKey,
        body: JSON.stringify({ challenge }),
        ...(signal ? { signal } : {}),
      });
      if (!response.ok) {
        let payload: unknown;
        try {
          payload = await this.#readJson(response);
        } catch {
          payload = undefined;
        }
        throw this.#statusError(response.status, parseErrorRequestId(payload));
      }
      const result = parseProbe(await this.#readJson(response), challenge);
      if (result === null) {
        throw new FinanceProbeError("invalid_backend_response");
      }
      this.#log("finance_probe_completed", {
        request_id: result.request_id,
        receipt: result.receipt,
        replayed: result.replayed,
        duration_ms: this.#duration(startedAt),
      });
      return result;
    } catch (error) {
      const safeError = this.#normalizeError(error);
      this.#logFailure(safeError, startedAt);
      throw safeError;
    }
  }

  async #request(path: string, options: RequestOptions): Promise<Response> {
    const controller = new AbortController();
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, this.#timeoutMs);
    const onExternalAbort = (): void => controller.abort();
    if (options.signal?.aborted) {
      controller.abort();
    } else {
      options.signal?.addEventListener("abort", onExternalAbort, { once: true });
    }

    try {
      const headers = new Headers({ accept: "application/json" });
      if (options.body !== undefined) {
        headers.set("content-type", "application/json");
      }
      if (options.idempotencyKey !== undefined) {
        headers.set("Idempotency-Key", options.idempotencyKey);
      }
      const requestInit: RequestInit = {
        method: options.method,
        headers,
        signal: controller.signal,
        redirect: "error",
        ...(options.body !== undefined ? { body: options.body } : {}),
      };
      return await this.#fetch(new URL(path, this.#baseUrl), requestInit);
    } catch {
      throw new FinanceProbeError(timedOut ? "backend_timeout" : "backend_unavailable");
    } finally {
      clearTimeout(timeout);
      options.signal?.removeEventListener("abort", onExternalAbort);
    }
  }

  async #readJson(response: Response): Promise<unknown> {
    try {
      return JSON.parse(await response.text()) as unknown;
    } catch {
      throw new FinanceProbeError("invalid_backend_response");
    }
  }

  #statusError(status: number, requestId?: string): FinanceProbeError {
    if (status === 409) {
      return new FinanceProbeError("duplicate_request_conflict", requestId);
    }
    if (status === 422) {
      return new FinanceProbeError("invalid_request", requestId);
    }
    if (status >= 500 && status <= 599) {
      return new FinanceProbeError("backend_unavailable", requestId);
    }
    return new FinanceProbeError("invalid_backend_response", requestId);
  }

  #normalizeError(error: unknown): FinanceProbeError {
    return error instanceof FinanceProbeError
      ? error
      : new FinanceProbeError("backend_unavailable");
  }

  #logFailure(error: FinanceProbeError, startedAt: number): void {
    const fields: Record<string, unknown> = {
      code: error.code,
      retryable: error.retryable,
      duration_ms: this.#duration(startedAt),
    };
    if (error.requestId !== undefined) {
      fields.request_id = error.requestId;
    }
    this.#log("finance_probe_failed", fields, true);
  }

  #log(event: string, fields: Record<string, unknown>, warn = false): void {
    const message = JSON.stringify({ event, ...fields });
    if (warn) {
      this.#logger?.warn(message);
    } else {
      this.#logger?.info(message);
    }
  }

  #duration(startedAt: number): number {
    return Math.max(0, Math.round(performance.now() - startedAt));
  }
}
