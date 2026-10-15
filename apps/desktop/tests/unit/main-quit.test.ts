import { EventEmitter } from "node:events";
import { appendFileSync } from "node:fs";
import { afterEach, expect, it, vi } from "vitest";
import { defaultSettings, deviceSettingsSchema, type DeviceSettings } from "../../electron/main/device-settings";

function deferred<T>() {
  let resolve!: (value: T) => void; let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
const flush = async () => { for (let i = 0; i < 60; i++) await Promise.resolve(); };
const event = () => ({ defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } });
function record(value: Record<string, unknown>) {
  if (process.env.MARIS_R7_TEST_JOURNAL) appendFileSync(process.env.MARIS_R7_TEST_JOURNAL, JSON.stringify(value) + "\n");
}
const mocked = ["device-settings", "outbox", "managed-host-port", "backend-supervisor", "owner-session", "owner-auth-client", "owner-secret-store", "host-client"];
afterEach(() => {
  vi.doUnmock("electron");
  for (const name of mocked) vi.doUnmock(`../../electron/main/${name}`);
  vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs();
});

async function fixture(overrides: Partial<DeviceSettings> = {}, ready = true) {
  vi.resetModules();
  vi.doUnmock("../../electron/main/composition-root");
  vi.doUnmock("../../electron/main/window-lifecycle");
  vi.doUnmock("../../electron/main/outbox-retention");
  vi.stubEnv("MARIS_E2E", ""); vi.stubEnv("MARIS_E2E_EXIT_MS", "");
  vi.stubEnv("MARIS_EXTERNAL_HOST_URL", ""); vi.stubEnv("MARIS_EXTERNAL_HOST_NONCE", "");
  for (const name of ["MAIN_WINDOW", "COMPANION_WINDOW"]) {
    vi.stubGlobal(`${name}_VITE_DEV_SERVER_URL`, ""); vi.stubGlobal(`${name}_VITE_NAME`, name.toLowerCase());
  }
  const trace: string[] = [];
  const stop = deferred<void>();
  const stopEntered = deferred<void>();
  const saveGate = deferred<void>();
  let holdSave = false;
  let persisted = { ...defaultSettings, closePolicy: "quit" as const, closeHintShown: false, companionVisible: true, ...overrides };
  const save = vi.fn(async (value: DeviceSettings) => { trace.push("settings_flush"); if (holdSave) await saveGate.promise; persisted = { ...value }; });
  const cleanup = vi.fn(async () => { trace.push("outbox_flush"); });
  const deleteConfirmed = vi.fn(async () => 1);
  const candidates = vi.fn(async (): Promise<readonly object[]> => []);
  const recover = vi.fn(); const revoke = vi.fn(); const establish = vi.fn(async () => "authenticated");
  const backendStart = vi.fn(async () => ({ state: "online", mode: "managed", authenticated: false, errorCode: null }));
  const backendStop = vi.fn(async () => { trace.push("owned_stop_enter"); stopEntered.resolve(); await stop.promise; trace.push("owned_stop_done"); });
  class Supervisor {
    snapshot = () => ({ state: "online", mode: "managed", authenticated: false, errorCode: null });
    subscribe = vi.fn(); start = backendStart; shutdown = backendStop; recover = recover;
  }
  class Owner { safeState = "authenticated"; establish = establish; accessToken = () => "VIRTUAL_R7_TOKEN"; revoke = revoke; refresh = vi.fn(); }
  class Host {
    setAccessToken = vi.fn();
    modules = async () => [{ module_id: "daily_finance", version: "1.0.0", enabled: true,
      profile_ids: ["daily_finance.assistant@1"], api_prefixes: ["/api/v1/finance"], settings_schema_version: 1 }];
  }
  class Settings { load = async () => ({ ...persisted }); save = save; }
  class Box { load = async () => {}; cleanup = cleanup; retentionCandidates = candidates; deleteConfirmed = deleteConfirmed; }
  class Noop { constructor(..._args: unknown[]) {} }
  const app = new EventEmitter() as EventEmitter & Record<string, any>;
  const live = new Set<Window>(); const windows: Window[] = [];
  let finalExits = 0; let quitDepth = 0; let allClosed = 0; let closeReceived = 0;
  class Window extends EventEmitter {
    destroyed = false; visible = false; destroys = 0;
    webContents = { setWindowOpenHandler: vi.fn(), on: vi.fn(), send: vi.fn() };
    show = vi.fn(() => { this.visible = true; }); hide = vi.fn(() => { if (this.destroyed) throw Error("destroyed_hide"); this.visible = false; });
    focus = vi.fn(); setAlwaysOnTop = vi.fn(); loadFile = vi.fn(async () => {}); loadURL = vi.fn(async () => {});
    constructor(readonly options: { title: string }) { super(); windows.push(this); live.add(this); }
    isDestroyed() { return this.destroyed; }
    isVisible() { return this.visible; }
    close() { closeReceived++; trace.push("close_received:" + this.options.title); const e = event(); this.emit("close", e); if (!e.defaultPrevented && !this.destroyed) this.destroy(); return e; }
    destroy() {
      if (this.destroyed) throw Error("double_destroy");
      this.destroys++; this.destroyed = true; live.delete(this); trace.push("destroy:" + this.options.title); this.emit("closed");
      if (live.size === 0) { allClosed++; trace.push("window_all_closed"); app.emit("window-all-closed"); }
    }
  }
  const quit = vi.fn(() => {
    if (++quitDepth > 12) throw Error("recursive_quit");
    try {
      trace.push("app_quit"); const before = event(); app.emit("before-quit", before);
      if (before.defaultPrevented) return;
      for (const w of [...live]) w.close();
      if (live.size) return;
      const will = event(); app.emit("will-quit", will);
      if (!will.defaultPrevented) { finalExits++; trace.push("app_quit_complete"); app.emit("quit", event(), 0); }
    } finally { quitDepth--; }
  });
  Object.assign(app, { getPath: () => "virtual-r7-profile", getAppPath: () => "virtual-r7-app", requestSingleInstanceLock: () => true,
    whenReady: async () => {}, quit, setLoginItemSettings: vi.fn(), isPackaged: false });
  const trays: Tray[] = []; let menu: { label?: string; click?: () => void }[] = [];
  class Tray {
    destroyed = false; destroys = 0; setToolTip = vi.fn(); on = vi.fn();
    constructor() { trays.push(this); }
    setContextMenu(value: typeof menu) { menu = value; }
    destroy() { if (this.destroyed) throw Error("double_tray_destroy"); this.destroyed = true; this.destroys++; trace.push("destroy:Tray"); }
  }
  const dialog = vi.fn(async (..._args: unknown[]) => ({ response: 0 }));
  vi.doMock("electron", () => ({ app, BrowserWindow: Window, Tray, dialog: { showMessageBox: dialog }, ipcMain: { handle: vi.fn() },
    Menu: { buildFromTemplate: (value: typeof menu) => value }, nativeImage: { createFromDataURL: vi.fn() }, safeStorage: {}, shell: {},
    screen: { getPrimaryDisplay: () => ({ workArea: { x: 0, y: 0, width: 1920, height: 1080 } }) },
    session: { defaultSession: { setPermissionRequestHandler: vi.fn(), setPermissionCheckHandler: vi.fn() } } }));
  vi.doMock("../../electron/main/device-settings", () => ({ DeviceSettingsStore: Settings, defaultSettings, deviceSettingsSchema }));
  vi.doMock("../../electron/main/outbox", () => ({ EncryptedOutbox: Box }));
  vi.doMock("../../electron/main/managed-host-port", () => ({ ManagedHostPort: Noop }));
  vi.doMock("../../electron/main/backend-supervisor", () => ({ BackendSupervisor: Supervisor }));
  vi.doMock("../../electron/main/owner-session", () => ({ LocalOwnerSession: Owner }));
  vi.doMock("../../electron/main/owner-auth-client", () => ({ OwnerAuthClient: Noop }));
  vi.doMock("../../electron/main/owner-secret-store", () => ({ OwnerSecretStore: Noop }));
  vi.doMock("../../electron/main/host-client", () => ({ HostClient: Host }));
  await import("../../electron/main/index"); await flush();
  if (ready) for (const window of windows) window.emit("ready-to-show");
  await flush();
  const main = windows.find(w => w.options.title === "Maris")!;
  expect(main).toBeTruthy(); expect(main.listenerCount("close")).toBe(1);
  expect(backendStart).toHaveBeenCalledTimes(1); expect(establish).toHaveBeenCalledTimes(1);
  expect(main.webContents.send).toHaveBeenCalledWith("runtime:state@1", expect.objectContaining({ state: "online", authenticated: true }));
  expect(trays).toHaveLength(1); expect(windows).toHaveLength(persisted.companionVisible ? 2 : 1);
  if (ready) expect(windows.every(window => window.visible)).toBe(true);
  cleanup.mockClear(); trace.length = 0;
  return { app, main, windows, trays, live, quit, trace, stop, stopEntered, saveGate, holdSave: () => { holdSave = true; },
    save, cleanup, backendStop, recover, revoke, establish, dialog, candidates, deleteConfirmed, persisted: () => persisted,
    trayQuit: () => menu.find(row => row.label === "退出")!.click!(),
    sample: () => ({ closeReceived, shutdownCalls: backendStop.mock.calls.length, finalExits, allClosed,
      liveWindows: live.size, mainDestroyed: main.destroyed, trayDestroyed: trays[0]!.destroyed }) };
}

it("routes an actual main-window quit close through unified shutdown with the companion visible", async () => {
  const f = await fixture();
  const received = f.main.close(); await flush();
  record({ event: "normal_main_close", expectedShutdown: true, actual: f.sample(), prevented: received.defaultPrevented, trace: f.trace });
  expect(f.sample().closeReceived).toBe(1);
  expect(f.backendStop).toHaveBeenCalledTimes(1);
  expect(received.defaultPrevented).toBe(true);
  expect(f.live.size).toBe(2); expect(f.sample().finalExits).toBe(0);
  f.stop.resolve(); await flush();
  expect(f.sample()).toMatchObject({ finalExits: 1, allClosed: 1, liveWindows: 0, trayDestroyed: true });
  expect(f.dialog).not.toHaveBeenCalled();
});

async function finished(f: Awaited<ReturnType<typeof fixture>>) {
  f.stop.resolve(); await flush();
  expect(f.sample()).toMatchObject({ finalExits: 1, allClosed: 1, liveWindows: 0, trayDestroyed: true });
  expect(f.save).toHaveBeenCalledTimes(1); expect(f.cleanup).toHaveBeenCalledTimes(1);
  expect(f.backendStop).toHaveBeenCalledTimes(1);
  expect(f.windows.every(window => window.destroys === 1)).toBe(true); expect(f.trays[0]!.destroys).toBe(1);
  expect(f.quit.mock.calls.length).toBeGreaterThanOrEqual(2); expect(f.quit.mock.calls.length).toBeLessThan(8);
  expect(f.recover).not.toHaveBeenCalled(); expect(f.revoke).not.toHaveBeenCalled(); expect(f.establish).toHaveBeenCalledTimes(1);
  expect(f.trace.indexOf("settings_flush")).toBeLessThan(f.trace.indexOf("outbox_flush"));
  expect(f.trace.indexOf("outbox_flush")).toBeLessThan(f.trace.indexOf("owned_stop_enter"));
  expect(f.trace.indexOf("owned_stop_done")).toBeLessThan(f.trace.indexOf("destroy:Tray"));
}

it.each([
  { closeHintShown: true, companionVisible: true },
  { closeHintShown: true, companionVisible: false },
  { closeHintShown: false, companionVisible: false },
])("keeps explicit quit independent of prior hint and companion visibility: %j", async settings => {
  const f = await fixture(settings); f.main.close(); await flush();
  expect(f.backendStop).toHaveBeenCalledTimes(1); expect(f.dialog).not.toHaveBeenCalled();
  expect(f.main.hide).not.toHaveBeenCalled(); expect(f.sample().finalExits).toBe(0);
  await finished(f);
});

it("waits for the actual settings/outbox flush callback before owned stop and resource release", async () => {
  const f = await fixture(); f.holdSave(); f.main.close(); await flush();
  expect(f.save).toHaveBeenCalledTimes(1); expect(f.cleanup).not.toHaveBeenCalled(); expect(f.backendStop).not.toHaveBeenCalled();
  expect(f.live.size).toBe(2); expect(f.trays[0]!.destroyed).toBe(false); expect(f.sample().finalExits).toBe(0);
  f.saveGate.resolve(); await flush();
  expect(f.cleanup).toHaveBeenCalledTimes(1); expect(f.backendStop).toHaveBeenCalledTimes(1);
  expect(f.live.size).toBe(2); expect(f.sample().finalExits).toBe(0);
  await finished(f); expect(f.persisted()).toMatchObject({ closePolicy: "quit", closeHintShown: false, companionVisible: true });
});

it("coalesces close, before-quit and Tray requests including synchronous last-window reentry", async () => {
  const f = await fixture(); f.main.close(); await flush();
  const before = event(); f.app.emit("before-quit", before); const again = f.main.close(); f.trayQuit(); f.trayQuit(); await flush();
  expect(before.defaultPrevented).toBe(true); expect(again.defaultPrevented).toBe(true);
  expect(f.backendStop).toHaveBeenCalledTimes(1); expect(f.save).toHaveBeenCalledTimes(1); expect(f.cleanup).toHaveBeenCalledTimes(1);
  expect(f.windows.every(window => window.destroys === 0)).toBe(true); expect(f.sample().finalExits).toBe(0);
  await finished(f);
  record({ event: "shutdown_reentry_finished", actual: f.sample(), quitCalls: f.quit.mock.calls.length, trace: f.trace });
});

it("does not release resources or claim success when owned shutdown rejects", async () => {
  const errors = vi.spyOn(console, "error").mockImplementation(() => {});
  const f = await fixture(); f.main.close(); await flush(); f.stop.reject(new Error("VIRTUAL_PRIVATE_STOP_DETAIL")); await flush();
  expect(f.live.size).toBe(2); expect(f.trays[0]!.destroyed).toBe(false); expect(f.sample().finalExits).toBe(0);
  f.main.close(); f.trayQuit(); f.app.emit("before-quit", event()); await flush();
  expect(f.backendStop).toHaveBeenCalledTimes(1); expect(f.save).toHaveBeenCalledTimes(1);
  expect(errors).toHaveBeenCalledExactlyOnceWith("desktop_shutdown_failed");
  expect(JSON.stringify(errors.mock.calls)).not.toContain("VIRTUAL_PRIVATE_STOP_DETAIL");
});

it("preserves default hide_to_tray and the first hint, saving before hiding", async () => {
  const f = await fixture({ ...defaultSettings }); const reply = deferred<{ response: number }>(); f.dialog.mockReturnValueOnce(reply.promise);
  const received = f.main.close(); await flush(); expect(received.defaultPrevented).toBe(true);
  expect(f.dialog).toHaveBeenCalledWith(f.main, expect.objectContaining({ message: "Maris 将继续在托盘运行", buttons: ["知道了"] }));
  expect(f.main.visible).toBe(true); expect(f.save).not.toHaveBeenCalled();
  reply.resolve({ response: 0 }); await flush();
  expect(f.persisted().closeHintShown).toBe(true); expect(f.save).toHaveBeenCalledTimes(1); expect(f.main.hide).toHaveBeenCalledTimes(1);
  f.main.close(); await flush(); expect(f.dialog).toHaveBeenCalledTimes(1); expect(f.main.hide).toHaveBeenCalledTimes(2);
  expect(f.backendStop).not.toHaveBeenCalled(); expect(f.live.size).toBe(2);
});

it("keeps the existing first-hint priority for ask_every_time", async () => {
  const f = await fixture({ closePolicy: "ask_every_time", closeHintShown: false }); f.main.close(); await flush();
  expect(f.dialog).toHaveBeenCalledExactlyOnceWith(f.main, expect.objectContaining({ type: "info", buttons: ["知道了"] }));
  expect(f.main.hide).toHaveBeenCalledTimes(1); expect(f.persisted().closeHintShown).toBe(true); expect(f.backendStop).not.toHaveBeenCalled();
});

it.each([0, 1, 2])("preserves ask_every_time hide/quit/cancel response %i", async response => {
  const f = await fixture({ closePolicy: "ask_every_time", closeHintShown: true }); f.dialog.mockResolvedValueOnce({ response });
  f.main.close(); await flush();
  expect(f.dialog).toHaveBeenCalledExactlyOnceWith(f.main, expect.objectContaining({ buttons: ["隐藏到托盘", "退出", "取消"], cancelId: 2, defaultId: 0 }));
  if (response === 1) await finished(f);
  else {
    expect(f.backendStop).not.toHaveBeenCalled(); expect(f.main.visible).toBe(response === 2); expect(f.live.size).toBe(2);
    expect(f.save).not.toHaveBeenCalled(); expect(f.establish).toHaveBeenCalledTimes(1); expect(f.revoke).not.toHaveBeenCalled();
  }
});

it.each(["tray", "session-end"])("routes virtual %s through the same unified shutdown", async origin => {
  const f = await fixture({ closePolicy: "hide_to_tray" });
  if (origin === "tray") f.trayQuit(); else f.main.emit("session-end");
  await flush(); expect(f.dialog).not.toHaveBeenCalled(); expect(f.live.size).toBe(2); await finished(f);
});

it.each([false, true])("ignores a late close-dialog reply after shutdown (hint previously shown=%s)", async closeHintShown => {
  const f = await fixture({ closePolicy: "ask_every_time", closeHintShown }); const reply = deferred<{ response: number }>();
  f.dialog.mockReturnValueOnce(reply.promise); f.main.close(); await flush(); f.trayQuit(); await flush(); await finished(f);
  reply.resolve({ response: 0 }); await flush();
  expect(f.main.hide).not.toHaveBeenCalled(); expect(f.save).toHaveBeenCalledTimes(1); expect(f.sample().finalExits).toBe(1);
});

it("does not hide a destroyed window when the first-hint save completes during quit", async () => {
  const f = await fixture({ closePolicy: "hide_to_tray" }); f.holdSave(); f.main.close(); await flush();
  expect(f.save).toHaveBeenCalledTimes(1); f.trayQuit(); await flush(); expect(f.save).toHaveBeenCalledTimes(2);
  f.saveGate.resolve(); await flush(); f.stop.resolve(); await flush();
  expect(f.main.hide).not.toHaveBeenCalled(); expect(f.sample().finalExits).toBe(1); expect(f.backendStop).toHaveBeenCalledTimes(1);
});

it.each([false, true])("keeps actual retention prompt shutdown protection (dialog already pending=%s)", async pending => {
  const f = await fixture({}, false); f.candidates.mockResolvedValue([{}]); const reply = deferred<{ response: number }>();
  f.dialog.mockReturnValueOnce(reply.promise);
  if (pending) { f.main.emit("ready-to-show"); await flush(); expect(f.dialog).toHaveBeenCalledTimes(1); }
  f.trayQuit(); await flush();
  if (!pending) { f.main.emit("ready-to-show"); await flush(); expect(f.dialog).not.toHaveBeenCalled(); }
  reply.resolve({ response: 1 }); await flush(); expect(f.deleteConfirmed).not.toHaveBeenCalled(); await finished(f);
});
