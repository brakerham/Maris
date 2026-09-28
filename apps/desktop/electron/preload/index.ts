import { contextBridge, ipcRenderer } from "electron";
import type { HostModuleSummary, MarisBridge, RuntimeSnapshot, Theme, WindowAction } from "../../src/shared/contracts";

const bridge: MarisBridge = {
  runtime: {
    getSnapshot: () => ipcRenderer.invoke("runtime:get-snapshot@1") as Promise<RuntimeSnapshot>,
    recover: () => ipcRenderer.invoke("runtime:recover@1") as Promise<RuntimeSnapshot>,
    subscribe: (listener) => {
      const handler = (_event: Electron.IpcRendererEvent, value: RuntimeSnapshot) => listener(value);
      ipcRenderer.on("runtime:state@1", handler);
      return () => ipcRenderer.removeListener("runtime:state@1", handler);
    }
  },
  window: {
    perform: (action: WindowAction) => ipcRenderer.invoke("window:perform@1", action)
  },
  modules: { list: () => ipcRenderer.invoke("modules:list@1") as Promise<readonly HostModuleSummary[]> },
  settings: { update: (value: { theme?: Theme; reducedMotion?: boolean; privacyMode?: boolean }) => ipcRenderer.invoke("settings:update@1", value) },
  outbox: { enqueue: (value: { draftId: string; body: string }) => ipcRenderer.invoke("outbox:enqueue@1", value) },
  external: { open: (linkId: "privacy") => ipcRenderer.invoke("external:open@1", linkId) }
};

contextBridge.exposeInMainWorld("maris", Object.freeze(bridge));
