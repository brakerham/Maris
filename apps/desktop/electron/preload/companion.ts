import { contextBridge, ipcRenderer } from "electron";
import type { CompanionBridge } from "../../src/shared/contracts";

const companion: CompanionBridge = Object.freeze({
  getState: () => ipcRenderer.invoke("companion:get-state@1"),
  openMain: () => ipcRenderer.invoke("companion:open-main@1")
});
contextBridge.exposeInMainWorld("companion", companion);
