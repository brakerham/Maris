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
  if (developmentOrigin && url.startsWith(developmentOrigin)) return true;
  return url.startsWith("file://") || url.startsWith("maris://app/");
}
