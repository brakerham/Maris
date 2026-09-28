import { createHash, randomUUID } from "node:crypto";
import { SecureStore } from "./secure-store";

export type OutboxEntry = Readonly<{
  draftId: string; clientEventId: string; body: string; digest: string;
  state: "draft" | "queued" | "sending" | "terminal"; createdAt: number; updatedAt: number;
}>;
export interface OutboxBlobPort { read(): Promise<Buffer | null>; write(value: Buffer): Promise<void>; }

export class EncryptedOutbox {
  #entries: OutboxEntry[] = [];
  constructor(private readonly storage: OutboxBlobPort, private readonly crypto: SecureStore, private readonly now = () => Date.now(), private readonly makeId: () => string = randomUUID) {}
  async load(): Promise<void> { const blob = await this.storage.read(); this.#entries = blob ? this.crypto.open<OutboxEntry[]>(blob) : []; }
  list(): readonly OutboxEntry[] { return Object.freeze([...this.#entries]); }
  async prepare(draftId: string, body: string): Promise<OutboxEntry> {
    const digest = createHash("sha256").update(body, "utf8").digest("hex");
    const existing = this.#entries.find((item) => item.draftId === draftId && item.digest === digest && item.state !== "terminal");
    if (existing) return existing;
    if (this.#entries.filter((item) => item.state !== "terminal").length >= 20) throw new Error("outbox_capacity_reached");
    const entry: OutboxEntry = { draftId, clientEventId: this.makeId(), body, digest, state: "queued", createdAt: this.now(), updatedAt: this.now() };
    this.#entries.push(entry); await this.#save(); return entry;
  }
  async setState(clientEventId: string, state: OutboxEntry["state"]): Promise<void> {
    this.#entries = this.#entries.map((item) => item.clientEventId === clientEventId ? { ...item, state, updatedAt: this.now() } : item);
    await this.#save();
  }
  async cleanup(): Promise<void> {
    const terminalCutoff = this.now() - 86_400_000; const draftCutoff = this.now() - 2_592_000_000;
    this.#entries = this.#entries.filter((item) => item.state === "terminal" ? item.updatedAt >= terminalCutoff : item.createdAt >= draftCutoff);
    await this.#save();
  }
  async #save(): Promise<void> { await this.storage.write(this.crypto.seal(this.#entries)); }
}
