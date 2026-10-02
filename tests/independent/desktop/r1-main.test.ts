import { EventEmitter } from 'node:events';
import path from 'node:path';
import { afterEach, expect, test, vi } from 'vitest';
import { deferred, encryptedFixture, settle } from './r1-fixtures';

// Import and execute the actual main module. Only OS, filesystem, and Host ports
// are virtual; retention, outbox, schemas, IPC registration and lifecycle are real.
async function boot() {
  vi.resetModules();
  const f = encryptedFixture(); const seed = f.open();
  const draft = await seed.prepare('virtual-old-draft', 'VIRTUAL_DRAFT'); await seed.setState(draft.clientEventId, 'draft');
  await seed.prepare('virtual-old-queue', 'VIRTUAL_QUEUE');
  const sending = await seed.prepare('virtual-sending', 'VIRTUAL_SENDING'); await seed.setState(sending.clientEventId, 'sending');
  const fresh = await seed.prepare('virtual-fresh', 'VIRTUAL_FRESH');
  const entries = seed.list().map(e => e.clientEventId === fresh.clientEventId ? { ...e, createdAt: Date.now(), updatedAt: Date.now() } : e);
  const files = new Map<string, Buffer>();
  const profile = path.resolve('tests/independent/desktop/evidence/r1/virtual-main-profile');
  const outboxFile = path.join(profile, 'outbox.bin'); files.set(outboxFile, f.crypto.seal(entries));
  const ready = deferred<void>(); const decision = deferred<{ response: number }>();
  const app = Object.assign(new EventEmitter(), {
    getPath: () => profile, getAppPath: () => process.cwd(), isPackaged: false,
    requestSingleInstanceLock: () => true, whenReady: () => ready.promise,
    setLoginItemSettings: vi.fn(), quit: vi.fn(), setPath: vi.fn(), disableHardwareAcceleration: vi.fn(),
  });
  const windows: any[] = [];
  class Window extends EventEmitter {
    destroyed = false; visible = false;
    webContents = Object.assign(new EventEmitter(), { mainFrame: { url: 'file:///virtual/index.html' },
      setWindowOpenHandler: vi.fn(), send: vi.fn() });
    constructor(public options: any) { super(); windows.push(this); }
    isDestroyed() { return this.destroyed; } isVisible() { return this.visible; }
    show() { this.visible = true; } hide() { this.visible = false; } focus() {} setAlwaysOnTop() {}
    async loadFile() {} async loadURL() {}
    destroy() { this.destroyed = true; this.emit('closed'); }
  }
  const dialog = { showMessageBox: vi.fn(() => decision.promise) };
  const ipcHandlers = new Map();
  class Tray { setToolTip() {} setContextMenu() {} on() {} destroy() {} }
  const hostStart = vi.fn(async () => ({ state: 'online' })); const hostShutdown = vi.fn();
  class Composition {
    constructor(...args: any[]) { this.persist = args[4]; }
    persist: () => Promise<void>;
    subscribe() {} start() { return hostStart(); } snapshot() { return { state: 'online' }; } modules() { return []; }
    async shutdown() { hostShutdown(); await this.persist(); }
  }
  vi.doMock('electron', () => ({ app, BrowserWindow: Window, dialog,
    ipcMain: { handle: (name: string, cb: unknown) => ipcHandlers.set(name, cb) },
    Menu: { buildFromTemplate: (items: unknown) => items }, nativeImage: { createFromDataURL: () => ({}) },
    safeStorage: f.provider, session: { defaultSession: { setPermissionRequestHandler() {}, setPermissionCheckHandler() {} } },
    shell: { openExternal: vi.fn() }, Tray, screen: { getPrimaryDisplay: () => ({ workArea: { x: 0, y: 0, width: 1200, height: 800 } }) },
  }));
  vi.doMock('node:fs/promises', () => ({
    mkdir: async () => undefined,
    readFile: async (name: string, encoding?: string) => { const data = files.get(name); if (!data) throw new Error('virtual_missing'); return encoding ? data.toString('utf8') : Buffer.from(data); },
    writeFile: async (name: string, value: Buffer) => { files.set(name, Buffer.from(value)); },
    rename: async (old: string, next: string) => { files.set(next, files.get(old)!); files.delete(old); },
    open: async (name: string) => ({ writeFile: async (value: string) => { files.set(name, Buffer.from(value)); }, sync: async () => {}, close: async () => {} }),
  }));
  vi.doMock('../../../apps/desktop/electron/main/composition-root', () => ({ DesktopCompositionRoot: Composition }));
  for (const name of ['MAIN_WINDOW_VITE_DEV_SERVER_URL', 'COMPANION_WINDOW_VITE_DEV_SERVER_URL']) vi.stubGlobal(name, undefined);
  vi.stubGlobal('MAIN_WINDOW_VITE_NAME', 'virtual-main'); vi.stubGlobal('COMPANION_WINDOW_VITE_NAME', 'virtual-companion');
  vi.stubGlobal('__dirname', profile);
  await import('../../../apps/desktop/electron/main/index'); ready.resolve(); await settle();
  const main = windows.find(w => w.options.title === 'Maris');
  const read = () => f.crypto.open<any[]>(files.get(outboxFile)!);
  return { app, decision, main, windows, dialog, hostStart, hostShutdown, read, entries, ipcHandlers };
}

afterEach(() => { vi.unstubAllGlobals(); vi.doUnmock('electron'); vi.doUnmock('node:fs/promises'); vi.doUnmock('../../../apps/desktop/electron/main/composition-root'); });

test('R1-MAIN-01 | real main starts Host before native dialog response; cancel preserves disk', async () => {
  const h = await boot(); expect(h.hostStart).toHaveBeenCalledTimes(1); expect(h.dialog.showMessageBox).not.toHaveBeenCalled();
  expect(h.windows.map(w => w.options.title).sort()).toEqual(['Maris', '毛毛']);
  h.main.emit('ready-to-show'); await settle(); expect(h.dialog.showMessageBox).toHaveBeenCalledTimes(1);
  expect(h.dialog.showMessageBox.mock.calls[0][0]).toBe(h.main);
  expect(h.dialog.showMessageBox.mock.calls[0][1]).toMatchObject({ defaultId: 0, cancelId: 0, buttons: ['保留', '明确删除'] });
  h.main.emit('ready-to-show'); h.decision.resolve({ response: 0 }); await settle(); expect(h.read()).toEqual(h.entries);
});
test('R1-MAIN-02 | before-quit before window ready stops retention and runs persistence cleanup', async () => {
  const h = await boot(); h.app.emit('before-quit', { preventDefault: vi.fn() }); await settle();
  h.main.emit('ready-to-show'); await settle(); expect(h.dialog.showMessageBox).not.toHaveBeenCalled();
  expect(h.hostShutdown).toHaveBeenCalledTimes(1); expect(h.read()).toEqual(h.entries); expect(h.windows.every(w => w.destroyed)).toBe(true);
});
test('R1-MAIN-03 | before-quit while dialog pending ignores later affirmative response', async () => {
  const h = await boot(); h.main.emit('ready-to-show'); await settle(); expect(h.dialog.showMessageBox).toHaveBeenCalledTimes(1);
  h.app.emit('before-quit', { preventDefault: vi.fn() }); await settle(); h.decision.resolve({ response: 1 }); await settle();
  expect(h.hostShutdown).toHaveBeenCalledTimes(1); expect(h.read()).toEqual(h.entries);
});
test('R1-MAIN-04 | main destruction during dialog preserves all virtual data', async () => {
  const h = await boot(); h.main.emit('ready-to-show'); await settle(); h.main.destroy(); h.decision.resolve({ response: 1 }); await settle();
  expect(h.read()).toEqual(h.entries);
});
test('R1-MAIN-05 | real native adapter affirmative deletes exactly aged draft/queued', async () => {
  const h = await boot(); h.main.emit('ready-to-show'); await settle(); h.decision.resolve({ response: 1 }); await settle();
  expect(h.read().map(e => e.body)).toEqual(['VIRTUAL_SENDING', 'VIRTUAL_FRESH']);
  expect(h.hostStart).toHaveBeenCalledTimes(1);
});
