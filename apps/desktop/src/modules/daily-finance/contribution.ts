import type { DesktopModuleContribution } from "../registry";

export const dailyFinanceContribution = {
  moduleId: "daily_finance",
  version: "1.0.0",
  hostUiMajor: 1,
  expectedApiPrefixes: ["/api/v1/finance"],
  navigation: { label: "日常财务", order: 10 },
  routes: [{ routeId: "daily_finance_home", path: "/daily" }],
  agentPanel: { profileId: "daily_finance.default", title: "毛毛 · 日常管钱" },
  settings: [{ key: "preferences", schemaVersion: 1 }],
  companion: { appearanceId: "daily_finance", label: "日常管钱" }
} as const satisfies DesktopModuleContribution;
