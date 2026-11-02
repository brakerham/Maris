import type { MarisBridge } from "../shared/contracts";

declare global {
  interface Window {
    maris: MarisBridge;
    companion: import("../shared/contracts").CompanionBridge;
  }
}

export {};
