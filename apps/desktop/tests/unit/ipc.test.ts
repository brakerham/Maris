import { describe, expect, it } from "vitest";
import { validateIpc } from "../../electron/main/ipc-contract";

function fixture(url="file:///app/index.html") {
  const frame = { url }; const contents = { mainFrame: frame }; const window = { webContents: contents };
  return { event:{ sender:contents, senderFrame:frame }, window } as any;
}
describe("IPC validation", () => {
  it("accepts exact main-frame sender and strict schema", () => { const {event,window}=fixture(); expect(validateIpc(event,window,"window:perform@1",["show_main"])).toEqual(["show_main"]); });
  it("rejects unknown action, extra args, origin, subframe, and sender", () => {
    const {event,window}=fixture();
    expect(() => validateIpc(event,window,"window:perform@1",["destroy"])).toThrow();
    expect(() => validateIpc(event,window,"runtime:get-snapshot@1",[1])).toThrow();
    expect(() => validateIpc(fixture("https://evil.invalid").event,window,"runtime:get-snapshot@1",[])).toThrow("ipc_sender_rejected");
    expect(() => validateIpc({...event,senderFrame:{url:"file:///app/frame.html"}},window,"runtime:get-snapshot@1",[])).toThrow("ipc_sender_rejected");
    expect(() => validateIpc({...event,sender:{}},window,"runtime:get-snapshot@1",[])).toThrow("ipc_sender_rejected");
  });
  it("rejects extra object fields", () => { const {event,window}=fixture(); expect(() => validateIpc(event,window,"settings:update@1",[{theme:"dark",token:"secret"}])).toThrow(); });
});
