// @vitest-environment jsdom
import { StrictMode, act } from "react";
import { appendFileSync } from "node:fs";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { DesktopCompositionRoot } from "../../electron/main/composition-root";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry } from "../../src/modules/registry";
import { DesktopApp, rendererRootOptions, type ModulePageLoaders } from "../../src/renderer/module-routes";
import type { HostModuleSummary, RuntimeSnapshot } from "../../src/shared/contracts";

const registry = compileRegistry([dailyFinanceContribution]);
const online: RuntimeSnapshot = { state: "online", mode: "managed", authenticated: true, errorCode: null };
const starting: RuntimeSnapshot = { ...online, state: "starting", authenticated: false };
const daily: HostModuleSummary = { module_id: "daily_finance", version: "1.0.0", display_name: "Virtual daily",
  enabled: true, profile_ids: ["daily_finance.assistant@1"], api_prefixes: ["/api/v1/finance"], settings_schema_version: 1 };
const Daily = () => <h1 id="daily-title">虚拟日常页面</h1>;
const canary = "VIRTUAL_READ_ERROR C:/virtual_private/token";
const healthyContribution = { ...dailyFinanceContribution, moduleId: "virtual_healthy",
  expectedApiPrefixes: ["/api/v1/virtual_healthy"], navigation: { label: "健康模块", order: 2 },
  routes: [{ routeId: "virtual_healthy_home", path: "/healthy" }],
  agentPanel: { profileId: "virtual_healthy.assistant@1", title: "Virtual" }, settings: [],
  companion: { appearanceId: "virtual_healthy", label: "Virtual" } };
const pairRegistry = compileRegistry([dailyFinanceContribution, healthyContribution]);
const healthy: HostModuleSummary = { ...daily, module_id: "virtual_healthy",
  profile_ids: ["virtual_healthy.assistant@1"], api_prefixes: ["/api/v1/virtual_healthy"] };
const Healthy = () => <h1>健康页面</h1>;
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function pageSample() {
  return { hash: ["#/", "#/daily", "#/settings", "#/healthy"].includes(location.hash) ? location.hash : "other",
    shell: !!document.querySelector("main.shell"), navigation: !!document.querySelector('nav[aria-label="模块导航"]'),
    agent: !!document.querySelector('aside[aria-label="统一 Agent 面板"]'),
    dailyNavigation: !!screen.queryByRole("link", { name: "日常财务" }), dailyPage: !!document.querySelector("#daily-title") };
}
function record(value: Record<string, unknown>) {
  const journal = process.env.MARIS_R6_TEST_JOURNAL;
  if (journal) appendFileSync(journal, JSON.stringify(value) + "\n");
}
let jsdomErrors: number;
let unhandled: number;
const onJsdomError = () => { jsdomErrors++; };
const onUnhandled = () => { unhandled++; };
const virtualConsole = (globalThis as unknown as { jsdom: { virtualConsole: {
  on(event: string, callback: () => void): void; removeListener(event: string, callback: () => void): void;
} } }).jsdom.virtualConsole;
beforeEach(() => {
  history.replaceState(null, "", "#/");
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  jsdomErrors = 0; unhandled = 0;
  vi.spyOn(console, "error").mockImplementation(() => {});
  vi.spyOn(console, "warn").mockImplementation(() => {});
  virtualConsole.on("jsdomError", onJsdomError);
  window.addEventListener("unhandledrejection", onUnhandled);
});
afterEach(() => {
  cleanup();
  const logged = JSON.stringify([vi.mocked(console.error).mock.calls, vi.mocked(console.warn).mock.calls]);
  record({ event: "cleanup_safety", jsdomErrors, unhandled, consoleCanary: logged.includes(canary) });
  virtualConsole.removeListener("jsdomError", onJsdomError);
  window.removeEventListener("unhandledrejection", onUnhandled);
  expect(jsdomErrors).toBe(0);
  expect(unhandled).toBe(0);
  expect(logged).not.toContain(canary);
  vi.restoreAllMocks(); vi.unstubAllGlobals();
});

function fixture(initial: readonly HostModuleSummary[] = [daily]) {
  const listeners = new Set<(value: RuntimeSnapshot) => void>();
  const trace: { event: string; category: string }[] = [];
  let current = initial;
  let activeReads = 0;
  let maxReads = 0;
  const pending: (() => Promise<readonly HostModuleSummary[]>)[] = [];
  const unsubscribe = vi.fn();
  const read = vi.fn(async () => {
    activeReads++; maxReads = Math.max(maxReads, activeReads);
    const operation = pending.shift();
    try {
      const value = operation ? await operation() : current;
      trace.push({ event: "modules_return", category: value.length ? "nonempty" : "empty" });
      return value;
    } catch (error) { trace.push({ event: "modules_return", category: "rejected" }); throw error; }
    finally { activeReads--; }
  });
  const bridge = {
    runtime: { getSnapshot: vi.fn(async (): Promise<RuntimeSnapshot> => online), recover: vi.fn(),
      subscribe: vi.fn((listener: (value: RuntimeSnapshot) => void) => {
        listeners.add(listener); return () => { listeners.delete(listener); unsubscribe(); };
      }) },
    modules: { list: read }, settings: { getSnapshot: async () => ({ theme: "system", reducedMotion: false, privacyMode: false }), update: vi.fn(async () => ({ accepted: true })) },
    outbox: { enqueue: vi.fn() }, external: { open: vi.fn() }, window: { perform: vi.fn() }
  };
  Object.defineProperty(window, "maris", { configurable: true, value: bridge });
  return { bridge, read, pending, trace, listeners, unsubscribe, maxReads: () => maxReads,
    setModules: (value: readonly HostModuleSummary[]) => { current = value; },
    emit: (value = online) => { trace.push({ event: "runtime", category: value.state + ":" + value.authenticated }); for (const listener of listeners) listener(value); } };
}
async function mount(strict = false, loaders: ModulePageLoaders = { daily_finance_home: async () => Daily }, modules = registry) {
  const app = <DesktopApp registry={modules} loaders={loaders} />;
  const rendered = render(strict ? <StrictMode>{app}</StrictMode> : app, rendererRootOptions);
  await act(async () => {});
  return rendered;
}

it.each([false, true])("automatically publishes the real page after initial empty modules and composition ready (StrictMode=%s)", async (strict) => {
  let backend = starting;
  let authenticated = false;
  let publishSupervisor = () => {};
  const connected = deferred<RuntimeSnapshot>();
  const hostModules = deferred<readonly HostModuleSummary[]>();
  const trace: { event: string; category: string }[] = [];
  const supervisor = { snapshot: () => backend, subscribe: (listener: () => void) => { publishSupervisor = listener; return () => {}; },
    start: () => connected.promise, recover: vi.fn(), shutdown: vi.fn() };
  const owner = { get safeState() { return authenticated ? "authenticated" : "empty"; },
    establish: async () => { authenticated = true; publishSupervisor(); return "authenticated"; },
    accessToken: () => "VIRTUAL_R6_OWNER_TOKEN", revoke: vi.fn() };
  const host = { setAccessToken: vi.fn(), modules: () => hostModules.promise };
  const root = new DesktopCompositionRoot(
    supervisor as unknown as ConstructorParameters<typeof DesktopCompositionRoot>[0],
    owner as unknown as ConstructorParameters<typeof DesktopCompositionRoot>[1],
    host as unknown as ConstructorParameters<typeof DesktopCompositionRoot>[2], registry);
  const readModules = vi.fn(async () => {
    const modules = root.modules();
    trace.push({ event: "modules_return", category: modules.length ? "enabled" : "empty" });
    return modules;
  });
  const recover = vi.fn();
  const subscribe = vi.fn((listener: (value: RuntimeSnapshot) => void) => root.subscribe((value) => {
    trace.push({ event: "runtime", category: value.state + (value.authenticated ? ":authenticated" : ":unauthenticated") });
    listener(value);
  }));
  Object.defineProperty(window, "maris", { configurable: true, value: {
    runtime: { getSnapshot: async () => root.snapshot(), subscribe, recover }, modules: { list: readModules },
    settings: { getSnapshot: async () => ({ theme: "system", reducedMotion: false, privacyMode: false }), update: vi.fn() }, outbox: { enqueue: vi.fn() }, external: { open: vi.fn() }, window: { perform: vi.fn() }
  } });
  const load = vi.fn(async () => Daily);
  const app = <DesktopApp registry={registry} loaders={{ daily_finance_home: load }} />;
  render(strict ? <StrictMode>{app}</StrictMode> : app, rendererRootOptions);
  await act(async () => {});
  const initial = pageSample();
  expect(readModules.mock.calls.length).toBeGreaterThanOrEqual(1);
  expect(trace.filter((row) => row.event === "modules_return").every((row) => row.category === "empty")).toBe(true);
  expect(initial).toMatchObject({ shell: true, agent: true, dailyNavigation: false, dailyPage: false });
  const flight = root.start();
  await act(async () => { backend = { ...online, authenticated: false }; connected.resolve(backend); });
  expect(root.snapshot()).toEqual(online);
  expect(root.modules()).toEqual([]);
  await act(async () => { hostModules.resolve([daily]); await flight; });
  const actual = pageSample();
  record({ event: "ready_sequence", strict, initial, backendEnabled: root.modules().length === 1,
    moduleCalls: readModules.mock.calls.length, loaderCalls: load.mock.calls.length, trace, expectedDailyPage: true, actual });
  expect(trace.filter((row) => row.event === "runtime").map((row) => row.category))
    .toEqual(["online:authenticated", "online:authenticated"]);
  expect(actual).toMatchObject({ shell: true, navigation: true, agent: true, dailyNavigation: true, dailyPage: true, hash: "#/daily" });
  expect(recover).not.toHaveBeenCalled();
  expect(owner.revoke).not.toHaveBeenCalled();
});

it.each([false, true])("shows an already ready module on mount (StrictMode=%s)", async (strict) => {
  const f = fixture();
  await mount(strict);
  expect(pageSample()).toMatchObject({ dailyPage: true, dailyNavigation: true, shell: true, agent: true });
  expect(f.bridge.runtime.recover).not.toHaveBeenCalled();
});

it.each([false, true])("keeps a subscription update when the initial runtime snapshot arrives late (StrictMode=%s)", async (strict) => {
  const f = fixture();
  const snapshot = deferred<RuntimeSnapshot>();
  f.bridge.runtime.getSnapshot.mockImplementation(() => snapshot.promise);
  await mount(strict);
  await act(async () => { f.emit(online); });
  await act(async () => { snapshot.resolve(starting); });
  expect(screen.getByRole("status").textContent).toContain("online");
  expect(pageSample().dailyPage).toBe(true);
  expect(f.listeners.size).toBe(1);
});

it("subscribes before snapshot or module calls, including a synchronous notification in getSnapshot", async () => {
  const f = fixture([]);
  f.bridge.runtime.getSnapshot.mockImplementation(async () => {
    expect(f.listeners.size).toBe(1);
    f.setModules([daily]); f.emit(); return starting;
  });
  await mount();
  expect(screen.getByRole("status").textContent).toContain("online");
  expect(pageSample().dailyPage).toBe(true);
  expect(f.read).toHaveBeenCalledTimes(1);
});

it("does not lose a ready notification raised during an initial module read", async () => {
  const f = fixture([daily]);
  f.pending.push(async () => { f.emit(); return []; });
  await mount();
  expect(f.read).toHaveBeenCalledTimes(2);
  expect(f.maxReads()).toBe(1);
  expect(pageSample().dailyPage).toBe(true);
});

it("coalesces a ready burst into one follow-up and discards the obsolete module result", async () => {
  const f = fixture([]);
  const old = deferred<readonly HostModuleSummary[]>();
  const latest = deferred<readonly HostModuleSummary[]>();
  f.pending.push(() => old.promise, () => latest.promise);
  await mount();
  await act(async () => { for (let i = 0; i < 20; i++) f.emit(); });
  expect(f.read).toHaveBeenCalledTimes(1);
  await act(async () => { old.resolve([daily]); });
  expect(f.read).toHaveBeenCalledTimes(2);
  expect(pageSample().dailyPage).toBe(false); // obsolete enabled data never commits.
  await act(async () => { latest.resolve([]); });
  expect(pageSample()).toMatchObject({ shell: true, dailyNavigation: false, dailyPage: false });
  expect(f.read).toHaveBeenCalledTimes(2);
  expect(f.maxReads()).toBe(1);
  record({ event: "coalesced", requests: f.read.mock.calls.length, maxReads: f.maxReads(), notifications: 20, actual: pageSample() });
});

it("ignores the disposed StrictMode effect's late module result", async () => {
  const f = fixture([daily]);
  const old = deferred<readonly HostModuleSummary[]>();
  f.pending.push(() => old.promise);
  await mount(true);
  expect(pageSample().dailyPage).toBe(true);
  const shell = document.querySelector("main.shell");
  await act(async () => { old.resolve([]); });
  expect(pageSample().dailyPage).toBe(true);
  expect(document.querySelector("main.shell")).toBe(shell);
  expect(f.unsubscribe).toHaveBeenCalledTimes(1);
  expect(f.listeners.size).toBe(1);
});

it.each([false, true])("ignores pending module/snapshot completion after unmount (reject=%s)", async (reject) => {
  const f = fixture([]);
  const pending = deferred<readonly HostModuleSummary[]>();
  const snapshot = deferred<RuntimeSnapshot>();
  f.pending.push(() => pending.promise);
  f.bridge.runtime.getSnapshot.mockImplementation(() => snapshot.promise);
  const rendered = await mount();
  await act(async () => { f.emit(); });
  rendered.unmount();
  await act(async () => {
    if (reject) { pending.reject(new Error(canary)); snapshot.reject(new Error(canary)); }
    else { pending.resolve([daily]); snapshot.resolve(online); }
    f.emit();
  });
  expect(f.read).toHaveBeenCalledTimes(1);
  expect(f.listeners.size).toBe(0);
  expect(f.unsubscribe).toHaveBeenCalledTimes(1);
  expect(document.querySelector("main.shell")).toBeNull();
});

it("handles initial and later read rejections safely without eventless retry", async () => {
  const f = fixture([daily]);
  f.pending.push(async () => { throw new Error(canary); });
  f.bridge.runtime.getSnapshot.mockRejectedValueOnce(new Error(canary));
  await mount();
  expect(pageSample()).toMatchObject({ shell: true, dailyPage: false });
  expect(f.read).toHaveBeenCalledTimes(1);
  await act(async () => { f.emit(); });
  expect(pageSample().dailyPage).toBe(true);
  const shell = document.querySelector("main.shell");
  f.pending.push(async () => { throw new Error(canary); });
  await act(async () => { f.emit(); });
  expect(f.read).toHaveBeenCalledTimes(3);
  expect(pageSample().dailyPage).toBe(true);
  expect(document.querySelector("main.shell")).toBe(shell);
  expect(document.body.textContent).not.toContain(canary);
});

it("keeps routes, theme, privacy and subscriptions for equal effective intersections and offline observations", async () => {
  const f = fixture([daily, healthy]);
  const user = userEvent.setup();
  const dailyLoader = vi.fn(async () => Daily);
  const healthyLoader = vi.fn(async () => Healthy);
  await mount(false, { daily_finance_home: dailyLoader, virtual_healthy_home: healthyLoader }, pairRegistry);
  const shell = document.querySelector("main.shell");
  await user.selectOptions(screen.getByLabelText("主题"), "dark");
  await user.click(screen.getByLabelText("隐私模式"));
  await user.click(screen.getByRole("link", { name: "健康模块" }));
  const healthyElement = screen.getByRole("heading", { name: "健康页面" });
  f.setModules([{ ...healthy }, { ...daily, version: "1.2.3" }, { ...daily, module_id: "unknown" }]);
  await act(async () => { f.emit(); f.emit(); });
  expect(screen.getByRole("heading", { name: "健康页面" })).toBe(healthyElement);
  expect(healthyLoader).toHaveBeenCalledTimes(1);
  expect(dailyLoader).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole("link", { name: "设置" }));
  await act(async () => { f.emit(); });
  expect(location.hash).toBe("#/settings");
  expect(document.querySelector("main.shell")).toBe(shell);
  const count = f.read.mock.calls.length;
  await act(async () => { f.emit({ ...online, state: "offline" }); });
  expect(f.read).toHaveBeenCalledTimes(count);
  expect(location.hash).toBe("#/settings");
  expect(shell?.getAttribute("data-theme")).toBe("dark");
  expect(shell?.getAttribute("data-privacy")).toBe("on");
  expect(screen.getByRole("status").textContent).toContain("offline");
  expect(f.bridge.runtime.subscribe).toHaveBeenCalledTimes(1);
  expect(f.unsubscribe).not.toHaveBeenCalled();
  expect(f.bridge.runtime.recover).not.toHaveBeenCalled();
  expect(f.bridge.outbox.enqueue).not.toHaveBeenCalled();
  expect(f.bridge.window.perform).not.toHaveBeenCalled();
  expect(f.bridge.external.open).not.toHaveBeenCalled();
  expect(f.bridge.settings.update.mock.calls).toEqual([[{ theme: "dark" }], [{ privacyMode: true }]]);
});

it.each([false, true])("does not automatically retry a failed page when ready notifications return equal modules (StrictMode=%s)", async (strict) => {
  const f = fixture();
  const load = vi.fn().mockRejectedValueOnce(new Error(canary)).mockResolvedValue(Daily);
  history.replaceState(null, "", "#/daily");
  await mount(strict, { daily_finance_home: load });
  expect(screen.getByRole("alert")).toBeTruthy();
  const shell = document.querySelector("main.shell");
  f.setModules([{ ...daily }]);
  await act(async () => { f.emit(); f.emit(); });
  expect(load).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("alert")).toBeTruthy();
  expect(document.querySelector("main.shell")).toBe(shell);
  await userEvent.click(screen.getByRole("button", { name: "重试" }));
  expect(pageSample().dailyPage).toBe(true);
  expect(load).toHaveBeenCalledTimes(2);
});

it("keeps ready empty/disabled/incompatible/unknown intersections empty and updates on a genuine change", async () => {
  const f = fixture([]);
  const load = vi.fn(async () => Daily);
  await mount(false, { daily_finance_home: load });
  for (const summaries of [[], [{ ...daily, enabled: false }], [{ ...daily, version: "2.0.0" }],
    [{ ...daily, module_id: "unknown" }], [{ ...daily, profile_ids: ["wrong.assistant@1"] }]]) {
    f.setModules(summaries);
    await act(async () => { f.emit(); });
    expect(pageSample()).toMatchObject({ shell: true, dailyPage: false, dailyNavigation: false });
    expect(load).not.toHaveBeenCalled();
  }
  f.setModules([daily]);
  await act(async () => { f.emit(); });
  expect(pageSample().dailyPage).toBe(true);
  expect(load).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole("link", { name: "设置" }));
  f.setModules([{ ...daily, enabled: false }]);
  await act(async () => { f.emit(); });
  expect(location.hash).toBe("#/settings");
  expect(pageSample().dailyNavigation).toBe(false);
  expect(load).toHaveBeenCalledTimes(1);
});

it("keeps the Shell available when the displayed module is removed from the intersection", async () => {
  const f = fixture([daily]);
  const load = vi.fn(async () => Daily);
  await mount(false, { daily_finance_home: load });
  expect(pageSample().dailyPage).toBe(true);
  f.setModules([]);
  await act(async () => { f.emit(); });
  record({ event: "displayed_module_removed", actual: pageSample() });
  expect(pageSample()).toMatchObject({ shell: true, navigation: true, agent: true, dailyNavigation: false, dailyPage: false });
  expect(load).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole("link", { name: "设置" }));
  expect(location.hash).toBe("#/settings");
});
