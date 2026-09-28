import { z } from "zod";
import type { BrowserWindow, IpcMainInvokeEvent } from "electron";
import { isTrustedRenderer } from "./security";

export const ipcRequests = {
  "runtime:get-snapshot@1": z.tuple([]),
  "runtime:recover@1": z.tuple([]),
  "window:perform@1": z.tuple([z.enum(["show_main", "focus_main", "hide_main", "toggle_companion"])]),
  "external:open@1": z.tuple([z.enum(["privacy"])]),
  "modules:list@1": z.tuple([]),
  "settings:update@1": z.tuple([z.strictObject({ theme: z.enum(["system", "light", "dark", "high_contrast"]).optional(), reducedMotion: z.boolean().optional(), privacyMode: z.boolean().optional() })]),
  "outbox:enqueue@1": z.tuple([z.strictObject({ draftId: z.string().uuid(), body: z.string().min(1).max(8000) })])
  ,"companion:get-state@1": z.tuple([])
  ,"companion:open-main@1": z.tuple([])
} as const;
export type IpcChannel = keyof typeof ipcRequests;

export function validateIpc(
  event: Pick<IpcMainInvokeEvent, "sender" | "senderFrame">,
  expectedWindow: BrowserWindow,
  channel: IpcChannel,
  args: readonly unknown[],
  developmentOrigin?: string
): unknown[] {
  if (event.sender !== expectedWindow.webContents || event.senderFrame !== expectedWindow.webContents.mainFrame) throw new Error("ipc_sender_rejected");
  if (!isTrustedRenderer(event.senderFrame.url, developmentOrigin)) throw new Error("ipc_origin_rejected");
  return ipcRequests[channel].parse(args);
}
