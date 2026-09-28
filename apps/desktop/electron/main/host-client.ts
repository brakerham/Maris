import { z } from "zod";
import type { HostModuleSummary } from "../../src/shared/contracts";
import { DesktopError } from "./desktop-error";

const moduleSchema = z.strictObject({
  module_id: z.string().regex(/^[a-z][a-z0-9_]{0,63}$/),
  version: z.string().regex(/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/),
  display_name: z.string().min(1).max(80),
  enabled: z.boolean(),
  profile_ids: z.array(z.string().min(1).max(140)).readonly(),
  api_prefixes: z.array(z.string().startsWith("/api/v1/")).readonly(),
  settings_schema_version: z.number().int().positive(),
});

export class HostClient {
  #accessToken: string | null = null;
  #refreshFlight: Promise<void> | null = null;

  constructor(
    private readonly endpoint: URL | (() => URL),
    private readonly refreshSession: () => Promise<string>,
    private readonly revokeSession: () => Promise<void> = async () => undefined
  ) {
    if (endpoint instanceof URL) assertLoopback(endpoint);
  }

  setAccessToken(token: string | null): void { this.#accessToken = token; }

  async modules(): Promise<readonly HostModuleSummary[]> {
    let response = await this.#requestModules();
    if (response.status === 401) {
      this.#refreshFlight ??= this.refreshSession()
        .then((token) => { this.#accessToken = token; })
        .finally(() => { this.#refreshFlight = null; });
      try { await this.#refreshFlight; }
      catch { await this.revokeSession(); throw new DesktopError("session_expired", "The local session expired."); }
      response = await this.#requestModules();
    }
    if (response.status === 401) {
      await this.revokeSession();
      this.#accessToken = null;
      throw new DesktopError("session_expired", "The local session expired.");
    }
    if (!response.ok) throw new DesktopError("module_unavailable", "Modules are unavailable.", null, response.status >= 500);
    try {
      return Object.freeze(z.array(moduleSchema).parse(await response.json()));
    } catch {
      throw new DesktopError("module_unavailable", "Modules are unavailable.");
    }
  }

  async #requestModules(): Promise<Response> {
    try {
      const baseUrl = typeof this.endpoint === "function" ? this.endpoint() : this.endpoint;
      assertLoopback(baseUrl);
      return await fetch(new URL("/api/v1/modules", baseUrl), {
        method: "GET",
        headers: this.#accessToken ? { Authorization: `Bearer ${this.#accessToken}` } : {},
        signal: AbortSignal.timeout(5_000),
      });
    } catch {
      throw new DesktopError("backend_offline", "The local Host is unavailable.", null, true);
    }
  }
}

function assertLoopback(baseUrl: URL): void {
  if (baseUrl.protocol !== "http:" || baseUrl.hostname !== "127.0.0.1") {
    throw new DesktopError("invalid_host_url", "Host address is invalid.");
  }
}
