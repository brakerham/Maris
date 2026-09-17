import {
  DEFAULT_BACKEND_BASE_URL,
  DEFAULT_TIMEOUT_MS,
  type FinanceProbeClientOptions,
} from "./client.js";
import { FinanceProbeError } from "./errors.js";

export type FinanceProbePluginConfig = {
  backendBaseUrl: string;
  timeoutMs: number;
};

export function resolvePluginConfig(value: unknown): FinanceProbePluginConfig {
  if (value === undefined) {
    return {
      backendBaseUrl: DEFAULT_BACKEND_BASE_URL,
      timeoutMs: DEFAULT_TIMEOUT_MS,
    };
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new FinanceProbeError("invalid_request");
  }
  const raw = value as Record<string, unknown>;
  const allowedKeys = new Set(["backendBaseUrl", "timeoutMs"]);
  if (Object.keys(raw).some((key) => !allowedKeys.has(key))) {
    throw new FinanceProbeError("invalid_request");
  }
  const backendBaseUrl = raw.backendBaseUrl ?? DEFAULT_BACKEND_BASE_URL;
  const timeoutMs = raw.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  if (typeof backendBaseUrl !== "string" || typeof timeoutMs !== "number") {
    throw new FinanceProbeError("invalid_request");
  }
  return { backendBaseUrl, timeoutMs };
}

export function toClientOptions(
  config: FinanceProbePluginConfig,
): Pick<FinanceProbeClientOptions, "baseUrl" | "timeoutMs"> {
  return {
    baseUrl: config.backendBaseUrl,
    timeoutMs: config.timeoutMs,
  };
}
