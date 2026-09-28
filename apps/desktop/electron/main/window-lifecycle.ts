import path from "node:path";
import { BrowserWindow, type Rectangle, screen } from "electron";
import { secureWebPreferences } from "./security";

export const companionStates = ["idle", "listening", "thinking", "tool", "needs_confirmation", "error", "offline"] as const;
export type CompanionState = (typeof companionStates)[number];

export function clampBounds(bounds: Rectangle, workArea: Rectangle): Rectangle {
  const width = Math.min(Math.max(bounds.width, 176), workArea.width);
  const height = Math.min(Math.max(bounds.height, 176), workArea.height);
  return {
    width, height,
    x: Math.min(Math.max(bounds.x, workArea.x), workArea.x + workArea.width - width),
    y: Math.min(Math.max(bounds.y, workArea.y), workArea.y + workArea.height - height)
  };
}

export class CompanionController {
  #window: BrowserWindow | null = null;
  #state: CompanionState = "offline";
  #appearanceId = "daily_finance";
  #fallback = false;
  constructor(private readonly preloadPath: string) {}
  get window(): BrowserWindow | null { return this.#window; }
  snapshot() { return { state: this.#state, appearanceId: this.#appearanceId } as const; }
  setState(state: CompanionState): void { this.#state = state; }
  setAppearance(appearanceId: string): void { this.#appearanceId = appearanceId; }
  setFallback(value: boolean): void { this.#fallback = value; }
  async show(): Promise<BrowserWindow> {
    if (this.#window && !this.#window.isDestroyed()) { this.#window.show(); return this.#window; }
    const area = screen.getPrimaryDisplay().workArea;
    const bounds = clampBounds({ x: area.x + area.width - 196, y: area.y + area.height - 196, width: 176, height: 176 }, area);
    this.#window = new BrowserWindow({
      ...bounds,
      title: "毛毛",
      frame: this.#fallback,
      transparent: !this.#fallback,
      ...(this.#fallback ? { backgroundColor: "#1f2937" } : {}),
      alwaysOnTop: false,
      show: false,
      webPreferences: secureWebPreferences(this.preloadPath)
    });
    this.#window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
    this.#window.webContents.on("will-navigate", (event) => event.preventDefault());
    if (COMPANION_WINDOW_VITE_DEV_SERVER_URL) await this.#window.loadURL(COMPANION_WINDOW_VITE_DEV_SERVER_URL);
    else await this.#window.loadFile(path.join(__dirname, `../renderer/${COMPANION_WINDOW_VITE_NAME}/index.html`));
    this.#window.once("ready-to-show", () => this.#window?.show());
    this.#window.on("closed", () => { this.#window = null; });
    return this.#window;
  }
  hide(): void { this.#window?.hide(); }
  toggle(): void { if (this.#window?.isVisible()) this.hide(); else void this.show(); }
  setAlwaysOnTop(value: boolean): void { this.#window?.setAlwaysOnTop(value); }
}
