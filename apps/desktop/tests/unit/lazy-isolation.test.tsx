// @vitest-environment jsdom
import { act } from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry, type HostModuleSummary } from "../../src/modules/registry";
import { DesktopApp, rendererRootOptions, type ModulePageLoaders } from "../../src/renderer/module-routes";
import type { RuntimeSnapshot } from "../../src/shared/contracts";

const canary = "VIRTUAL_TOKEN_CANARY C:/virtual_private/chunk.js";
const online: RuntimeSnapshot = { state: "online", mode: "managed", authenticated: true, errorCode: null };
const healthyContribution = { ...dailyFinanceContribution, moduleId: "virtual_healthy",
  expectedApiPrefixes: ["/api/v1/virtual_healthy"], navigation: { label: "健康模块", order: 2 },
  routes: [{ routeId: "virtual_healthy_home", path: "/healthy" }],
  agentPanel: { profileId: "virtual_healthy.assistant@1", title: "Virtual" }, settings: [],
  companion: { appearanceId: "virtual_healthy", label: "Virtual" } };
const registry = compileRegistry([dailyFinanceContribution, healthyContribution]);
const summaries: readonly HostModuleSummary[] = registry.map((item) => ({ module_id: item.moduleId, version: item.version,
  enabled: true, profile_ids: [item.agentPanel.profileId], api_prefixes: item.expectedApiPrefixes, settings_schema_version: 1 }));
const HealthyPage = () => <h1>健康模块页面</h1>;
const RecoveredPage = () => <h1>模块已恢复</h1>;

function bridgeFixture(host: readonly HostModuleSummary[] = summaries) {
  const subscribers = new Set<(value: RuntimeSnapshot) => void>();
  const unsubscribe = vi.fn();
  const bridge = {
    runtime: { getSnapshot: vi.fn(async () => online), recover: vi.fn(), subscribe: vi.fn((listener: (value: RuntimeSnapshot) => void) => {
      subscribers.add(listener); return () => { subscribers.delete(listener); unsubscribe(); };
    }) },
    modules: { list: vi.fn(async () => host) }, settings: { getSnapshot: async () => ({ theme: "system", reducedMotion: false, privacyMode: false }), update: vi.fn(async () => ({ ok: true })) },
    outbox: { enqueue: vi.fn() }, external: { open: vi.fn() }, window: { perform: vi.fn() }
  };
  Object.defineProperty(window, "maris", { configurable: true, value: bridge });
  return { bridge, subscribers, unsubscribe, emit: (value: RuntimeSnapshot) => { for (const listener of subscribers) listener(value); } };
}

type VirtualConsolePort = { on(event: string, listener: (error: Error) => void): void; removeListener(event: string, listener: (error: Error) => void): void };
let jsdomErrors: string[];
let onJsdomError: (error: Error) => void;
let virtualConsole: VirtualConsolePort;

beforeEach(() => {
  window.history.replaceState(null, "", "#/");
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  vi.spyOn(console, "error").mockImplementation(() => {});
  vi.spyOn(console, "warn").mockImplementation(() => {});
  jsdomErrors = [];
  virtualConsole = (globalThis as unknown as { jsdom: { virtualConsole: VirtualConsolePort } }).jsdom.virtualConsole;
  onJsdomError = (error) => { jsdomErrors.push(error.message); };
  virtualConsole.on("jsdomError", onJsdomError);
});

afterEach(() => {
  cleanup();
  expect(jsdomErrors).toEqual([]); // jsdom emits an error if location.reload/navigation is attempted.
  const records = JSON.stringify([vi.mocked(console.error).mock.calls, vi.mocked(console.warn).mock.calls]);
  expect(records).not.toContain(canary);
  expect(records).not.toContain("virtual_private");
  virtualConsole.removeListener("jsdomError", onJsdomError);
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function mount(loaders: ModulePageLoaders, host = summaries) {
  const fixture = bridgeFixture(host);
  render(<DesktopApp registry={registry} loaders={loaders} />, rendererRootOptions);
  return fixture;
}

function expectShell() {
  const shell = document.querySelector("main.shell");
  expect(shell).not.toBeNull();
  expect(screen.getByRole("navigation", { name: "模块导航" })).toBeTruthy();
  expect(screen.getByRole("complementary", { name: "统一 Agent 面板" })).toBeTruthy();
  return shell!;
}

describe("real desktop module routing with only virtual bridge/page ports", () => {
  it("recovers a transient import via one explicit loader retry while preserving Shell state and subscriptions", async () => {
    const user = userEvent.setup();
    const failed = vi.fn().mockRejectedValueOnce(new Error(canary)).mockResolvedValue(RecoveredPage);
    const healthy = vi.fn(async () => HealthyPage);
    const fixture = mount({ daily_finance_home: failed, virtual_healthy_home: healthy });
    expect(await screen.findByRole("alert")).toHaveProperty("textContent", expect.stringContaining("页面暂时无法打开"));
    const shell = expectShell();
    expect(failed).toHaveBeenCalledTimes(1);
    await user.selectOptions(screen.getByLabelText("主题"), "dark");
    await user.click(screen.getByLabelText("隐私模式"));
    await act(async () => { fixture.emit({ ...online, state: "offline" }); });
    expect(screen.getByRole("status").textContent).toContain("offline");
    expect(failed).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(await screen.findByRole("heading", { name: "模块已恢复" })).toBeTruthy();
    expect(failed).toHaveBeenCalledTimes(2);
    expect(healthy).not.toHaveBeenCalled();
    expect(expectShell()).toBe(shell);
    expect(shell.getAttribute("data-theme")).toBe("dark");
    expect(shell.getAttribute("data-privacy")).toBe("on");
    expect(screen.getByRole("status").textContent).toContain("offline");
    expect(fixture.bridge.settings.update.mock.calls).toEqual([[{ theme: "dark" }], [{ privacyMode: true }]]);
    expect(fixture.bridge.runtime.getSnapshot).toHaveBeenCalledTimes(1);
    expect(fixture.bridge.runtime.subscribe).toHaveBeenCalledTimes(1);
    expect(fixture.bridge.modules.list).toHaveBeenCalledTimes(1);
    expect(fixture.unsubscribe).not.toHaveBeenCalled();
    expect(fixture.bridge.runtime.recover).not.toHaveBeenCalled();
    expect(fixture.bridge.outbox.enqueue).not.toHaveBeenCalled();
    expect(fixture.bridge.window.perform).not.toHaveBeenCalled();
    expect(fixture.bridge.external.open).not.toHaveBeenCalled();
    cleanup();
    expect(fixture.unsubscribe).toHaveBeenCalledTimes(1);
    expect(fixture.subscribers.size).toBe(0);
  });

  it("keeps persistent failures local without looping and permits healthy/settings navigation and return", async () => {
    const user = userEvent.setup();
    const failed = vi.fn(async () => { throw new Error(canary); });
    const healthy = vi.fn(async () => HealthyPage);
    mount({ daily_finance_home: failed, virtual_healthy_home: healthy });
    await screen.findByRole("alert");
    const shell = expectShell();
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 50)); });
    expect(failed).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "重试" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "重试" })).toHaveProperty("disabled", false));
    expect(failed).toHaveBeenCalledTimes(2);
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 50)); });
    expect(failed).toHaveBeenCalledTimes(2);
    await user.click(screen.getByRole("link", { name: "健康模块" }));
    await screen.findByRole("heading", { name: "健康模块页面" });
    expect(healthy).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alert")).toBeNull();
    await user.click(screen.getByRole("link", { name: "设置" }));
    await screen.findByRole("heading", { name: "设置" });
    await user.click(screen.getByRole("link", { name: "日常财务" }));
    await screen.findByRole("alert");
    expect(failed).toHaveBeenCalledTimes(3); // user navigation is another explicit attempt.
    expect(expectShell()).toBe(shell);
    await user.click(screen.getByRole("link", { name: "健康模块" }));
    await screen.findByRole("heading", { name: "健康模块页面" });
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.body.textContent).not.toContain(canary);
  });

  it("bounds pending retry to one loader call even with repeated clicks and can leave the failing route", async () => {
    const user = userEvent.setup();
    let finish!: (page: typeof RecoveredPage) => void;
    const failed = vi.fn().mockRejectedValueOnce(new Error(canary)).mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
    const fixture = mount({ daily_finance_home: failed, virtual_healthy_home: async () => HealthyPage });
    await screen.findByRole("alert");
    await user.click(screen.getByRole("button", { name: "重试" }));
    const pending = await screen.findByRole("button", { name: "正在重试" });
    expect(pending).toHaveProperty("disabled", true);
    await user.dblClick(pending);
    expect(failed).toHaveBeenCalledTimes(2);
    await user.click(screen.getByRole("link", { name: "健康模块" }));
    await screen.findByRole("heading", { name: "健康模块页面" });
    await act(async () => { finish(RecoveredPage); });
    expect(screen.getByRole("heading", { name: "健康模块页面" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "模块已恢复" })).toBeNull();
    expect(fixture.bridge.runtime.recover).not.toHaveBeenCalled();
  });

  it("isolates a module render error and retries its real loader to reset the local boundary", async () => {
    const user = userEvent.setup();
    const BrokenPage = () => { throw new Error(canary); };
    const load = vi.fn().mockResolvedValueOnce(BrokenPage).mockResolvedValue(RecoveredPage);
    mount({ daily_finance_home: load, virtual_healthy_home: async () => HealthyPage });
    await screen.findByRole("alert");
    expectShell();
    expect(document.body.textContent).not.toContain(canary);
    expect(vi.mocked(console.error).mock.calls).toEqual([["desktop_render_unavailable"]]);
    await user.click(screen.getByRole("button", { name: "重试" }));
    await screen.findByRole("heading", { name: "模块已恢复" });
    expect(load).toHaveBeenCalledTimes(2);
    expectShell();
  });

  it("keeps the empty Host intersection and settings available without calling a page loader", async () => {
    const load = vi.fn(async () => RecoveredPage);
    mount({ daily_finance_home: load }, []);
    await screen.findByRole("heading", { name: "模块尚未连接" });
    expectShell();
    expect(screen.queryByRole("link", { name: "日常财务" })).toBeNull();
    expect(load).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("link", { name: "设置" }));
    await screen.findByRole("heading", { name: "设置" });
  });

  it("does not load a disabled module even when its contribution and page port exist", async () => {
    const healthy = vi.fn(async () => HealthyPage);
    mount({ daily_finance_home: async () => RecoveredPage, virtual_healthy_home: healthy },
      summaries.map((summary) => ({ ...summary, enabled: summary.module_id !== "virtual_healthy" })));
    await screen.findByRole("heading", { name: "模块已恢复" });
    expect(screen.queryByRole("link", { name: "健康模块" })).toBeNull();
    expect(healthy).not.toHaveBeenCalled();
  });

  it("fails closed for an unregistered trusted page port without importing a renderer-supplied path", async () => {
    mount({ virtual_healthy_home: async () => HealthyPage });
    await screen.findByRole("alert");
    expectShell();
    await userEvent.click(screen.getByRole("link", { name: "健康模块" }));
    await screen.findByRole("heading", { name: "健康模块页面" });
  });

  it("keeps the actual production entry and builtin daily page success path working", async () => {
    document.body.innerHTML = '<div id="root"></div>';
    const fixture = bridgeFixture([summaries[0]!]);
    let root: Awaited<typeof import("../../src/renderer/main")>["desktopRoot"] | undefined;
    try {
      await act(async () => { root = (await import("../../src/renderer/main")).desktopRoot; });
      await screen.findByRole("heading", { name: "日常财务" });
      expectShell();
      expect(screen.queryByRole("alert")).toBeNull();
      expect(fixture.bridge.runtime.recover).not.toHaveBeenCalled();
      expect(fixture.bridge.outbox.enqueue).not.toHaveBeenCalled();
    } finally { await act(async () => { root?.unmount(); }); }
  });
});
