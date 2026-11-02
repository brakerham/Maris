import type { BrowserWindowConstructorOptions } from "electron";

export const productionCsp = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self' data:",
  "connect-src 'none'",
  "object-src 'none'",
  "frame-src 'none'",
  "base-uri 'none'"
].join("; ");

export function secureWebPreferences(
  preload: string
): NonNullable<BrowserWindowConstructorOptions["webPreferences"]> {
  return {
    preload,
    contextIsolation: true,
    sandbox: true,
    nodeIntegration: false,
    webSecurity: true,
    allowRunningInsecureContent: false
  };
}

export function isTrustedRenderer(url: string, developmentOrigin?: string): boolean {
  if (developmentOrigin) {
    try {
      const configured = new URL(developmentOrigin);
      const actual = new URL(url);
      const isNetworkOrigin = (value: URL) =>
        (value.protocol === "http:" || value.protocol === "https:") &&
        value.username === "" && value.password === "" && value.origin !== "null";
      if (isNetworkOrigin(configured) && isNetworkOrigin(actual) && actual.origin === configured.origin) return true;
    } catch {
      // Invalid development URLs never grant network access.
    }
  }
  return url.startsWith("file://") || url.startsWith("maris://app/");
}
