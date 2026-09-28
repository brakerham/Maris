import path from "node:path";
import { randomBytes } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { app, BrowserWindow, dialog, ipcMain, Menu, nativeImage, safeStorage, session, shell, Tray } from "electron";
import { DeviceSettingsStore, defaultSettings, deviceSettingsSchema, type DeviceSettings } from "./device-settings";
import { EncryptedOutbox } from "./outbox";
import { SecureStore } from "./secure-store";
import { validateIpc, type IpcChannel } from "./ipc-contract";
import { secureWebPreferences } from "./security";
import { CompanionController } from "./window-lifecycle";
import type { RuntimeSnapshot } from "../../src/shared/contracts";
import { compileRegistry } from "../../src/modules/registry";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { BackendSupervisor } from "./backend-supervisor";
import { DesktopCompositionRoot } from "./composition-root";
import { HostClient } from "./host-client";
import { ManagedHostPort } from "./managed-host-port";
import { OwnerAuthClient } from "./owner-auth-client";
import { OwnerSecretStore } from "./owner-secret-store";
import { LocalOwnerSession } from "./owner-session";

if (process.env.MARIS_E2E === "1") {
  const isolatedProfile = process.env.MARIS_E2E_USER_DATA;
  if (!isolatedProfile || !path.isAbsolute(isolatedProfile)) throw new Error("invalid_e2e_profile");
  app.setPath("userData", isolatedProfile);
  app.disableHardwareAcceleration();
}

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let quitting = false;
let shutdownComplete = false;
let settings: DeviceSettings = { ...defaultSettings };
let composition: DesktopCompositionRoot | null = null;
const allowedExternalLinks = new Map([["privacy", "https://github.com/brakerham/Maris"]]);
const settingsStore = new DeviceSettingsStore(path.join(app.getPath("userData"), "device-settings.json"));
const companion = new CompanionController(path.join(__dirname, "companion.js"));
const encryptedStore = new SecureStore({
  isEncryptionAvailable: () => safeStorage.isEncryptionAvailable(),
  encryptString: (value) => safeStorage.encryptString(value),
  decryptString: (value) => safeStorage.decryptString(value)
});
const outboxFile = path.join(app.getPath("userData"), "outbox.bin");
const outbox = new EncryptedOutbox({
  read: async () => { try { return await readFile(outboxFile); } catch { return null; } },
  write: async (value) => { await mkdir(path.dirname(outboxFile), { recursive: true }); const temporary = `${outboxFile}.tmp`; await writeFile(temporary, value, { mode: 0o600 }); await rename(temporary, outboxFile); }
}, encryptedStore);

function createComposition(): DesktopCompositionRoot {
  const projectRoot = process.env.MARIS_HOST_PROJECT_ROOT ?? (app.isPackaged ? process.resourcesPath : path.resolve(app.getAppPath(), "..", ".."));
  const pythonExecutable = process.env.MARIS_PYTHON_EXECUTABLE ?? (app.isPackaged ? "python" : path.join(projectRoot, ".venv", "Scripts", "python.exe"));
  const databasePath = path.join(app.getPath("userData"), "maris-host.db").replaceAll("\\", "/");
  const bootstrapToken = secret();
  const externalUrl = !app.isPackaged && process.env.MARIS_EXTERNAL_HOST_URL ? new URL(process.env.MARIS_EXTERNAL_HOST_URL) : undefined;
  const externalNonce = !app.isPackaged ? process.env.MARIS_EXTERNAL_HOST_NONCE ?? null : null;
  const port = new ManagedHostPort({
    pythonExecutable,
    projectRoot,
    databaseUrl: `sqlite+pysqlite:///${databasePath}`,
    secrets: {
      bootstrapToken,
      bindingHmacKey: secret(),
      adapterToken: secret(),
      hostStateKey: secret(),
      cursorKey: secret(),
      agentDigestKey: secret(),
      financeReceiptKey: secret(),
    },
    ...(externalUrl ? { externalUrl } : {}),
  });
  const mode = settings.backendMode === "external_dev" && !app.isPackaged ? "external_dev" : "managed";
  const supervisor = new BackendSupervisor(mode, port, () => Date.now(), externalNonce);
  const ownerSecrets = new OwnerSecretStore(path.join(app.getPath("userData"), "owner-session.bin"), encryptedStore);
  const auth = new OwnerAuthClient(() => supervisor.endpoint(), bootstrapToken);
  const owner = new LocalOwnerSession(auth, ownerSecrets, () => ({
    handle: "local_owner",
    password: secret(48),
  }));
  const host = new HostClient(
    () => supervisor.endpoint(),
    () => owner.refresh(),
    () => owner.revoke()
  );
  return new DesktopCompositionRoot(
    supervisor,
    owner,
    host,
    compileRegistry([dailyFinanceContribution]),
    async () => { await settingsStore.save(settings); await outbox.cleanup(); }
  );
}

function secret(bytes = 32): string { return randomBytes(bytes).toString("base64url"); }

function createMainWindow(): BrowserWindow {
  const window = new BrowserWindow({ title: "Maris", width: 1360, height: 820, minWidth: 960, minHeight: 680, show: false, webPreferences: secureWebPreferences(path.join(__dirname, "preload.js")) });
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  window.webContents.on("will-navigate", (event) => event.preventDefault());
  window.on("close", (event) => { if (!quitting && settings.closePolicy !== "quit") { event.preventDefault(); void handleClose(window); } });
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) void window.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  else void window.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  window.once("ready-to-show", () => window.show());
  return window;
}

async function handleClose(window: BrowserWindow): Promise<void> {
  if (!settings.closeHintShown) {
    await dialog.showMessageBox(window, { type: "info", message: "Maris 将继续在托盘运行", detail: "可在设置中改为每次询问或直接退出。", buttons: ["知道了"] });
    settings = { ...settings, closeHintShown: true }; await settingsStore.save(settings); window.hide(); return;
  }
  if (settings.closePolicy === "ask_every_time") {
    const result = await dialog.showMessageBox(window, { type: "question", message: "关闭 Maris", buttons: ["隐藏到托盘", "退出", "取消"], cancelId: 2, defaultId: 0 });
    if (result.response === 0) window.hide(); else if (result.response === 1) { quitting = true; app.quit(); }
    return;
  }
  window.hide();
}

function registerSecurityDefaults(): void {
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
}

function registerMainHandler(channel: IpcChannel, handler: (...args: any[]) => unknown | Promise<unknown>): void {
  ipcMain.handle(channel, (event, ...args) => {
    if (!mainWindow) throw new Error("main_window_unavailable");
    const parsed = validateIpc(event, mainWindow, channel, args, MAIN_WINDOW_VITE_DEV_SERVER_URL);
    return handler(...parsed);
  });
}

function registerIpc(): void {
  registerMainHandler("runtime:get-snapshot@1", () => requireComposition().snapshot());
  registerMainHandler("runtime:recover@1", () => requireComposition().recover());
  registerMainHandler("modules:list@1", () => requireComposition().modules());
  registerMainHandler("window:perform@1", (action: string) => { if (action === "show_main" || action === "focus_main") { mainWindow?.show(); mainWindow?.focus(); } if (action === "hide_main") mainWindow?.hide(); if (action === "toggle_companion") companion.toggle(); return { accepted: true }; });
  registerMainHandler("external:open@1", async (linkId: string) => { const url = allowedExternalLinks.get(linkId); if (!url) throw new Error("external_link_not_allowed"); await shell.openExternal(url); return { accepted: true }; });
  registerMainHandler("settings:update@1", async (value: object) => { const next = deviceSettingsSchema.parse({ ...settings, ...value }); await settingsStore.save(next); settings = next; if (process.env.MARIS_E2E !== "1") app.setLoginItemSettings({ openAtLogin: settings.launchAtLogin }); return { accepted: true }; });
  registerMainHandler("outbox:enqueue@1", async (value: { draftId: string; body: string }) => ({ clientEventId: (await outbox.prepare(value.draftId, value.body)).clientEventId }));
  ipcMain.handle("companion:get-state@1", (event, ...args) => { const window = companion.window; if (!window) throw new Error("companion_window_unavailable"); validateIpc(event, window, "companion:get-state@1", args, COMPANION_WINDOW_VITE_DEV_SERVER_URL); return companion.snapshot(); });
  ipcMain.handle("companion:open-main@1", (event, ...args) => { const window = companion.window; if (!window) throw new Error("companion_window_unavailable"); validateIpc(event, window, "companion:open-main@1", args, COMPANION_WINDOW_VITE_DEV_SERVER_URL); mainWindow?.show(); mainWindow?.focus(); return { accepted: true }; });
}

function requireComposition(): DesktopCompositionRoot {
  if (!composition) throw new Error("composition_unavailable");
  return composition;
}

function publishRuntime(snapshot: RuntimeSnapshot): void {
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send("runtime:state@1", snapshot);
  companion.setState(snapshot.state === "online" ? "idle" : "offline");
}

async function shutdown(): Promise<void> {
  if (shutdownComplete) return;
  await composition?.shutdown();
  tray?.destroy();
  tray = null;
  companion.window?.destroy();
  mainWindow?.destroy();
  mainWindow = null;
  shutdownComplete = true;
}

function createTray(): void {
  const icon = nativeImage.createFromDataURL("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=");
  tray = new Tray(icon); tray.setToolTip("Maris"); tray.setContextMenu(Menu.buildFromTemplate([
    { label: "打开 Maris", click: () => { mainWindow?.show(); mainWindow?.focus(); } },
    { label: "显示/隐藏毛毛", click: () => companion.toggle() },
    { type: "separator" }, { label: "退出", click: requestQuit }
  ])); tray.on("double-click", () => mainWindow?.show());
}

function requestQuit(): void { quitting = true; app.quit(); }

const singleInstance = app.requestSingleInstanceLock();
if (!singleInstance) app.quit();
else {
  app.on("second-instance", () => { mainWindow?.show(); mainWindow?.focus(); });
  void app.whenReady().then(async () => {
    registerSecurityDefaults(); settings = await settingsStore.load(); await outbox.load(); await outbox.cleanup();
    companion.setFallback(settings.companionFallback || process.env.MARIS_E2E === "1");
    composition = createComposition();
    composition.subscribe(publishRuntime);
    if (process.env.MARIS_E2E !== "1") app.setLoginItemSettings({ openAtLogin: settings.launchAtLogin }); mainWindow = createMainWindow(); registerIpc(); createTray();
    mainWindow.on("session-end", () => { quitting = true; app.quit(); });
    void composition.start().then(publishRuntime);
    if (settings.companionVisible) { const window = await companion.show(); window.setAlwaysOnTop(settings.companionAlwaysOnTop); }
    if (process.env.MARIS_E2E === "1" && process.env.MARIS_E2E_EXIT_MS) {
      const delay = Number(process.env.MARIS_E2E_EXIT_MS);
      if (Number.isFinite(delay) && delay >= 1000 && delay <= 30_000) setTimeout(requestQuit, delay);
    }
  });
  app.on("before-quit", (event) => {
    quitting = true;
    if (shutdownComplete) return;
    event.preventDefault();
    void shutdown().then(() => app.quit());
  });
  app.on("window-all-closed", () => { if (quitting) app.quit(); });
}
