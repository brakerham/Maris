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
});
