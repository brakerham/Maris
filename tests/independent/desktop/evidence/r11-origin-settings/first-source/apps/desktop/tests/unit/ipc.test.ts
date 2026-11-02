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

describe("R9 real validateIpc origin checks", () => {
  it("R9 original counterexample changes only the same mainFrame URL", () => {
    const { event, window } = fixture("http://127.0.0.1:5173/index.html");
    const origin = "http://127.0.0.1:5173";
    expect(validateIpc(event, window, "settings:get-snapshot@1", [], origin)).toEqual([]);
    event.senderFrame.url = "http://127.0.0.1:51730/index.html";
    expect(event.senderFrame).toBe(window.webContents.mainFrame);
    expect(event.sender).toBe(window.webContents);
    expect(() => validateIpc(event, window, "settings:get-snapshot@1", [], origin)).toThrow("ipc_origin_rejected");
  });

  it.each(["http://127.0.0.1:51730/", "https://127.0.0.1:5173/", "http://localhost:5173/",
    "http://user@127.0.0.1:5173/", "blob:http://127.0.0.1:5173/id", "/relative", "http://[broken"])
  ("rejects the actual main-frame origin before parameter parsing: %s", url => {
    const { event, window } = fixture(url);
    expect(() => validateIpc(event, window, "settings:update@1", [{ token: "virtual" }], "http://127.0.0.1:5173"))
      .toThrow("ipc_origin_rejected");
  });

  it("preserves sender priority and strict getter/update contracts at a trusted origin", () => {
    const { event, window } = fixture("http://localhost:5173/other?q=1#settings");
    const origin = "http://localhost:5173/";
    expect(() => validateIpc({ ...event, sender: {} }, window, "settings:get-snapshot@1", [1], origin)).toThrow("ipc_sender_rejected");
    expect(() => validateIpc({ ...event, senderFrame: { url: event.senderFrame.url } }, window, "settings:get-snapshot@1", [], origin)).toThrow("ipc_sender_rejected");
    expect(() => validateIpc(event, window, "settings:get-snapshot@1", [1], origin)).toThrow();
    expect(validateIpc(event, window, "settings:update@1", [{ theme: "dark", privacyMode: true, reducedMotion: false }], origin))
      .toEqual([{ theme: "dark", privacyMode: true, reducedMotion: false }]);
    expect(() => validateIpc(event, window, "settings:update@1", [{ theme: "dark", closePolicy: "quit" }], origin)).toThrow();
  });
});
