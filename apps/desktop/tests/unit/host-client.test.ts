import { afterEach, describe, expect, it, vi } from "vitest";
import { HostClient } from "../../electron/main/host-client";

const modules = [{
  module_id: "daily_finance",
  version: "1.0.0",
  display_name: "Daily Finance",
  enabled: true,
  profile_ids: ["daily_finance.default"],
  api_prefixes: ["/api/v1/finance"],
  settings_schema_version: 1,
}];

afterEach(() => vi.unstubAllGlobals());

describe("HostClient", () => {
  it("single-flights refresh and returns only strict module summaries", async () => {
    let requests = 0; let refreshes = 0;
    vi.stubGlobal("fetch", vi.fn(async () => {
      requests++;
      return requests <= 2 ? new Response("", { status: 401 }) : Response.json(modules);
    }));
    const client = new HostClient(new URL("http://127.0.0.1:41000"), async () => { refreshes++; await Promise.resolve(); return "a".repeat(48); });
    client.setAccessToken("b".repeat(48));
    const [left, right] = await Promise.all([client.modules(), client.modules()]);
    expect(left).toEqual(modules); expect(right).toEqual(modules); expect(refreshes).toBe(1);
  });

  it("revokes after the one permitted retry and hides response details", async () => {
    let revoked = 0;
    vi.stubGlobal("fetch", vi.fn(async () => new Response("private detail", { status: 401 })));
    const client = new HostClient(new URL("http://127.0.0.1:41000"), async () => "a".repeat(48), async () => { revoked++; });
    client.setAccessToken("b".repeat(48));
    await expect(client.modules()).rejects.toMatchObject({ code: "session_expired" });
    expect(revoked).toBe(1);
  });

  it("rejects extra Host fields instead of exposing raw payloads", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Response.json([{ ...modules[0], token: "secret" }])));
    const client = new HostClient(new URL("http://127.0.0.1:41000"), async () => "a".repeat(48));
    client.setAccessToken("b".repeat(48));
    await expect(client.modules()).rejects.toMatchObject({ code: "module_unavailable" });
  });
});
