import { describe, expect, it } from "vitest";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry, intersectModules } from "../../src/modules/registry";

describe("desktop module registry", () => {
  it("strictly parses and intersects compatible Host modules", () => {
    const registry = compileRegistry([dailyFinanceContribution]);
    expect(intersectModules(registry, [{ module_id:"daily_finance", version:"1.2.3", enabled:true, profile_ids:["daily_finance.default"], api_prefixes:["/api/v1/finance"], settings_schema_version:1 }])).toHaveLength(1);
    expect(intersectModules(registry, [{ module_id:"daily_finance", version:"2.0.0", enabled:true, profile_ids:["daily_finance.default"], api_prefixes:["/api/v1/finance"], settings_schema_version:1 }])).toHaveLength(0);
  });
  it("rejects extra fields and global conflicts without partial output", () => {
    expect(() => compileRegistry([{ ...dailyFinanceContribution, surprise:true }])).toThrow();
    expect(() => compileRegistry([dailyFinanceContribution, dailyFinanceContribution])).toThrow("desktop_registry_conflict");
  });
});
