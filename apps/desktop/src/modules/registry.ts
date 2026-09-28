import { z } from "zod";

const asciiId = /^[a-z][a-z0-9_]{0,63}$/;
const profileId = /^[a-z][a-z0-9_.-]{0,139}$/;
const semver = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const apiPrefix = /^\/api\/v1\/[a-z][a-z0-9_/-]*$/;

export const moduleContributionSchema = z.strictObject({
  moduleId: z.string().regex(asciiId),
  version: z.string().regex(semver),
  hostUiMajor: z.literal(1),
  expectedApiPrefixes: z.array(z.string().regex(apiPrefix)).min(1).readonly(),
  navigation: z.strictObject({ label: z.string().min(1).max(48), order: z.number().int() }),
  routes: z.array(z.strictObject({ routeId: z.string().regex(asciiId), path: z.string().startsWith("/") })).min(1).readonly(),
  agentPanel: z.strictObject({ profileId: z.string().regex(profileId), title: z.string().min(1).max(64) }),
  settings: z.array(z.strictObject({ key: z.string().regex(asciiId), schemaVersion: z.number().int().positive() })).readonly(),
  companion: z.strictObject({ appearanceId: z.string().regex(asciiId), label: z.string().min(1).max(48) })
});

export type DesktopModuleContribution = z.infer<typeof moduleContributionSchema>;

export type HostModuleSummary = Readonly<{
  module_id: string;
  version: string;
  enabled: boolean;
  profile_ids: readonly string[];
  api_prefixes: readonly string[];
  settings_schema_version: number;
}>;

export function compileRegistry(values: readonly unknown[]): readonly DesktopModuleContribution[] {
  const parsed = values.map((value) => moduleContributionSchema.parse(value));
  const seen = new Set<string>();
  for (const item of parsed) {
    const keys = [
      `module:${item.moduleId}`,
      `profile:${item.agentPanel.profileId}`,
      `appearance:${item.companion.appearanceId}`,
      ...item.routes.map((route) => `route:${route.routeId}`),
      ...item.settings.map((setting) => `setting:${item.moduleId}:${setting.key}`)
    ];
    for (const key of keys) {
      if (seen.has(key)) throw new Error("desktop_registry_conflict");
      seen.add(key);
    }
  }
  return Object.freeze(parsed);
}

export function intersectModules(
  registry: readonly DesktopModuleContribution[],
  host: readonly HostModuleSummary[]
): readonly DesktopModuleContribution[] {
  const hostById = new Map(host.map((summary) => [summary.module_id, summary]));
  return registry.filter((contribution) => {
    const summary = hostById.get(contribution.moduleId);
    if (!summary?.enabled) return false;
    if (summary.version.split(".")[0] !== contribution.version.split(".")[0]) return false;
    if (!summary.profile_ids.includes(contribution.agentPanel.profileId)) return false;
    if (!contribution.expectedApiPrefixes.every((prefix) => summary.api_prefixes.includes(prefix))) return false;
    return contribution.settings.every((setting) => setting.schemaVersion === summary.settings_schema_version);
  });
}
