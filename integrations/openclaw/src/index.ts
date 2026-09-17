import { randomUUID } from "node:crypto";

import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "typebox";

import {
  FinanceProbeClient,
  type FinanceProbeClientOptions,
  type ProbeResponse,
} from "./client.js";
import { resolvePluginConfig, toClientOptions } from "./config.js";
import {
  asFinanceProbeError,
  FINANCE_PROBE_ERROR_CODES,
  formatSafeError,
  toErrorDetails,
} from "./errors.js";

export type FinanceProbeClientPort = Pick<FinanceProbeClient, "createProbe" | "health">;

export type FinanceProbePluginDependencies = {
  clientFactory?: (options: FinanceProbeClientOptions) => FinanceProbeClientPort;
  invocationIdFactory?: () => string;
};

const probeResponseSchema = Type.Object(
  {
    request_id: Type.String(),
    challenge: Type.String(),
    receipt: Type.String(),
    created_at: Type.String(),
    replayed: Type.Boolean(),
  },
  { additionalProperties: false },
);

const probeErrorSchema = Type.Object(
  {
    error: Type.Object(
      {
        code: Type.Union(FINANCE_PROBE_ERROR_CODES.map((code) => Type.Literal(code))),
        message: Type.String(),
        retryable: Type.Boolean(),
      },
      { additionalProperties: false },
    ),
  },
  { additionalProperties: false },
);

function formatProbe(result: ProbeResponse): string {
  return [
    `request_id: ${result.request_id}`,
    `receipt: ${result.receipt}`,
    `created_at: ${result.created_at}`,
    `replayed: ${String(result.replayed)}`,
  ].join("\n");
}

export function registerFinanceProbePlugin(
  api: OpenClawPluginApi,
  dependencies: FinanceProbePluginDependencies = {},
): void {
  const config = resolvePluginConfig(api.pluginConfig);
  const clientFactory =
    dependencies.clientFactory ??
    ((options: FinanceProbeClientOptions): FinanceProbeClientPort => new FinanceProbeClient(options));
  const client = clientFactory({ ...toClientOptions(config), logger: api.logger });
  const invocationIdFactory = dependencies.invocationIdFactory ?? randomUUID;

  api.registerCommand({
    name: "finance-probe",
    description: "Call the local wife-system finance probe without invoking the model.",
    acceptsArgs: true,
    requireAuth: true,
    handler: async (context) => {
      const invocationKey = invocationIdFactory();
      const challenge = context.args?.trim() ?? "";
      try {
        const result = await client.createProbe(challenge, invocationKey);
        return { text: formatProbe(result) };
      } catch (error) {
        return { text: formatSafeError(asFinanceProbeError(error)), isError: true };
      }
    },
  });

  api.registerTool({
    name: "finance_probe",
    label: "Finance Probe",
    description: "Call the local wife-system probe and return its backend-generated receipt.",
    parameters: Type.Object(
      {
        challenge: Type.String({ minLength: 1, maxLength: 128 }),
      },
      { additionalProperties: false },
    ),
    outputSchema: Type.Union([probeResponseSchema, probeErrorSchema]),
    async execute(toolCallId, params, signal) {
      try {
        const challenge = (params as { challenge: string }).challenge;
        const result = await client.createProbe(challenge, toolCallId, signal);
        return {
          content: [{ type: "text", text: formatProbe(result) }],
          details: result,
        };
      } catch (error) {
        const safeError = asFinanceProbeError(error);
        return {
          content: [{ type: "text", text: formatSafeError(safeError) }],
          details: toErrorDetails(safeError),
          isError: true,
        };
      }
    },
  });
}

export default definePluginEntry({
  id: "wife-system-finance-probe",
  name: "Wife System Finance Probe",
  description: "Forwards probe requests to the local wife-system service.",
  register(api) {
    registerFinanceProbePlugin(api);
  },
});

export { FinanceProbeClient } from "./client.js";
export type { FinanceProbeClientOptions, ProbeHealth, ProbeResponse } from "./client.js";
export {
  FinanceProbeError,
  type FinanceProbeErrorCode,
  type FinanceProbeErrorDetails,
} from "./errors.js";
