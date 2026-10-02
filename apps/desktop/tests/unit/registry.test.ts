import { describe, expect, it } from "vitest";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry, intersectModules } from "../../src/modules/registry";

const alternateContribution = {
  ...dailyFinanceContribution,
  moduleId: "alternate",
  routes: [{ routeId: "alternate_home", path: "/alternate" }],
  agentPanel: { profileId: "alternate.assistant@1", title: "Alternate" },
  settings: [{ key: "alternate_preferences", schemaVersion: 1 }],
  companion: { appearanceId: "alternate", label: "Alternate" }
};

function compileProfile(profileId: string) {
  return compileRegistry([{
    ...dailyFinanceContribution,
    agentPanel: { ...dailyFinanceContribution.agentPanel, profileId }
  }]);
}

describe("desktop module registry", () => {
  it("accepts the Python canonical Profile grammar and its length boundaries", () => {
    const name64 = `a${"b".repeat(63)}`;
    expect(() => compileProfile("daily_finance.assistant@1")).not.toThrow();
    expect(() => compileProfile("a.b@0")).not.toThrow();
    expect(() => compileProfile(`${name64}.${name64}@1`)).not.toThrow();
  });

  it.each([
    "daily_finance.assistant",
    "daily_finance.assistant@01",
    "daily_finance.assistant@-1",
    "daily_finance.assistant@1.0",
    "daily_finance.assistant@1@2",
    "daily-finance.assistant@1",
    "daily_finance.assistant-name@1",
    "daily_finance.assistant.extra@1",
    "Daily_finance.assistant@1",
    "daily_finance.Assistant@1",
    " daily_finance.assistant@1",
    "daily_finance.assistant@1 ",
    "daily_finance．assistant@1",
    "daily_finance.assistant＠1"
  ])("rejects non-canonical Profile %j", (profileId) => {
    expect(() => compileProfile(profileId)).toThrow();
  });

  it("rejects module and local names longer than 64 ASCII characters", () => {
    const name64 = `a${"b".repeat(63)}`;
    const name65 = `a${"b".repeat(64)}`;
    expect(() => compileProfile(`${name65}.b@1`)).toThrow();
    expect(() => compileProfile(`a.${name65}@1`)).toThrow();
    expect(() => compileProfile(`${name64}.${name64}@1`)).not.toThrow();
  });

  it("strictly intersects compatible Host modules", () => {
    const registry = compileRegistry([dailyFinanceContribution]);
    const supported = { module_id:"daily_finance", version:"1.2.3", enabled:true, profile_ids:["daily_finance.assistant@1"], api_prefixes:["/api/v1/finance"], settings_schema_version:1 };
    const legacyProfileId = ["daily_finance", "default"].join(".");
    expect(intersectModules(registry, [supported])).toEqual([dailyFinanceContribution]);
    expect(intersectModules(registry, [{ ...supported, profile_ids:[legacyProfileId] }])).toHaveLength(0);
    expect(intersectModules(registry, [{ ...supported, version:"2.0.0" }])).toHaveLength(0);
    expect(intersectModules(registry, [{ ...supported, api_prefixes:[] }])).toHaveLength(0);
    expect(intersectModules(registry, [{ ...supported, settings_schema_version:2 }])).toHaveLength(0);
  });

  it("rejects extra fields and every registry conflict without partial output", () => {
    expect(() => compileRegistry([{ ...dailyFinanceContribution, surprise:true }])).toThrow();
    const conflicts = [
      { ...alternateContribution, moduleId: dailyFinanceContribution.moduleId },
      { ...alternateContribution, agentPanel: dailyFinanceContribution.agentPanel },
      { ...alternateContribution, routes: dailyFinanceContribution.routes },
      { ...alternateContribution, companion: dailyFinanceContribution.companion }
    ];
    for (const conflict of conflicts) {
      expect(() => compileRegistry([dailyFinanceContribution, conflict])).toThrow("desktop_registry_conflict");
    }
    expect(() => compileRegistry([{
      ...alternateContribution,
      settings: [
        { key: "preferences", schemaVersion: 1 },
        { key: "preferences", schemaVersion: 1 }
      ]
    }])).toThrow("desktop_registry_conflict");
  });

  it.each([
    { schemaVersion: 1, reverse: false },
    { schemaVersion: 1, reverse: true },
    { schemaVersion: 2, reverse: false },
    { schemaVersion: 2, reverse: true }
  ])("rejects cross-module setting collisions regardless of version/order: %j", ({ schemaVersion, reverse }) => {
    const conflicting = {
      ...alternateContribution,
      settings: [{ key: dailyFinanceContribution.settings[0]!.key, schemaVersion }]
    };
    const values = reverse ? [conflicting, dailyFinanceContribution] : [dailyFinanceContribution, conflicting];
    expect(() => compileRegistry(values)).toThrow("desktop_registry_conflict");
  });

  it.each([1, 2])("rejects repeated keys within one module with schemaVersion %i", (schemaVersion) => {
    expect(() => compileRegistry([{
      ...alternateContribution,
      settings: [{ key: "virtual_shared", schemaVersion: 1 }, { key: "virtual_shared", schemaVersion }]
    }])).toThrow("desktop_registry_conflict");
  });

  it("accepts distinct global keys without changing daily finance or Host intersection", () => {
    const registry = compileRegistry([dailyFinanceContribution, alternateContribution]);
    expect(registry).toEqual([dailyFinanceContribution, alternateContribution]);
    expect(Object.isFrozen(registry)).toBe(true);
    expect(registry[0]!.settings).toEqual([{ key: "preferences", schemaVersion: 1 }]);
    expect(registry[0]!.agentPanel.profileId).toBe("daily_finance.assistant@1");
    expect(intersectModules(registry, [{
      module_id: "daily_finance", version: "1.0.0", enabled: true,
      profile_ids: ["daily_finance.assistant@1"], api_prefixes: ["/api/v1/finance"], settings_schema_version: 1
    }])).toEqual([dailyFinanceContribution]);
  });

  it("does not mutate input or retain seen state after a rejected compilation", () => {
    const valid = structuredClone([dailyFinanceContribution, alternateContribution]);
    const conflicting = [structuredClone(dailyFinanceContribution), {
      ...structuredClone(alternateContribution),
      settings: [{ key: "preferences", schemaVersion: 2 }]
    }];
    const before = structuredClone(conflicting);
    expect(() => compileRegistry(conflicting)).toThrow("desktop_registry_conflict");
    expect(conflicting).toEqual(before);
    const validBefore = structuredClone(valid);
    expect(compileRegistry(valid)).toEqual(validBefore);
    expect(valid).toEqual(validBefore);
  });
});
