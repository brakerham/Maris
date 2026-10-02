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
  it.each([false, true])("rejects cross-module identical paths with distinct route IDs (reverse=%s)", (reverse) => {
    const conflicting = { ...alternateContribution, routes: [{ routeId: "alternate_home", path: dailyFinanceContribution.routes[0]!.path }] };
    const values = reverse ? [conflicting, dailyFinanceContribution] : [dailyFinanceContribution, conflicting];
    expect(() => compileRegistry(values)).toThrow("desktop_registry_conflict");
  });

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

  it.each([false, true])("rejects identical paths within one module with distinct IDs (reverse=%s)", (reverse) => {
    const routes = [{ routeId: "virtual_first", path: "/virtual_shared" }, { routeId: "virtual_last", path: "/virtual_shared" }];
    expect(() => compileRegistry([{ ...alternateContribution, routes: reverse ? routes.toReversed() : routes }])).toThrow("desktop_registry_conflict");
  });

  it("rejects a path collision in the last route of the last module without output or mutation", () => {
    const third = { ...alternateContribution, moduleId: "third", agentPanel: { profileId: "third.assistant@1", title: "Third" },
      settings: [], companion: { appearanceId: "third", label: "Third" },
      routes: [{ routeId: "third_home", path: "/third" }, { routeId: "third_last", path: "/daily" }] };
    const values = structuredClone([dailyFinanceContribution, alternateContribution, third]);
    const before = structuredClone(values);
    let output: ReturnType<typeof compileRegistry> | undefined;
    expect(() => { output = compileRegistry(values); }).toThrow("desktop_registry_conflict");
    expect(output).toBeUndefined();
    expect(values).toEqual(before);
    expect(compileRegistry([dailyFinanceContribution, alternateContribution])).toEqual([dailyFinanceContribution, alternateContribution]);
  });

  it("continues to reject equal route IDs even when paths differ", () => {
    const conflicting = { ...alternateContribution, routes: [{ routeId: "daily_finance_home", path: "/different" }] };
    for (const values of [[dailyFinanceContribution, conflicting], [conflicting, dailyFinanceContribution]]) {
      expect(() => compileRegistry(values)).toThrow("desktop_registry_conflict");
    }
  });

  it("accepts distinct paths and keeps route ID and path namespaces separate", () => {
    const virtual = { ...alternateContribution, routes: [{ routeId: "alternate_home", path: "/route:daily_finance_home" },
      { routeId: "virtual_extra", path: "/module:daily_finance" }] };
    const values = [dailyFinanceContribution, virtual];
    expect(compileRegistry(values)).toEqual(values);
    expect(compileRegistry(values.toReversed())).toEqual(values.toReversed());
  });

  it("preserves input paths exactly without normalizing case or trailing slashes", () => {
    const virtual = { ...alternateContribution, routes: [{ routeId: "virtual_case", path: "/Daily" },
      { routeId: "virtual_slash", path: "/daily/" }] };
    expect(compileRegistry([dailyFinanceContribution, virtual])[1]!.routes).toEqual(virtual.routes);
  });

  it.each(["missing", "disabled"])("excludes %s Host modules from the compatible registry", (mode) => {
    const registry = compileRegistry([dailyFinanceContribution, alternateContribution]);
    const summary = { module_id: "daily_finance", version: "1.0.0", enabled: mode !== "disabled", profile_ids: ["daily_finance.assistant@1"],
      api_prefixes: ["/api/v1/finance"], settings_schema_version: 1 };
    expect(intersectModules(registry, mode === "missing" ? [] : [summary])).toEqual([]);
  });

  it.each(["module", "route", "setting", "appearance"])("strictly validates ASCII %s identifiers without normalization", (field) => {
    for (const id of ["Upper", "virtual-name", " virtual", "virtual ", "virtual\n", "虚拟", "ｖirtual", "", "a".repeat(65)]) {
      const value = { ...alternateContribution,
        ...(field === "module" ? { moduleId: id } : {}),
        ...(field === "route" ? { routes: [{ routeId: id, path: "/alternate" }] } : {}),
        ...(field === "setting" ? { settings: [{ key: id, schemaVersion: 1 }] } : {}),
        ...(field === "appearance" ? { companion: { appearanceId: id, label: "Virtual" } } : {}) };
      expect(() => compileRegistry([value])).toThrow();
    }
    expect(() => compileRegistry([{ ...alternateContribution, moduleId: "a".repeat(64) }])).not.toThrow();
  });

  it.each(["01.0.0", "1.01.0", "1.0.01", "1.0", "1.0.0-beta", " 1.0.0", "1.0.0\n", "１.0.0"])("rejects noncanonical SemVer %j", (version) => {
    expect(() => compileRegistry([{ ...alternateContribution, version }])).toThrow();
  });

  it.each([0, 2, "1"])("rejects incompatible or mistyped hostUiMajor %j", (hostUiMajor) => {
    expect(() => compileRegistry([{ ...alternateContribution, hostUiMajor }])).toThrow();
  });

  it("rejects undeclared nested contribution fields", () => {
    expect(() => compileRegistry([{ ...alternateContribution, routes: [{ ...alternateContribution.routes[0], surprise: true }] }])).toThrow();
  });
});
