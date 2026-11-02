import { createHash, randomUUID } from "node:crypto";
import { SecureStore } from "./secure-store";

export type OutboxEntry = Readonly<{
  draftId: string; clientEventId: string; body: string; digest: string;
  state: "draft" | "queued" | "sending" | "terminal"; createdAt: number; updatedAt: number;
}>;
export interface OutboxBlobPort { read(): Promise<Buffer | null>; write(value: Buffer): Promise<void>; }

export class EncryptedOutbox {
  #entries: OutboxEntry[] = [];
  #tail: Promise<unknown> = Promise.resolve();
  constructor(private readonly storage: OutboxBlobPort, private readonly crypto: SecureStore, private readonly now = () => Date.now(), private readonly makeId: () => string = randomUUID) {}
  load(): Promise<void> { return this.#serialize(async () => { const blob = await this.storage.read(); this.#entries = (blob ? this.crypto.open<OutboxEntry[]>(blob) : []).map((entry) => Object.freeze({ ...entry })); }); }
  list(): readonly OutboxEntry[] { return Object.freeze([...this.#entries]); }
  async prepare(draftId: string, body: string): Promise<OutboxEntry> {
    return this.#serialize(async () => {
      const digest = createHash("sha256").update(body, "utf8").digest("hex");
      const existing = this.#entries.find((item) => item.draftId === draftId && item.digest === digest && item.state !== "terminal");
      if (existing) return existing;
      if (this.#entries.filter((item) => item.state !== "terminal").length >= 20) throw new Error("outbox_capacity_reached");
      const timestamp = this.now();
      const entry: OutboxEntry = Object.freeze({ draftId, clientEventId: this.makeId(), body, digest, state: "queued", createdAt: timestamp, updatedAt: timestamp });
      await this.#save([...this.#entries, entry]); return entry;
    });
  }
  async setState(clientEventId: string, state: OutboxEntry["state"]): Promise<void> {
    return this.#serialize(async () => {
      const entries = this.#entries.map((item) => item.clientEventId === clientEventId ? Object.freeze({ ...item, state, updatedAt: this.now() }) : item);
      await this.#save(entries);
    });
  }
  async cleanup(): Promise<void> {
    return this.#serialize(async () => {
      const terminalCutoff = this.now() - 86_400_000;
      await this.#save(this.#entries.filter((item) => item.state !== "terminal" || item.updatedAt >= terminalCutoff));
    });
  }
  retentionCandidates(): Promise<readonly OutboxEntry[]> {
    return this.#serialize(async () => Object.freeze(this.#entries.filter((item) => this.#stale(item))));
  }
  deleteConfirmed(candidates: readonly OutboxEntry[], isActive = () => true): Promise<number> {
    return this.#serialize(async () => {
      if (!isActive()) return 0;
      // Frozen object identity binds consent to the exact entries shown. Every
      // state update and reload replaces identity, including same-clock updates.
      const shown = new Set(candidates);
      const entries = this.#entries.filter((item) => !shown.has(item) || !this.#stale(item));
      const removed = this.#entries.length - entries.length;
      if (removed) await this.#save(entries);
      return removed;
    });
  }
  #stale(entry: OutboxEntry): boolean {
    return (entry.state === "draft" || entry.state === "queued") && this.now() - entry.createdAt > 2_592_000_000;
  }
  #serialize<T>(operation: () => Promise<T>): Promise<T> {
    const result = this.#tail.then(operation);
    this.#tail = result.catch(() => undefined);
    return result;
  }
  async #save(entries: OutboxEntry[]): Promise<void> {
    await this.storage.write(this.crypto.seal(entries));
    this.#entries = entries;
  }
}
