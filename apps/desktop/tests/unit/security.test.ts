import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { isTrustedRenderer, productionCsp, secureWebPreferences } from "../../electron/main/security";

describe("desktop security shell", () => {
  it("keeps renderer sandboxed without Node integration", () => {
    expect(secureWebPreferences("trusted-preload.js")).toMatchObject({
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      webSecurity: true,
      allowRunningInsecureContent: false
    });
  });

  it("denies renderer network and unknown origins", () => {
    expect(productionCsp).toContain("connect-src 'none'");
    expect(isTrustedRenderer("https://evil.invalid/")).toBe(false);
    expect(isTrustedRenderer("file:///app/index.html")).toBe(true);
  });

  it("keeps process, network, token, nonce, PID, port, and paths out of the preload bridge", () => {
    const source = readFileSync(path.resolve(__dirname, "../../electron/preload/index.ts"), "utf8");
    for (const forbidden of ["child_process", "fetch(", "accessToken", "refreshToken", "startupNonce", "processId", "backendPort", "databasePath"]) expect(source).not.toContain(forbidden);
  });
});
