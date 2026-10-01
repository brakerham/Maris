import { EventEmitter } from "node:events";
import { describe, expect, it, vi } from "vitest";
import { EncryptedOutbox, type OutboxEntry } from "../../electron/main/outbox";
import { SecureStore } from "../../electron/main/secure-store";
import { OutboxRetentionController, type RetentionWindow } from "../../electron/main/outbox-retention";
import type { MessageBoxOptions } from "electron";

const day = 86_400_000;
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
function deferred<T>() { let resolve!: (value: T) => void; let reject!: (error: Error) => void; const promise = new Promise<T>((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }
class Window extends EventEmitter { destroyed = false; isDestroyed() { return this.destroyed; } destroy() { this.destroyed = true; this.emit("closed"); } }
async function fixture(age = 31 * day) {
  let blob: Buffer | null = null; let id = 0;
  const secure = new SecureStore({ isEncryptionAvailable: () => true, encryptString: (v) => Buffer.from(v).reverse(), decryptString: (v) => Buffer.from(v).reverse().toString() });
  const entries: OutboxEntry[] = [{ draftId: "PRIVATE-ID", clientEventId: "PRIVATE-EVENT", body: "PRIVATE-BODY", digest: "PRIVATE-DIGEST", state: "draft", createdAt: 100 * day - age, updatedAt: 100 * day - age }]; blob = secure.seal(entries);
  const storage = { read: async () => blob, write: async (v: Buffer) => { blob = v; } };
  const box = new EncryptedOutbox(storage, secure, () => 100 * day, () => `virtual-${++id}`); await box.load();
  const window = new Window(); const reply = deferred<{ response: number }>(); const dialog = { showMessageBox: vi.fn((_window: RetentionWindow, _options: MessageBoxOptions) => reply.promise) }; let quitting = false;
  const controller = new OutboxRetentionController(box, dialog, () => quitting);
  return { box, window, reply, dialog, controller, quit: () => { quitting = true; }, reload: async () => { const next = new EncryptedOutbox(storage, secure); await next.load(); return next.list(); } };
}
describe("native outbox confirmation adapter", () => {
  it("does not prompt at exactly 30 days", async () => { const f = await fixture(30 * day); f.controller.attach(f.window); f.window.emit("ready-to-show"); await flush(); expect(f.dialog.showMessageBox).not.toHaveBeenCalled(); });
  it("prompts once after readiness with safe count and retain defaults", async () => {
    const f = await fixture(30 * day + 1); f.controller.attach(f.window); f.controller.attach(f.window); expect(f.dialog.showMessageBox).not.toHaveBeenCalled(); f.window.emit("ready-to-show"); f.window.emit("ready-to-show"); await flush();
    expect(f.dialog.showMessageBox).toHaveBeenCalledTimes(1); const options = f.dialog.showMessageBox.mock.calls[0]![1] as any;
    expect(options).toMatchObject({ defaultId: 0, cancelId: 0, buttons: ["保留", "明确删除"] }); expect(options.message).toContain("1"); expect(options.detail).toContain("永久删除");
    expect(JSON.stringify(options)).not.toMatch(/PRIVATE/); f.reply.resolve({ response: 0 }); await flush(); expect(await f.reload()).toHaveLength(1);
  });
  it.each(["retain", "dialog-close", "rejection"])("retains all data on %s", async (action) => {
    const f = await fixture(); f.controller.attach(f.window); f.window.emit("ready-to-show"); await flush(); if (action === "rejection") f.reply.reject(new Error("PRIVATE-BODY")); else f.reply.resolve({ response: action === "retain" ? 0 : -1 }); await flush(); expect(await f.reload()).toEqual(f.box.list()); expect(f.box.list()).toHaveLength(1);
  });
  it("explicit consent protects state changes and new messages while the dialog is pending", async () => {
    const f = await fixture(); f.controller.attach(f.window); f.window.emit("ready-to-show"); await flush(); await Promise.all([f.box.prepare("new", "virtual-new"), f.box.setState("PRIVATE-EVENT", "sending")]); f.reply.resolve({ response: 1 }); await flush(); expect(await f.reload()).toHaveLength(2);
  });
  it("explicit consent deletes the shown expired draft and persists the result", async () => { const f = await fixture(); f.controller.attach(f.window); f.window.emit("ready-to-show"); await flush(); f.reply.resolve({ response: 1 }); await flush(); expect(await f.reload()).toEqual([]); });
  it.each(["destroy", "quit", "stop"])("does not prompt or delete during %s", async (action) => {
    for (const pending of [false, true]) { const f = await fixture(); f.controller.attach(f.window); if (pending) { f.window.emit("ready-to-show"); await flush(); }
      if (action === "destroy") f.window.destroy(); else if (action === "quit") f.quit(); else f.controller.stop();
      if (!pending) f.window.emit("ready-to-show"); f.reply.resolve({ response: 1 }); await flush(); expect(f.dialog.showMessageBox).toHaveBeenCalledTimes(pending ? 1 : 0); expect(await f.reload()).toHaveLength(1);
    }
  });
});

describe("executable main lifecycle wiring", () => {
  it.each(["before-ready-quit", "pending-quit", "pending-destroy", "online"])("keeps Host startup independent of retention dialog: %s", async (scenario) => {
    vi.resetModules();
    const app = new EventEmitter() as EventEmitter & Record<string, any>;
    Object.assign(app, { getPath: () => "virtual-profile", getAppPath: () => "virtual-app", requestSingleInstanceLock: () => true, whenReady: () => Promise.resolve(), quit: vi.fn(), setLoginItemSettings: vi.fn(), isPackaged: false });
    const windows: any[] = []; const reply = deferred<{ response: number }>(); const showMessageBox = vi.fn(() => reply.promise);
    class MainWindow extends Window {
      webContents = { setWindowOpenHandler: vi.fn(), on: vi.fn(), send: vi.fn() };
      show = vi.fn(); hide = vi.fn(); focus = vi.fn(); loadFile = vi.fn(); loadURL = vi.fn();
      constructor(..._args: any[]) { super(); windows.push(this); }
    }
    const start = vi.fn(async () => ({ state: "online", authenticated: true })); const shutdown = vi.fn(async () => {}); const deleteConfirmed = vi.fn(async () => 1);
    class Box { load = vi.fn(async () => {}); cleanup = vi.fn(async () => {}); retentionCandidates = vi.fn(async () => [{}]); deleteConfirmed = deleteConfirmed; }
    class Composition { start = start; shutdown = shutdown; subscribe = vi.fn(); }
    class Settings { load = async () => ({ closePolicy: "quit", companionVisible: false }); save = async () => {}; }
    class Companion { window = null; setFallback() {} setState() {} }
    class Noop { constructor(..._args: any[]) {} }
    class FakeTray { setToolTip() {} setContextMenu() {} on() {} destroy() {} }
    vi.doMock("electron", () => ({ app, BrowserWindow: MainWindow, dialog: { showMessageBox }, ipcMain: { handle: vi.fn() }, Menu: { buildFromTemplate: vi.fn() }, nativeImage: { createFromDataURL: vi.fn() }, safeStorage: {}, session: { defaultSession: { setPermissionRequestHandler: vi.fn(), setPermissionCheckHandler: vi.fn() } }, shell: {}, Tray: FakeTray }));
    vi.doMock("../../electron/main/outbox", () => ({ EncryptedOutbox: Box }));
    vi.doMock("../../electron/main/composition-root", () => ({ DesktopCompositionRoot: Composition }));
    vi.doMock("../../electron/main/device-settings", () => ({ DeviceSettingsStore: Settings, defaultSettings: {}, deviceSettingsSchema: {} }));
    vi.doMock("../../electron/main/window-lifecycle", () => ({ CompanionController: Companion }));
    vi.doMock("../../electron/main/managed-host-port", () => ({ ManagedHostPort: Noop }));
    vi.doMock("../../electron/main/backend-supervisor", () => ({ BackendSupervisor: Noop }));
    vi.doMock("../../electron/main/owner-session", () => ({ LocalOwnerSession: Noop }));
    vi.doMock("../../electron/main/owner-auth-client", () => ({ OwnerAuthClient: Noop }));
    vi.doMock("../../electron/main/owner-secret-store", () => ({ OwnerSecretStore: Noop }));
    vi.doMock("../../electron/main/host-client", () => ({ HostClient: Noop }));
    vi.stubGlobal("MAIN_WINDOW_VITE_DEV_SERVER_URL", ""); vi.stubGlobal("MAIN_WINDOW_VITE_NAME", "main");
    const priorE2e = process.env.MARIS_E2E; delete process.env.MARIS_E2E;
    try {
      await import("../../electron/main/index"); await flush(); expect(start).toHaveBeenCalledTimes(1); expect(windows).toHaveLength(1); expect(showMessageBox).not.toHaveBeenCalled();
      const window = windows[0]!;
      if (scenario === "before-ready-quit") app.emit("before-quit", { preventDefault() {} });
      window.emit("ready-to-show"); await flush();
      expect(window.show).toHaveBeenCalledTimes(1); expect(showMessageBox).toHaveBeenCalledTimes(scenario === "before-ready-quit" ? 0 : 1);
      expect(window.webContents.send).toHaveBeenCalledWith("runtime:state@1", expect.objectContaining({ state: "online" }));
      if (scenario === "pending-quit") app.emit("before-quit", { preventDefault() {} });
      if (scenario === "pending-destroy") window.destroy();
      reply.resolve({ response: 1 }); await flush(); expect(deleteConfirmed).toHaveBeenCalledTimes(scenario === "online" ? 1 : 0);
      if (scenario === "before-ready-quit" || scenario === "pending-quit") expect(shutdown).toHaveBeenCalledTimes(1);
    } finally { if (priorE2e === undefined) delete process.env.MARIS_E2E; else process.env.MARIS_E2E = priorE2e; vi.unstubAllGlobals(); }
  });
});
