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

describe("R9 development origin boundary", () => {
  it("R9 original counterexample keeps the same-origin positive control", () => {
    const origin = "http://127.0.0.1:5173";
    expect(isTrustedRenderer(`${origin}/index.html`, origin)).toBe(true);
    expect(isTrustedRenderer("http://127.0.0.1:51730/index.html", origin)).toBe(false);
  });

  it.each([
    ["http://127.0.0.1:5173", "http://127.0.0.1:5173/index.html"],
    ["http://127.0.0.1:5173/", "http://127.0.0.1:5173/other?q=1#settings"],
    ["http://127.0.0.1:5173/base?config=1#x", "http://127.0.0.1:5173/elsewhere?q=2#y"],
    ["http://LOCALHOST:80/", "http://localhost/index.html"],
    ["http://localhost", "http://LOCALHOST:80/index.html"],
    ["https://LOCALHOST:443/", "https://localhost/index.html"],
    ["https://localhost", "https://LOCALHOST:443/index.html"],
    ["http://[::1]:5173", "http://[::1]:5173/index.html"],
    ["http://127.0.0.1:51730", "http://127.0.0.1:51730/index.html"]
  ])("accepts normalized same origin: %s -> %s", (configured, actual) => {
    expect(isTrustedRenderer(actual, configured)).toBe(true);
  });

  it.each([
    ["http://127.0.0.1:5173", "http://127.0.0.1:51730/index.html"],
    ["http://127.0.0.1:5173/", "http://127.0.0.1:51730/index.html"],
    ["http://127.0.0.1:51730", "http://127.0.0.1:5173/index.html"],
    ["http://localhost:5173", "https://localhost:5173/index.html"],
    ["https://localhost:5173", "http://localhost:5173/index.html"],
    ["http://localhost", "http://localhost:81/"],
    ["https://localhost", "https://localhost:444/"],
    ["http://localhost:5173", "http://127.0.0.1:5173/"],
    ["http://127.0.0.1:5173", "http://localhost:5173/"],
    ["http://localhost", "http://localhost.evil.invalid/"],
    ["http://localhost.evil.invalid", "http://localhost/"],
    ["http://localhost", "http://localhost@evil.invalid/"],
    ["http://localhost", "http://user@localhost/"],
    ["http://localhost", "http://user:password@localhost/"],
    ["http://user@localhost", "http://localhost/"],
    ["http://user:password@localhost", "http://user:password@localhost/"],
    ["http://localhost", "blob:http://localhost/virtual-id"],
    ["blob:http://localhost/virtual-id", "blob:http://localhost/virtual-id"],
    ["data:text/plain,virtual", "data:text/plain,virtual"],
    ["javascript:void(0)", "javascript:void(0)"],
    ["ftp://localhost", "ftp://localhost/file"],
    ["http://localhost", "data:text/plain,virtual"],
    ["http://localhost", "javascript:void(0)"],
    ["http://localhost", ""],
    ["http://localhost", "/relative"],
    ["http://localhost", "http://[broken"],
    ["http://[broken", "http://localhost/"],
    ["/relative", "/relative/index"],
    ["", "http://localhost/"],
    [undefined, "http://localhost/"],
    ["null", "null"]
  ])("fails closed without throwing: %s -> %s", (configured, actual) => {
    expect(() => isTrustedRenderer(actual!, configured)).not.toThrow();
    expect(isTrustedRenderer(actual!, configured)).toBe(false);
  });

  it("preserves production schemes and denies similar maris hosts", () => {
    for (const configured of [undefined, "", "http://[broken"]) {
      expect(isTrustedRenderer("file:///app/index.html", configured)).toBe(true);
      expect(isTrustedRenderer("maris://app/index.html", configured)).toBe(true);
      expect(isTrustedRenderer("maris://app.evil.invalid/index.html", configured)).toBe(false);
      expect(isTrustedRenderer("maris://application/index.html", configured)).toBe(false);
    }
  });
});
