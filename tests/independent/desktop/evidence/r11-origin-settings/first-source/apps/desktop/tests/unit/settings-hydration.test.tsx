// @vitest-environment jsdom
import { StrictMode, act, useLayoutEffect } from "react";
import { appendFileSync } from "node:fs";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry } from "../../src/modules/registry";
import { DesktopApp, rendererRootOptions } from "../../src/renderer/module-routes";
import type { HostModuleSummary, RuntimeSnapshot, SettingsSnapshot } from "../../src/shared/contracts";

const registry = compileRegistry([dailyFinanceContribution]);
const online: RuntimeSnapshot = { state: "online", mode: "managed", authenticated: true, errorCode: null };
const daily: HostModuleSummary = { module_id: "daily_finance", version: "1.0.0", display_name: "Virtual daily",
  enabled: true, profile_ids: ["daily_finance.assistant@1"], api_prefixes: ["/api/v1/finance"], settings_schema_version: 1 };
const Daily = () => <h1 id="daily-title">虚拟日常页面</h1>;
const saved: SettingsSnapshot = { theme: "dark", privacyMode: true, reducedMotion: false };
const canary = "VIRTUAL_SETTINGS_CANARY C:/virtual_private/token";
let unhandled: number;
let jsdomErrors: number;
const onUnhandled = () => { unhandled++; };
const onJsdom = () => { jsdomErrors++; };
const virtualConsole = (globalThis as unknown as { jsdom: { virtualConsole: {
  on(event: string, callback: () => void): void; removeListener(event: string, callback: () => void): void;
} } }).jsdom.virtualConsole;
beforeEach(() => {
  history.replaceState(null, "", "#/");
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  vi.spyOn(console, "error").mockImplementation(() => {});
  vi.spyOn(console, "warn").mockImplementation(() => {});
  unhandled = 0; jsdomErrors = 0;
  window.addEventListener("unhandledrejection", onUnhandled);
  virtualConsole.on("jsdomError", onJsdom);
});
afterEach(() => {
  cleanup();
  expect(document.body.textContent).not.toContain(canary);
  expect(JSON.stringify([vi.mocked(console.error).mock.calls, vi.mocked(console.warn).mock.calls])).not.toContain(canary);
  expect(unhandled).toBe(0); expect(jsdomErrors).toBe(0);
  window.removeEventListener("unhandledrejection", onUnhandled);
  virtualConsole.removeListener("jsdomError", onJsdom);
  vi.restoreAllMocks(); vi.unstubAllGlobals();
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function fixture(read: () => Promise<unknown> = async () => saved, modules: readonly HostModuleSummary[] = [daily]) {
  const listeners = new Set<(value: RuntimeSnapshot) => void>();
  const emit = (value = online) => { for (const listener of listeners) listener(value); };
  const bridge = {
    runtime: { getSnapshot: vi.fn(async () => online), subscribe: vi.fn((listener: (value: RuntimeSnapshot) => void) => {
      listeners.add(listener); return () => { listeners.delete(listener); };
    }), recover: vi.fn(async () => { emit({ ...online, state: "recovering" }); emit(); return online; }) },
    modules: { list: vi.fn(async () => modules) },
    settings: { getSnapshot: vi.fn(read), update: vi.fn(async () => ({ accepted: true })) },
    outbox: { enqueue: vi.fn() }, external: { open: vi.fn() }, window: { perform: vi.fn() }
  };
  Object.defineProperty(window, "maris", { configurable: true, value: bridge });
  return { bridge, emit, listeners };
}
async function mount(strict = false, load = vi.fn(async () => Daily)) {
  const app = <DesktopApp registry={registry} loaders={{ daily_finance_home: load }} />;
  const view = render(strict ? <StrictMode>{app}</StrictMode> : app, rendererRootOptions);
  await act(async () => {});
  return { ...view, load };
}
function values() {
  const shell = document.querySelector<HTMLElement>("main.shell");
  return { theme: shell?.dataset.theme, privacy: shell?.dataset.privacy,
    themeControl: (screen.getByRole("combobox", { name: "主题" }) as HTMLSelectElement).value,
    privacyControl: (screen.getByRole("checkbox", { name: "隐私模式" }) as HTMLInputElement).checked };
}
function noWrites(bridge: ReturnType<typeof fixture>["bridge"]) {
  expect(bridge.settings.update).not.toHaveBeenCalled();
  expect(bridge.runtime.recover).not.toHaveBeenCalled();
  expect(bridge.outbox.enqueue).not.toHaveBeenCalled();
  expect(bridge.external.open).not.toHaveBeenCalled();
  expect(bridge.window.perform).not.toHaveBeenCalled();
}

it("restores persisted dark and privacy before showing the real Shell and module page", async () => {
  history.replaceState(null, "", "#/");
  const getSnapshot = vi.fn(async () => ({ theme: "dark", privacyMode: true, reducedMotion: false }));
  const update = vi.fn();
  Object.defineProperty(window, "maris", { configurable: true, value: {
    runtime: { getSnapshot: async () => online, subscribe: () => () => {}, recover: vi.fn() },
    modules: { list: async () => [daily] }, settings: { getSnapshot, update },
    outbox: { enqueue: vi.fn() }, external: { open: vi.fn() }, window: { perform: vi.fn() }
  } });
  render(<DesktopApp registry={registry} loaders={{ daily_finance_home: async () => Daily }} />, rendererRootOptions);
  await act(async () => {});
  expect(screen.getByRole("heading", { name: "虚拟日常页面" })).toBeTruthy();
  const shell = document.querySelector<HTMLElement>("main.shell")!;
  const sample = { shell: !!shell, daily: !!document.querySelector("#daily-title"),
    theme: shell.dataset.theme, privacy: shell.dataset.privacy,
    themeControl: (screen.getByRole("combobox", { name: "主题" }) as HTMLSelectElement).value,
    privacyControl: (screen.getByRole("checkbox", { name: "隐私模式" }) as HTMLInputElement).checked,
    reads: getSnapshot.mock.calls.length, writes: update.mock.calls.length };
  if (process.env.MARIS_R8_TEST_JOURNAL) appendFileSync(process.env.MARIS_R8_TEST_JOURNAL, JSON.stringify({ event: "first_real_page", sample }) + "\n");
  expect(sample).toMatchObject({ shell: true, daily: true, theme: "dark", privacy: "on", themeControl: "dark", privacyControl: true, writes: 0 });
});

it.each([
  [false, "dark", true], [true, "dark", true], [false, "light", false],
  [true, "high_contrast", true], [false, "system", false]
] as const)("hydrates before the first visible page (strict=%s theme=%s privacy=%s)", async (strict, theme, privacyMode) => {
  const f = fixture(async () => ({ theme, privacyMode, reducedMotion: true }));
  const firstPages: unknown[] = [];
  function Observed() { useLayoutEffect(() => { firstPages.push(values()); }, []); return <Daily />; }
  await mount(strict, vi.fn(async () => Observed));
  const expected = { theme, privacy: privacyMode ? "on" : "off", themeControl: theme, privacyControl: privacyMode };
  expect(firstPages.length).toBeGreaterThan(0);
  expect(firstPages.every((sample) => JSON.stringify(sample) === JSON.stringify(expected))).toBe(true);
  expect(values()).toEqual(expected); noWrites(f.bridge);
});

it.each([false, true])("holds content and controls until a valid delayed read (strict=%s)", async (strict) => {
  const gate = deferred<unknown>(); const f = fixture(() => gate.promise); const { load } = await mount(strict);
  expect(screen.getByRole("status").textContent).toBe("正在读取设备设置");
  expect(document.querySelector("main.shell")).toBeNull();
  expect(screen.queryByRole("combobox")).toBeNull(); expect(screen.queryByRole("checkbox")).toBeNull();
  expect(load).not.toHaveBeenCalled(); noWrites(f.bridge);
  await act(async () => { gate.resolve(saved); });
  expect(values()).toEqual({ theme: "dark", privacy: "on", themeControl: "dark", privacyControl: true });
  expect(screen.getByRole("heading", { name: "虚拟日常页面" })).toBeTruthy(); noWrites(f.bridge);
});

it.each([
  ["missing snapshot", undefined], ["null", null], ["missing theme", { privacyMode: true, reducedMotion: false }],
  ["missing privacy", { theme: "dark", reducedMotion: false }], ["missing motion", { theme: "dark", privacyMode: true }],
  ["wrong theme", { ...saved, theme: canary }], ["wrong privacy", { ...saved, privacyMode: "true" }],
  ["wrong motion", { ...saved, reducedMotion: 1 }], ["extra field", { ...saved, token: canary }]
])("fails safely without defaults, writes or automatic retry: %s", async (_name, value) => {
  const f = fixture(async () => value); const { load } = await mount();
  expect(screen.getByRole("alert").textContent).toBe("暂时无法读取设备设置，请稍后重新打开应用。");
  expect(document.querySelector("main.shell")).toBeNull(); expect(load).not.toHaveBeenCalled();
  expect(document.body.textContent).not.toContain(canary); noWrites(f.bridge);
  const reads = f.bridge.settings.getSnapshot.mock.calls.length;
  await act(async () => { f.emit(); f.emit(); });
  expect(f.bridge.settings.getSnapshot).toHaveBeenCalledTimes(reads); noWrites(f.bridge);
});

it.each(["rejection", "synchronous throw", "missing getter"])("contains %s and never publishes a default Shell", async (kind) => {
  const f = fixture(kind === "rejection" ? () => Promise.reject(new Error(canary)) : () => { throw new Error(canary); });
  if (kind === "missing getter") Reflect.deleteProperty(f.bridge.settings, "getSnapshot");
  const { load } = await mount();
  expect(screen.getByRole("alert")).toBeTruthy(); expect(document.body.textContent).not.toContain(canary);
  expect(document.querySelector("main.shell")).toBeNull(); expect(load).not.toHaveBeenCalled(); noWrites(f.bridge);
});

it("keeps empty modules separate from settings readiness and retains Agent and settings entry", async () => {
  const f = fixture(async () => saved, []); await mount();
  expect(screen.getByRole("heading", { name: "模块尚未连接" })).toBeTruthy();
  expect(screen.getByRole("complementary", { name: "统一 Agent 面板" })).toBeTruthy();
  await userEvent.click(screen.getByRole("link", { name: "设置" }));
  expect(screen.getByRole("heading", { name: "设置" })).toBeTruthy();
  expect(values().privacy).toBe("on"); noWrites(f.bridge);
});

it.each([false, true])("does not rehydrate or reload after user settings and equal notifications/recover (strict=%s)", async (strict) => {
  const f = fixture(); const { load } = await mount(strict);
  const before = load.mock.calls.length; const reads = f.bridge.settings.getSnapshot.mock.calls.length;
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "主题" }), "light");
  await userEvent.click(screen.getByRole("checkbox", { name: "隐私模式" }));
  expect(f.bridge.settings.update.mock.calls).toEqual([[{ theme: "light" }], [{ privacyMode: false }]]);
  await act(async () => { f.emit(); f.emit(); await f.bridge.runtime.recover(); });
  expect(values()).toEqual({ theme: "light", privacy: "off", themeControl: "light", privacyControl: false });
  expect(load.mock.calls.length - before).toBe(0);
  expect(f.bridge.settings.getSnapshot).toHaveBeenCalledTimes(reads);
  expect(f.bridge.settings.update).toHaveBeenCalledTimes(2);
});

it("ignores a stale StrictMode read arriving after a completed user choice", async () => {
  const stale = deferred<unknown>(); let reads = 0;
  const f = fixture(() => ++reads === 1 ? stale.promise : Promise.resolve(saved));
  const { load } = await mount(true); expect(reads).toBe(2);
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "主题" }), "high_contrast");
  const before = load.mock.calls.length;
  await act(async () => { stale.resolve({ theme: "light", privacyMode: false, reducedMotion: false }); });
  expect(values()).toEqual({ theme: "high_contrast", privacy: "on", themeControl: "high_contrast", privacyControl: true });
  expect(f.bridge.settings.update.mock.calls).toEqual([[{ theme: "high_contrast" }]]);
  expect(load.mock.calls.length - before).toBe(0);
});

it.each([false, true])("ignores stale resolve/reject after unmount and a fresh mount (reject=%s)", async (reject) => {
  const stale = deferred<unknown>(); const old = fixture(() => stale.promise); const view = await mount(); view.unmount();
  expect(old.listeners.size).toBe(0);
  const current = fixture(async () => ({ theme: "high_contrast", privacyMode: true, reducedMotion: true }));
  await mount();
  await act(async () => { if (reject) stale.reject(new Error(canary)); else stale.resolve({ theme: "light", privacyMode: false, reducedMotion: false }); });
  expect(values()).toEqual({ theme: "high_contrast", privacy: "on", themeControl: "high_contrast", privacyControl: true });
  noWrites(old.bridge); noWrites(current.bridge);
});

it("does not implicitly retry a failed lazy page on settings changes or recovery", async () => {
  const f = fixture(); const load = vi.fn(async () => { throw new Error(canary); }); await mount(false, load);
  expect(screen.getByRole("heading", { name: "页面暂时无法打开" })).toBeTruthy(); const before = load.mock.calls.length;
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "主题" }), "light");
  await act(async () => { f.emit(); await f.bridge.runtime.recover(); });
  expect(load.mock.calls.length - before).toBe(0);
  expect(screen.getByRole("heading", { name: "页面暂时无法打开" })).toBeTruthy();
  expect(values().theme).toBe("light");
  expect(f.bridge.settings.getSnapshot).toHaveBeenCalledTimes(1);
});
