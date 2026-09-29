import { describe, expect, it } from "vitest";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry, intersectModules } from "../../src/modules/registry";

describe("desktop module registry", () => {
  it("strictly parses and intersects compatible Host modules", () => {
    const registry = compileRegistry([dailyFinanceContribution]);
    const supported = { module_id:"daily_finance", version:"1.2.3", enabled:true, profile_ids:["daily_finance.assistant@1"], api_prefixes:["/api/v1/finance"], settings_schema_version:1 };
    const legacyProfileId = ["daily_finance", "default"].join(".");
    expect(intersectModules(registry, [supported])).toEqual([dailyFinanceContribution]);
    expect(intersectModules(registry, [{ ...supported, profile_ids:[legacyProfileId] }])).toHaveLength(0);
    expect(intersectModules(registry, [{ ...supported, version:"2.0.0" }])).toHaveLength(0);
  });
  it("rejects extra fields and global conflicts without partial output", () => {
    expect(() => compileRegistry([{ ...dailyFinanceContribution, surprise:true }])).toThrow();
    expect(() => compileRegistry([dailyFinanceContribution, dailyFinanceContribution])).toThrow("desktop_registry_conflict");
  });
});
