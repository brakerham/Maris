export const backendStates = [
  "starting",
  "online",
  "offline",
  "recovering",
  "failed",
  "stopping",
  "stopped"
] as const;

export type BackendState = (typeof backendStates)[number];

export type RuntimeSnapshot = Readonly<{
  state: BackendState;
  mode: "managed" | "external_dev";
  authenticated: boolean;
  errorCode: string | null;
}>;

export type WindowAction =
  | "show_main"
  | "focus_main"
  | "hide_main"
  | "toggle_companion";

export type Theme = "system" | "light" | "dark" | "high_contrast";
export type HostModuleSummary = Readonly<{
  module_id: string; version: string; display_name: string; enabled: boolean; profile_ids: readonly string[];
  api_prefixes: readonly string[]; settings_schema_version: number;
}>;

export interface MarisBridge {
  runtime: {
    getSnapshot(): Promise<RuntimeSnapshot>;
    recover(): Promise<RuntimeSnapshot>;
    subscribe(listener: (snapshot: RuntimeSnapshot) => void): () => void;
  };
  window: {
    perform(action: WindowAction): Promise<{ accepted: true }>;
  };
  modules: { list(): Promise<readonly HostModuleSummary[]> };
  settings: { update(value: Readonly<{ theme?: Theme; reducedMotion?: boolean; privacyMode?: boolean }>): Promise<{ accepted: true }> };
  outbox: { enqueue(value: Readonly<{ draftId: string; body: string }>): Promise<{ clientEventId: string }> };
  external: { open(linkId: "privacy"): Promise<{ accepted: true }> };
}

export interface CompanionBridge {
  getState(): Promise<{ state: "idle" | "listening" | "thinking" | "tool" | "needs_confirmation" | "error" | "offline"; appearanceId: string }>;
  openMain(): Promise<{ accepted: true }>;
}
