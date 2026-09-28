import type { DesktopModuleContribution } from "../../src/modules/registry";
import { intersectModules } from "../../src/modules/registry";
import type { HostModuleSummary, RuntimeSnapshot } from "../../src/shared/contracts";
import { BackendSupervisor } from "./backend-supervisor";
import { DesktopError } from "./desktop-error";
import { HostClient } from "./host-client";
import { LocalOwnerSession } from "./owner-session";

type Publisher = (snapshot: RuntimeSnapshot) => void;

export class DesktopCompositionRoot {
  #modules: readonly HostModuleSummary[] = Object.freeze([]);
  #flight: Promise<RuntimeSnapshot> | null = null;
  #shutdownFlight: Promise<void> | null = null;
  #listeners = new Set<Publisher>();

  constructor(
    readonly supervisor: BackendSupervisor,
    readonly ownerSession: LocalOwnerSession,
    readonly hostClient: HostClient,
    private readonly compiledRegistry: readonly DesktopModuleContribution[],
    private readonly flush: () => Promise<void> = async () => undefined
  ) {
    supervisor.subscribe(() => this.#publish());
  }

  snapshot(): RuntimeSnapshot {
    const backend = this.supervisor.snapshot();
    const ownerState = this.ownerSession.safeState;
    return {
      ...backend,
      authenticated: ownerState === "authenticated",
      errorCode: ownerState === "needs_repair" ? "needs_repair" : backend.errorCode,
    };
  }

  modules(): readonly HostModuleSummary[] { return this.#modules; }

  subscribe(listener: Publisher): () => void {
    this.#listeners.add(listener);
    return () => this.#listeners.delete(listener);
  }

  start(): Promise<RuntimeSnapshot> { return this.#singleFlight(() => this.#connect(false)); }

  recover(): Promise<RuntimeSnapshot> { return this.#singleFlight(() => this.#connect(true)); }

  shutdown(): Promise<void> {
    this.#shutdownFlight ??= (async () => {
      this.#modules = Object.freeze([]);
      this.hostClient.setAccessToken(null);
      await this.flush().catch(() => undefined);
      await this.supervisor.shutdown();
      this.#publish();
    })();
    return this.#shutdownFlight;
  }

  #singleFlight(operation: () => Promise<RuntimeSnapshot>): Promise<RuntimeSnapshot> {
    if (this.#flight) return this.#flight;
    const flight = operation().finally(() => {
      if (this.#flight === flight) this.#flight = null;
    });
    this.#flight = flight;
    return flight;
  }

  async #connect(recover: boolean): Promise<RuntimeSnapshot> {
    const backend = recover ? await this.supervisor.recover() : await this.supervisor.start();
    this.#modules = Object.freeze([]);
    if (backend.state !== "online") { this.#publish(); return this.snapshot(); }

    const ownerState = await this.ownerSession.establish();
    if (ownerState !== "authenticated") { this.#publish(); return this.snapshot(); }
    this.hostClient.setAccessToken(this.ownerSession.accessToken());
    try {
      const hostModules = await this.hostClient.modules();
      const available = new Set(intersectModules(this.compiledRegistry, hostModules).map((item) => item.moduleId));
      this.#modules = Object.freeze(hostModules.filter((item) => available.has(item.module_id)));
    } catch (error) {
      this.#modules = Object.freeze([]);
      if (error instanceof DesktopError && error.code === "session_expired") await this.ownerSession.revoke();
    }
    this.#publish();
    return this.snapshot();
  }

  #publish(): void {
    const snapshot = this.snapshot();
    for (const listener of this.#listeners) listener(snapshot);
  }
}
