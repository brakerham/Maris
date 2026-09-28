import { createHash, randomBytes, randomUUID, timingSafeEqual } from "node:crypto";
import type { BackendState, RuntimeSnapshot } from "../../src/shared/contracts";

export interface OwnedChild {
  readonly instanceId: string;
  readonly nonceDigest: string;
  readonly port: number;
  readonly handle: object;
  stop(): Promise<void>;
  forceStopTree(): Promise<void>;
  onExit?(listener: () => void): () => void;
}

export interface SupervisorPort {
  start(input: { instanceId: string; nonce: string }): Promise<OwnedChild>;
  ready(child: OwnedChild, nonce: string, timeoutMs: number): Promise<boolean>;
  health(child: OwnedChild): Promise<boolean>;
  baseUrl(child: OwnedChild): URL;
  delay(ms: number): Promise<void>;
  observeExternal?(nonce: string, timeoutMs: number): Promise<OwnedChild>;
}

type SnapshotListener = (snapshot: RuntimeSnapshot) => void;

export class BackendSupervisor {
  #state: BackendState = "stopped";
  #errorCode: string | null = null;
  #owned: OwnedChild | null = null;
  #flight: Promise<RuntimeSnapshot> | null = null;
  #recoveries: number[] = [];
  #listeners = new Set<SnapshotListener>();
  #healthTimer: ReturnType<typeof setInterval> | null = null;
  #healthBusy = false;
  #healthFailures = 0;
  #onlineSince: number | null = null;
  #acceptRecovery = true;
  #removeExitListener: (() => void) | null = null;

  constructor(
    private readonly mode: "managed" | "external_dev",
    private readonly port: SupervisorPort,
    private readonly now = () => Date.now(),
    private readonly externalNonce: string | null = null
  ) {}

  snapshot(): RuntimeSnapshot {
    return { state: this.#state, mode: this.mode, authenticated: false, errorCode: this.#errorCode };
  }

  subscribe(listener: SnapshotListener): () => void {
    this.#listeners.add(listener);
    return () => this.#listeners.delete(listener);
  }

  endpoint(): URL {
    if (!this.#owned || this.#state !== "online") throw new Error("backend_not_online");
    return this.port.baseUrl(this.#owned);
  }

  start(): Promise<RuntimeSnapshot> {
    if (this.#flight) return this.#flight;
    if (!this.#acceptRecovery) return Promise.resolve(this.snapshot());
    return this.#run(() => this.#start());
  }

  recover(): Promise<RuntimeSnapshot> {
    if (this.#flight) return this.#flight;
    if (!this.#acceptRecovery) return Promise.resolve(this.snapshot());
    return this.#run(async () => {
      const cutoff = this.now() - 300_000;
      this.#recoveries = this.#recoveries.filter((time) => time >= cutoff);
      if (this.#recoveries.length >= 3) {
        this.#transition("failed", "backend_recovery_exhausted");
        return this.snapshot();
      }
      this.#recoveries.push(this.now());
      this.#transition("recovering", null);
      await this.#stopOwned();
      await this.port.delay(2 ** (this.#recoveries.length - 1) * 1000);
      return this.#start();
    });
  }

  stop(candidate?: OwnedChild): Promise<RuntimeSnapshot> {
    if (this.#flight) return this.#flight.then(() => this.stop(candidate));
    return this.#run(async () => {
      if (this.#state === "stopped" && !this.#owned) return this.snapshot();
      if (candidate && candidate !== this.#owned) {
        this.#transition("failed", "backend_identity_rejected");
        return this.snapshot();
      }
      this.#transition("stopping", null);
      if (this.mode === "managed") await this.#stopOwned();
      else this.#releaseOwned();
      this.#transition("stopped", null);
      return this.snapshot();
    });
  }

  shutdown(): Promise<RuntimeSnapshot> {
    this.#acceptRecovery = false;
    return this.stop();
  }

  #run(operation: () => Promise<RuntimeSnapshot>): Promise<RuntimeSnapshot> {
    const flight = operation().finally(() => {
      if (this.#flight === flight) this.#flight = null;
    });
    this.#flight = flight;
    return flight;
  }

  async #start(): Promise<RuntimeSnapshot> {
    this.#clearHealthLoop();
    this.#transition("starting", null);
    if (this.mode === "external_dev") return this.#startExternal();

    const instanceId = randomUUID();
    const nonceBytes = randomBytes(32);
    const nonce = nonceBytes.toString("base64url");
    const expectedDigest = createHash("sha256").update(nonce, "utf8").digest("hex");
    let child: OwnedChild | null = null;
    try {
      child = await this.port.start({ instanceId, nonce });
      if (child.instanceId !== instanceId || !safeHexEqual(child.nonceDigest, expectedDigest)) {
        await this.#cleanupCandidate(child);
        this.#transition("failed", "backend_identity_rejected");
        return this.snapshot();
      }
      this.#owned = child;
      if (!(await this.port.ready(child, nonce, 30_000))) {
        await this.#stopOwned();
        this.#transition("failed", "backend_not_ready");
        return this.snapshot();
      }
      this.#bindExit(child);
      this.#transition("online", null);
      this.#startHealthLoop(child);
      return this.snapshot();
    } catch {
      if (child && child !== this.#owned) await this.#cleanupCandidate(child);
      else await this.#stopOwned();
      this.#transition("failed", "backend_start_failed");
      return this.snapshot();
    } finally {
      nonceBytes.fill(0);
    }
  }

  async #startExternal(): Promise<RuntimeSnapshot> {
    if (!this.externalNonce || this.externalNonce.length < 32 || !this.port.observeExternal) {
      this.#transition("failed", "backend_identity_rejected");
      return this.snapshot();
    }
    try {
      const observed = await this.port.observeExternal(this.externalNonce, 30_000);
      this.#owned = observed;
      this.#transition("online", null);
      this.#startHealthLoop(observed);
    } catch {
      this.#releaseOwned();
      this.#transition("failed", "backend_not_ready");
    }
    return this.snapshot();
  }

  async #stopOwned(): Promise<void> {
    const owned = this.#owned;
    this.#clearHealthLoop();
    this.#removeExitListener?.();
    this.#removeExitListener = null;
    if (!owned) return;
    if (this.mode !== "managed") {
      this.#releaseOwned();
      return;
    }
    const graceful = owned.stop().then(() => false, () => false);
    const timedOut = await Promise.race([graceful, this.port.delay(5_000).then(() => true)]);
    if (timedOut && this.#owned === owned) await owned.forceStopTree();
    if (this.#owned === owned) this.#owned = null;
  }

  async #cleanupCandidate(child: OwnedChild): Promise<void> {
    if (this.mode !== "managed") return;
    const timedOut = await Promise.race([
      child.stop().then(() => false, () => false),
      this.port.delay(5_000).then(() => true),
    ]);
    if (timedOut) await child.forceStopTree();
  }

  #releaseOwned(): void {
    this.#clearHealthLoop();
    this.#removeExitListener?.();
    this.#removeExitListener = null;
    this.#owned = null;
  }

  #bindExit(child: OwnedChild): void {
    this.#removeExitListener = child.onExit?.(() => {
      if (this.#owned !== child || this.#state === "stopping" || this.#state === "stopped") return;
      this.#releaseOwned();
      this.#transition("offline", "backend_exited");
    }) ?? null;
  }

  #startHealthLoop(child: OwnedChild): void {
    this.#onlineSince = this.now();
    this.#healthFailures = 0;
    this.#healthTimer = setInterval(() => void this.#checkHealth(child), 5_000);
    this.#healthTimer.unref?.();
  }

  async #checkHealth(child: OwnedChild): Promise<void> {
    if (this.#healthBusy || this.#owned !== child || this.#state !== "online") return;
    this.#healthBusy = true;
    try {
      const healthy = await this.port.health(child).catch(() => false);
      if (this.#owned !== child) return;
      this.#healthFailures = healthy ? 0 : this.#healthFailures + 1;
      if (this.#onlineSince !== null && this.now() - this.#onlineSince >= 600_000) this.#recoveries = [];
      if (this.#healthFailures >= 3) {
        this.#clearHealthLoop();
        this.#transition("offline", "backend_health_failed");
      }
    } finally {
      this.#healthBusy = false;
    }
  }

  #clearHealthLoop(): void {
    if (this.#healthTimer) clearInterval(this.#healthTimer);
    this.#healthTimer = null;
    this.#healthFailures = 0;
    this.#onlineSince = null;
  }

  #transition(state: BackendState, errorCode: string | null): void {
    const changed = this.#state !== state || this.#errorCode !== errorCode;
    this.#state = state;
    this.#errorCode = errorCode;
    if (changed) for (const listener of this.#listeners) listener(this.snapshot());
  }
}

function safeHexEqual(left: string, right: string): boolean {
  if (!/^[0-9a-f]{64}$/.test(left) || !/^[0-9a-f]{64}$/.test(right)) return false;
  const a = Buffer.from(left, "hex");
  const b = Buffer.from(right, "hex");
  return a.length === b.length && timingSafeEqual(a, b);
}
