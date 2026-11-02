import { mkdir, open, readFile, rename } from "node:fs/promises";
import path from "node:path";
import { z } from "zod";

const boundsSchema = z.strictObject({ x: z.number(), y: z.number(), width: z.number().positive(), height: z.number().positive(), displayId: z.string().max(128) });
export const deviceSettingsSchema = z.strictObject({
  schemaVersion: z.literal(1),
  backendMode: z.enum(["managed", "external_dev"]),
  closePolicy: z.enum(["hide_to_tray", "ask_every_time", "quit"]),
  closeHintShown: z.boolean(),
  theme: z.enum(["system", "light", "dark", "high_contrast"]),
  reducedMotion: z.boolean(),
  privacyMode: z.boolean(),
  companionVisible: z.boolean(),
  companionAlwaysOnTop: z.boolean(),
  companionAppearance: z.string().max(64),
  companionFallback: z.boolean(),
  mainBounds: boundsSchema.nullable(),
  companionBounds: boundsSchema.nullable(),
  launchAtLogin: z.boolean(),
  externalFullscreenSupported: z.boolean(),
  externalFullscreenEnabled: z.boolean(),
  outboxVersion: z.literal(1)
});
export type DeviceSettings = z.infer<typeof deviceSettingsSchema>;

export const defaultSettings: DeviceSettings = Object.freeze({
  schemaVersion: 1, backendMode: "managed", closePolicy: "hide_to_tray", closeHintShown: false,
  theme: "system", reducedMotion: false, privacyMode: false, companionVisible: true,
  companionAlwaysOnTop: false, companionAppearance: "daily_finance", companionFallback: false,
  mainBounds: null, companionBounds: null, launchAtLogin: false,
  externalFullscreenSupported: false, externalFullscreenEnabled: false, outboxVersion: 1
});

export class DeviceSettingsStore {
  constructor(private readonly file: string) {}

  async load(): Promise<DeviceSettings> {
    try { return deviceSettingsSchema.parse(JSON.parse(await readFile(this.file, "utf8"))); }
    catch { return { ...defaultSettings }; }
  }

  async save(value: DeviceSettings): Promise<void> {
    const valid = deviceSettingsSchema.parse(value);
    await mkdir(path.dirname(this.file), { recursive: true });
    const temporary = `${this.file}.tmp`;
    const handle = await open(temporary, "w", 0o600);
    try { await handle.writeFile(`${JSON.stringify(valid)}\n`, "utf8"); await handle.sync(); }
    finally { await handle.close(); }
    await rename(temporary, this.file);
  }
}
