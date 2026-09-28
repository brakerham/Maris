import { createHash, randomUUID } from "node:crypto";
import { z } from "zod";
import type { OwnerAuthPort, TokenPair } from "./owner-session";

const bootstrapSchema = z.strictObject({ needs_initialization: z.boolean() });
const tokenSchema = z.strictObject({
  session_id: z.string().uuid(),
  device_id: z.string().uuid(),
  access_token: z.string().min(40).max(128),
  refresh_token: z.string().min(40).max(128),
  access_expires_at: z.string().datetime({ offset: true }),
  refresh_expires_at: z.string().datetime({ offset: true }),
});

export class OwnerAuthClient implements OwnerAuthPort {
  constructor(private readonly endpoint: URL | (() => URL), private readonly bootstrapToken: string) {
    if (endpoint instanceof URL) assertLoopback(endpoint);
    if (Buffer.byteLength(bootstrapToken, "utf8") < 32) throw new Error("invalid_bootstrap_token");
  }

  async bootstrapStatus(): Promise<{ needsInitialization: boolean }> {
    const response = await this.#request("/api/v1/auth/bootstrap-status", { method: "GET" });
    const parsed = bootstrapSchema.parse(await response.json());
    return { needsInitialization: parsed.needs_initialization };
  }

  async initialize(credentials: { handle: string; password: string }): Promise<void> {
    await this.#request("/api/v1/auth/initialize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": randomUUID(),
        "X-Bootstrap-Token": this.bootstrapToken,
      },
      body: JSON.stringify(credentials),
    });
  }

  async login(credentials: { handle: string; password: string }): Promise<TokenPair> {
    const response = await this.#request("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        handle: credentials.handle,
        password: credentials.password,
        client_fingerprint: createHash("sha256").update(credentials.handle, "utf8").digest("hex"),
        device_name: "Maris local desktop",
        platform: "windows_desktop",
      }),
    });
    return toTokenPair(await response.json());
  }

  async refresh(refreshToken: string): Promise<TokenPair> {
    const response = await this.#request("/api/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    return toTokenPair(await response.json());
  }

  async #request(path: string, init: RequestInit): Promise<Response> {
    let response: Response;
    try {
      response = await fetch(new URL(path, this.#baseUrl()), { ...init, signal: AbortSignal.timeout(5_000) });
    } catch {
      throw new Error("owner_auth_unavailable");
    }
    if (!response.ok) throw new Error(response.status === 401 ? "owner_auth_rejected" : "owner_auth_failed");
    return response;
  }

  #baseUrl(): URL {
    const value = typeof this.endpoint === "function" ? this.endpoint() : this.endpoint;
    assertLoopback(value);
    return value;
  }
}

function toTokenPair(value: unknown): TokenPair {
  const parsed = tokenSchema.parse(value);
  return { accessToken: parsed.access_token, refreshToken: parsed.refresh_token };
}

function assertLoopback(value: URL): void {
  if (value.protocol !== "http:" || value.hostname !== "127.0.0.1") throw new Error("invalid_host_url");
}
