import { EventEmitter } from "node:events";
import type { BrowserWindow, IpcMainInvokeEvent } from "electron";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultSettings, deviceSettingsSchema, type DeviceSettings } from "../../electron/main/device-settings";
import { validateIpc, type IpcChannel } from "../../electron/main/ipc-contract";
import { settingsSnapshotSchema, type MarisBridge, type SettingsSnapshot } from "../../src/shared/contracts";

type Invocation = Pick<IpcMainInvokeEvent, "sender" | "senderFrame">;
type Handler = (event: Invocation, ...args: unknown[]) => unknown;
const virtualSnapshot: SettingsSnapshot = { theme: "dark", reducedMotion: true, privacyMode: true };
const mocked = ["device-settings", "outbox", "managed-host-port", "backend-supervisor", "owner-session", "owner-auth-client", "owner-secret-store", "host-client"];
const flush = async () => { for (let i = 0; i < 60; i++) await Promise.resolve(); };

afterEach(() => {
  vi.doUnmock("electron");
  for (const name of mocked) vi.doUnmock(`../../electron/main/${name}`);
  vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs();
});

async function mainFixture() {
  vi.resetModules();
  vi.stubEnv("MARIS_E2E", ""); vi.stubEnv("MARIS_E2E_EXIT_MS", "");
  vi.stubEnv("MARIS_EXTERNAL_HOST_URL", ""); vi.stubEnv("MARIS_EXTERNAL_HOST_NONCE", "");
  for (const name of ["MAIN_WINDOW", "COMPANION_WINDOW"]) {
    vi.stubGlobal(`${name}_VITE_DEV_SERVER_URL`, ""); vi.stubGlobal(`${name}_VITE_NAME`, name.toLowerCase());
  }
  let persisted: DeviceSettings = { ...defaultSettings, ...virtualSnapshot, launchAtLogin: true,
    closePolicy: "quit", companionVisible: true, companionAppearance: "VIRTUAL_PRIVATE_APPEARANCE",
    mainBounds: { x: 1, y: 2, width: 1000, height: 700, displayId: "VIRTUAL_PRIVATE_DISPLAY" } };
  const load = vi.fn(async () => ({ ...persisted }));
  const save = vi.fn(async (value: DeviceSettings) => { persisted = { ...value }; });
  const cleanup = vi.fn(async () => {}); const outboxLoad = vi.fn(async () => {});
  const prepare = vi.fn(); const candidates = vi.fn(async () => []); const deleteConfirmed = vi.fn();
  const start = vi.fn(async () => ({ state: "online", mode: "managed", authenticated: false, errorCode: null }));
  const recover = vi.fn(); const stop = vi.fn(); const establish = vi.fn(async () => "authenticated");
  const revoke = vi.fn(); const refresh = vi.fn(); const setAccessToken = vi.fn();
  const modules = vi.fn(async () => [{ module_id: "daily_finance", version: "1.0.0", enabled: true,
    profile_ids: ["daily_finance.assistant@1"], api_prefixes: ["/api/v1/finance"], settings_schema_version: 1 }]);
  class Settings { load = load; save = save; }
  class Box { load = outboxLoad; cleanup = cleanup; prepare = prepare; retentionCandidates = candidates; deleteConfirmed = deleteConfirmed; }
  class Supervisor {
    snapshot = () => ({ state: "online", mode: "managed", authenticated: false, errorCode: null });
    subscribe = vi.fn(); start = start; recover = recover; shutdown = stop;
  }
  class Owner { safeState = "authenticated"; establish = establish; revoke = revoke; refresh = refresh; accessToken = () => "VIRTUAL_R8_TOKEN"; }
  class Host { modules = modules; setAccessToken = setAccessToken; }
  class Noop { constructor(..._args: unknown[]) {} }
  const windows: Window[] = [];
  class Window extends EventEmitter {
    webContents = { mainFrame: { url: "file:///virtual-r8/index.html" }, setWindowOpenHandler: vi.fn(), on: vi.fn(), send: vi.fn() };
    show = vi.fn(); hide = vi.fn(); focus = vi.fn(); setAlwaysOnTop = vi.fn(); destroy = vi.fn();
    loadURL = vi.fn(async () => {}); loadFile = vi.fn(async () => {});
    isDestroyed = () => false; isVisible = () => true;
    constructor(readonly options: { title: string }) { super(); windows.push(this); }
  }
  const login = vi.fn(); const app = Object.assign(new EventEmitter(), {
    getPath: () => "virtual-r8-profile", getAppPath: () => "virtual-r8-app", isPackaged: false,
    requestSingleInstanceLock: () => true, whenReady: async () => {}, quit: vi.fn(), setLoginItemSettings: login
  });
  class Tray { setToolTip = vi.fn(); setContextMenu = vi.fn(); on = vi.fn(); destroy = vi.fn(); }
  const handlers = new Map<string, Handler>();
  const openExternal = vi.fn(); const dialog = vi.fn();
  vi.doMock("electron", () => ({ app, BrowserWindow: Window, Tray,
    ipcMain: { handle: (channel: string, handler: Handler) => handlers.set(channel, handler) },
    Menu: { buildFromTemplate: (value: unknown) => value }, nativeImage: { createFromDataURL: vi.fn() },
    dialog: { showMessageBox: dialog }, safeStorage: {}, shell: { openExternal },
    screen: { getPrimaryDisplay: () => ({ workArea: { x: 0, y: 0, width: 1920, height: 1080 } }) },
    session: { defaultSession: { setPermissionRequestHandler: vi.fn(), setPermissionCheckHandler: vi.fn() } }
  }));
  vi.doMock("../../electron/main/device-settings", () => ({ DeviceSettingsStore: Settings, defaultSettings, deviceSettingsSchema }));
  vi.doMock("../../electron/main/outbox", () => ({ EncryptedOutbox: Box }));
  vi.doMock("../../electron/main/managed-host-port", () => ({ ManagedHostPort: Noop }));
  vi.doMock("../../electron/main/backend-supervisor", () => ({ BackendSupervisor: Supervisor }));
  vi.doMock("../../electron/main/owner-session", () => ({ LocalOwnerSession: Owner }));
  vi.doMock("../../electron/main/owner-auth-client", () => ({ OwnerAuthClient: Noop }));
  vi.doMock("../../electron/main/owner-secret-store", () => ({ OwnerSecretStore: Noop }));
  vi.doMock("../../electron/main/host-client", () => ({ HostClient: Host }));
  await import("../../electron/main/index"); await flush();
  const main = windows.find(window => window.options.title === "Maris")!;
  const companion = windows.find(window => window.options.title === "毛毛")!;
  expect(main).toBeDefined(); expect(companion).toBeDefined(); expect(load).toHaveBeenCalledTimes(1);
  expect(start).toHaveBeenCalledTimes(1); expect(establish).toHaveBeenCalledTimes(1); expect(modules).toHaveBeenCalledTimes(1);
  expect(handlers.has("settings:get-snapshot@1")).toBe(true);
  expect(main.webContents.send).toHaveBeenCalledWith("runtime:state@1", expect.objectContaining({ authenticated: true, state: "online" }));
  const effects = { load, save, cleanup, outboxLoad, prepare, candidates, deleteConfirmed, start, recover, stop,
    establish, revoke, refresh, modules, setAccessToken, login, openExternal, dialog };
  for (const effect of Object.values(effects)) effect.mockClear();
  const event = { sender: main.webContents, senderFrame: main.webContents.mainFrame } as unknown as Invocation;
  const invoke = (channel: IpcChannel, args: unknown[] = [], sender = event) => handlers.get(channel)!(sender, ...args);
  return { main, companion, event, effects, invoke, persisted: () => persisted };
}

describe("actual main settings projection", () => {
  it("returns fresh three-field loaded snapshots without storage, OS, Host or outbox effects", async () => {
    const f = await mainFixture();
    const before = structuredClone(f.persisted());
    const first = f.invoke("settings:get-snapshot@1") as Record<string, unknown>;
    const second = f.invoke("settings:get-snapshot@1");
    expect(first).toEqual(virtualSnapshot); expect(second).toEqual(virtualSnapshot); expect(first).not.toBe(second);
    expect(Object.keys(first).sort()).toEqual(["privacyMode", "reducedMotion", "theme"]);
    expect(JSON.stringify(first)).not.toContain("VIRTUAL_PRIVATE");
    first.theme = "light"; first.privacyMode = false; first.reducedMotion = false; first.token = "VIRTUAL_MUTATION";
    expect(f.invoke("settings:get-snapshot@1")).toEqual(virtualSnapshot); expect(f.persisted()).toEqual(before);
    for (const effect of Object.values(f.effects)) expect(effect).not.toHaveBeenCalled();
  });

  it("reads the current settings after a successful typed update and preserves the old update receipt", async () => {
    const f = await mainFixture(); const patch = { theme: "high_contrast", reducedMotion: false, privacyMode: false };
    await expect(f.invoke("settings:update@1", [patch])).resolves.toEqual({ accepted: true });
    expect(f.effects.save).toHaveBeenCalledTimes(1); expect(f.effects.login).toHaveBeenCalledExactlyOnceWith({ openAtLogin: true });
    const updated = structuredClone(f.persisted());
    for (const effect of Object.values(f.effects)) effect.mockClear();
    expect(f.invoke("settings:get-snapshot@1")).toEqual(patch); expect(f.persisted()).toEqual(updated);
    for (const effect of Object.values(f.effects)) expect(effect).not.toHaveBeenCalled();
  });

  it("keeps the loaded snapshot when a write fails and does not broaden write permissions", async () => {
    const f = await mainFixture(); f.effects.save.mockRejectedValueOnce(new Error("VIRTUAL_SAVE_FAILURE"));
    await expect(f.invoke("settings:update@1", [{ theme: "light" }])).rejects.toThrow("VIRTUAL_SAVE_FAILURE");
    expect(f.invoke("settings:get-snapshot@1")).toEqual(virtualSnapshot); expect(f.effects.login).not.toHaveBeenCalled();
    for (const patch of [{ closePolicy: "quit" }, { token: "VIRTUAL_PRIVATE" }, { theme: "sepia" }]) {
      expect(() => f.invoke("settings:update@1", [patch])).toThrow();
    }
    expect(f.effects.save).toHaveBeenCalledTimes(1);
  });

  it("uses actual main sender, frame, origin and empty-argument checks, excluding the companion", async () => {
    const f = await mainFixture(); const channel = "settings:get-snapshot@1";
    const wrongSender = { ...f.event, sender: {} } as Invocation;
    const subframe = { ...f.event, senderFrame: { url: f.main.webContents.mainFrame.url } } as Invocation;
    const companion = { sender: f.companion.webContents, senderFrame: f.companion.webContents.mainFrame } as unknown as Invocation;
    for (const event of [wrongSender, subframe, companion]) expect(() => f.invoke(channel, [], event)).toThrow("ipc_sender_rejected");
    f.main.webContents.mainFrame.url = "https://untrusted.invalid/";
    expect(() => f.invoke(channel)).toThrow("ipc_origin_rejected");
    f.main.webContents.mainFrame.url = "file:///virtual-r8/index.html";
    expect(() => f.invoke(channel, ["VIRTUAL_ARGUMENT"])).toThrow();
    expect(() => f.invoke(channel, [null, null])).toThrow();
    expect(f.invoke(channel)).toEqual(virtualSnapshot);
    for (const effect of Object.values(f.effects)) expect(effect).not.toHaveBeenCalled();
  });
});

describe("actual preload settings bridge", () => {
  it("adds only the fixed zero-argument getter while keeping the existing bridge key sets", async () => {
    vi.resetModules();
    const invoke = vi.fn(async () => virtualSnapshot); const expose = vi.fn();
    vi.doMock("electron", () => ({ contextBridge: { exposeInMainWorld: expose }, ipcRenderer: { invoke, on: vi.fn(), removeListener: vi.fn() } }));
    await import("../../electron/preload/index");
    expect(expose).toHaveBeenCalledTimes(1); expect(expose.mock.calls[0]![0]).toBe("maris");
    const bridge = expose.mock.calls[0]![1] as MarisBridge;
    expect(Object.isFrozen(bridge)).toBe(true);
    const keysets = Object.fromEntries(Object.entries(bridge).map(([key, value]) => [key, Object.keys(value).sort()]));
    expect(keysets).toEqual({ runtime: ["getSnapshot", "recover", "subscribe"], window: ["perform"], modules: ["list"],
      settings: ["getSnapshot", "update"], outbox: ["enqueue"], external: ["open"] });
    expect(invoke).not.toHaveBeenCalled();
    await expect(bridge.settings.getSnapshot()).resolves.toEqual(virtualSnapshot);
    expect(invoke).toHaveBeenCalledExactlyOnceWith("settings:get-snapshot@1");
    invoke.mockClear();
    await (bridge.settings.getSnapshot as (...args: unknown[]) => Promise<unknown>)("untrusted:channel", { path: "VIRTUAL_PATH" });
    expect(invoke).toHaveBeenCalledExactlyOnceWith("settings:get-snapshot@1");
    invoke.mockClear();
    await bridge.settings.update({ theme: "dark", privacyMode: true });
    expect(invoke).toHaveBeenCalledExactlyOnceWith("settings:update@1", { theme: "dark", privacyMode: true });
  });
});

describe("settings snapshot input and response boundaries", () => {
  it("validates the new IPC channel using the actual empty tuple and identity rules", () => {
    const frame = { url: "file:///virtual-r8/index.html" }; const contents = { mainFrame: frame };
    const window = { webContents: contents } as unknown as BrowserWindow;
    const event = { sender: contents, senderFrame: frame } as unknown as Invocation;
    const channel = "settings:get-snapshot@1";
    expect(validateIpc(event, window, channel, [])).toEqual([]);
    expect(() => validateIpc({ ...event, sender: {} } as Invocation, window, channel, [])).toThrow("ipc_sender_rejected");
    expect(() => validateIpc({ ...event, senderFrame: { ...frame } } as Invocation, window, channel, [])).toThrow("ipc_sender_rejected");
    frame.url = "https://untrusted.invalid/";
    expect(() => validateIpc(event, window, channel, [])).toThrow("ipc_origin_rejected");
    frame.url = "file:///virtual-r8/index.html";
    expect(() => validateIpc(event, window, channel, [undefined])).toThrow();
    expect(() => validateIpc(event, window, channel, [1, 2])).toThrow();
  });

  it.each(["system", "light", "dark", "high_contrast"])("accepts the exact %s snapshot without coercion", theme => {
    const value = { theme, reducedMotion: false, privacyMode: true };
    expect(settingsSnapshotSchema.parse(value)).toEqual(value);
  });

  it.each([
    { label: "missing theme", value: { reducedMotion: false, privacyMode: true } },
    { label: "missing privacy", value: { theme: "dark", reducedMotion: false } },
    { label: "missing motion", value: { theme: "dark", privacyMode: true } },
    { label: "invalid enum", value: { ...virtualSnapshot, theme: "sepia" } },
    { label: "theme type", value: { ...virtualSnapshot, theme: 1 } },
    { label: "motion type", value: { ...virtualSnapshot, reducedMotion: "false" } },
    { label: "privacy type", value: { ...virtualSnapshot, privacyMode: "true" } },
    { label: "extra field", value: { ...virtualSnapshot, closePolicy: "quit" } },
    { label: "extra private field", value: { ...virtualSnapshot, token: "VIRTUAL_PRIVATE" } },
    { label: "null", value: null },
    { label: "array", value: [virtualSnapshot] }
  ])("rejects $label responses", ({ value }) => {
    expect(settingsSnapshotSchema.safeParse(value).success).toBe(false);
  });
});
