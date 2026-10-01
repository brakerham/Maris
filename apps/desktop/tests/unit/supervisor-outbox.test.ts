import { createHash } from "node:crypto"; import { describe, expect, it } from "vitest";
import { BackendSupervisor } from "../../electron/main/backend-supervisor";
import { EncryptedOutbox, type OutboxEntry } from "../../electron/main/outbox"; import { SecureStore } from "../../electron/main/secure-store";

it("single-flights managed start, validates identity, and makes stop idempotent", async () => {
  let starts=0; let stopped=0;
  const port:any={delay:async()=>{},ready:async()=>true,health:async()=>true,baseUrl:(child:any)=>new URL(`http://127.0.0.1:${child.port}`),start:async({instanceId,nonce}:any)=>{starts++;await Promise.resolve();return {instanceId,nonceDigest:createHash("sha256").update(nonce).digest("hex"),port:41000,handle:{},stop:async()=>{stopped++;},forceStopTree:async()=>{stopped+=10;}}}};
  const managed=new BackendSupervisor("managed",port,()=>1000);
  const [first,second]=await Promise.all([managed.start(),managed.start()]); expect(first.state).toBe("online"); expect(second.state).toBe("online"); expect(starts).toBe(1);
  expect((await managed.stop()).state).toBe("stopped"); expect((await managed.stop()).state).toBe("stopped"); expect(stopped).toBe(1);
});

const day = 86_400_000;
function outboxFixture() {
  let time = 100 * day; let blob: Buffer | null = null; let ids = 0; let fail = false;
  const secure = new SecureStore({ isEncryptionAvailable: () => true, encryptString: (v) => Buffer.from(v).reverse(), decryptString: (v) => Buffer.from(v).reverse().toString() });
  const storage = { read: async () => blob, write: async (v: Buffer) => { if (fail) throw new Error("virtual_write_failure"); blob = v; } };
  const make = () => new EncryptedOutbox(storage, secure, () => time, () => `virtual-${++ids}`);
  return { make, time: (v: number) => { time = v; }, fail: (v: boolean) => { fail = v; }, seed: (entries: OutboxEntry[]) => { blob = secure.seal(entries); }, persisted: () => blob ? secure.open<OutboxEntry[]>(blob) : [] };
}
function oldEntry(state: OutboxEntry["state"], age: number, id = `${state}-${age}`): OutboxEntry {
  return { draftId: id, clientEventId: id, body: "virtual-private-body", digest: createHash("sha256").update("virtual-private-body").digest("hex"), state, createdAt: 100 * day - age, updatedAt: 100 * day - age };
}

describe("outbox retention and transactional persistence", () => {
  it.each(["draft", "queued", "sending"] as const)("retains %s at 30 days, +1ms and far beyond across startup/shutdown/reload", async (state) => {
    const f = outboxFixture(); const entries = [30 * day, 30 * day + 1, 300 * day].map((age) => oldEntry(state, age)); f.seed(entries);
    const box = f.make(); await box.load(); await box.cleanup(); await box.cleanup();
    const restarted = f.make(); await restarted.load(); expect(restarted.list()).toEqual(entries); expect(f.persisted()).toEqual(entries);
    expect((await restarted.retentionCandidates()).map((entry) => entry.clientEventId)).toEqual(state === "sending" ? [] : entries.slice(1).map((entry) => entry.clientEventId));
  });
  it("only expires terminal strictly beyond 24h", async () => {
    const f = outboxFixture(); const boundary = oldEntry("terminal", day); f.seed([boundary, oldEntry("terminal", day + 1), oldEntry("sending", 1000 * day)]);
    const box = f.make(); await box.load(); await box.cleanup(); expect(box.list()).toEqual([boundary, oldEntry("sending", 1000 * day)]);
    const restarted = f.make(); await restarted.load(); expect(restarted.list()).toEqual(box.list());
  });
  it("deletes only unchanged shown candidates, preserves concurrent changes and bounds repeated confirmation", async () => {
    const f = outboxFixture(); f.seed([oldEntry("draft", 40 * day, "delete"), oldEntry("queued", 40 * day, "changed"), oldEntry("queued", 40 * day, "same-clock"), oldEntry("sending", 40 * day, "sending"), oldEntry("draft", 30 * day, "fresh")]);
    const box = f.make(); await box.load(); const shown = await box.retentionCandidates(); expect(Object.isFrozen(shown)).toBe(true); expect(shown.every(Object.isFrozen)).toBe(true);
    await Promise.all([box.prepare("new", "virtual-new"), box.setState("changed", "sending"), box.setState("same-clock", "queued")]);
    expect(await box.deleteConfirmed(shown)).toBe(1); expect(await box.deleteConfirmed(shown)).toBe(0);
    expect(box.list().map((entry) => entry.clientEventId)).toEqual(["changed", "same-clock", "sending", "fresh", "virtual-1"]);
    const restarted = f.make(); await restarted.load(); expect(restarted.list()).toEqual(box.list());
  });
  it("invalidates consent on reload and protects candidates changed while deletion waits in the queue", async () => {
    const f = outboxFixture(); f.seed([oldEntry("draft", 40 * day)]); const box = f.make(); await box.load(); const shown = await box.retentionCandidates();
    await box.load(); expect(await box.deleteConfirmed(shown)).toBe(0);
    const current = await box.retentionCandidates(); const mutation = box.setState(current[0]!.clientEventId, "sending"); const deletion = box.deleteConfirmed(current);
    await mutation; expect(await deletion).toBe(0);
  });
  it("does not publish failed prepare/state/cleanup/deletion and recovers its serialized queue", async () => {
    const f = outboxFixture(); f.seed([oldEntry("queued", 40 * day), oldEntry("terminal", day + 1)]); const box = f.make(); await box.load(); const before = box.list(); const shown = await box.retentionCandidates(); f.fail(true);
    await expect(box.prepare("new", "virtual-new")).rejects.toThrow("virtual_write_failure");
    await expect(box.setState(before[0]!.clientEventId, "sending")).rejects.toThrow("virtual_write_failure");
    await expect(box.cleanup()).rejects.toThrow("virtual_write_failure");
    await expect(box.deleteConfirmed(shown)).rejects.toThrow("virtual_write_failure");
    expect(box.list()).toEqual(before); const restarted = f.make(); await restarted.load(); expect(restarted.list()).toEqual(before);
    f.fail(false); expect(await box.deleteConfirmed(shown)).toBe(1); await box.cleanup(); await box.prepare("recovery", "virtual-recovery"); expect(box.list()).toHaveLength(1); expect(f.persisted()).toEqual(box.list());
  });
  it("serializes simultaneous writes and capacity checks without silently evicting expired messages", async () => {
    const f = outboxFixture(); f.seed(Array.from({ length: 19 }, (_, i) => oldEntry("queued", 300 * day, `old-${i}`))); const box = f.make(); await box.load(); await box.cleanup();
    const results = await Promise.allSettled([box.prepare("a", "virtual-a"), box.prepare("b", "virtual-b"), box.cleanup()]);
    expect(results.map((result) => result.status)).toEqual(["fulfilled", "rejected", "fulfilled"]); expect(box.list()).toHaveLength(20); expect(f.persisted()).toEqual(box.list());
  });
  it("keeps pending writes unpublished and prevents concurrent lost updates", async () => {
    let blob: Buffer | null = null; let release!: () => void; let writes = 0;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const secure = new SecureStore({ isEncryptionAvailable: () => true, encryptString: (v) => Buffer.from(v).reverse(), decryptString: (v) => Buffer.from(v).reverse().toString() });
    const storage = { read: async () => blob, write: async (value: Buffer) => { writes++; if (writes === 1) await gate; blob = value; } };
    let ids = 0; const box = new EncryptedOutbox(storage, secure, () => 1, () => `virtual-${++ids}`);
    const first = box.prepare("first", "virtual-first"); const second = box.prepare("second", "virtual-second");
    await Promise.resolve(); await Promise.resolve(); expect(writes).toBe(1); expect(box.list()).toEqual([]);
    release(); await Promise.all([first, second]); expect(writes).toBe(2); expect(box.list()).toHaveLength(2);
    const restarted = new EncryptedOutbox(storage, secure); await restarted.load(); expect(restarted.list()).toEqual(box.list());
  });
  it("preserves retry IDs but allocates a new ID for changed sending content", async () => {
    const f = outboxFixture(); const box = f.make(); const first = await box.prepare("draft", "virtual-first"); await box.setState(first.clientEventId, "sending");
    expect((await box.prepare("draft", "virtual-first")).clientEventId).toBe(first.clientEventId);
    expect((await box.prepare("draft", "virtual-edited")).clientEventId).not.toBe(first.clientEventId);
  });
});
it("cleans a managed child that fails readiness and never stops external dev", async () => {
  let stopped=0; const child=(instanceId:string,nonce:string)=>({instanceId,nonceDigest:createHash("sha256").update(nonce).digest("hex"),port:41001,handle:{},stop:async()=>{stopped++;},forceStopTree:async()=>{stopped+=10;}});
  const port:any={delay:async()=>{},ready:async()=>false,health:async()=>true,baseUrl:(value:any)=>new URL(`http://127.0.0.1:${value.port}`),start:async({instanceId,nonce}:any)=>child(instanceId,nonce),observeExternal:async()=>child("00000000-0000-4000-8000-000000000000","x")};
  const managed=new BackendSupervisor("managed",port); expect((await managed.start()).state).toBe("failed"); expect(stopped).toBe(1);
  const external=new BackendSupervisor("external_dev",port,()=>Date.now(),"x".repeat(32)); expect((await external.start()).state).toBe("online"); await external.stop(); expect(stopped).toBe(1);
});
it("outbox preserves IDs across retry and restart, rejects overflow, and encrypts body", async () => {
  let blob:Buffer|null=null; let ids=0; const storage={read:async()=>blob,write:async(v:Buffer)=>{blob=v;}}; const secure=new SecureStore({isEncryptionAvailable:()=>true,encryptString:(v)=>Buffer.from(v).reverse(),decryptString:(v)=>Buffer.from(v).reverse().toString()});
  const box=new EncryptedOutbox(storage,secure,()=>1,()=>`id-${++ids}`); await box.load(); const first=await box.prepare("00000000-0000-4000-8000-000000000001","virtual message"); expect((await box.prepare(first.draftId,"virtual message")).clientEventId).toBe(first.clientEventId); expect(blob!.toString()).not.toContain("virtual message");
  const restarted=new EncryptedOutbox(storage,secure,()=>2,()=>`id-${++ids}`); await restarted.load(); expect((await restarted.prepare(first.draftId,"virtual message")).clientEventId).toBe(first.clientEventId);
  for(let i=2;i<=20;i++) await restarted.prepare(`00000000-0000-4000-8000-${String(i).padStart(12,"0")}`,`body-${i}`); await expect(restarted.prepare("00000000-0000-4000-8000-000000000021","overflow")).rejects.toThrow("outbox_capacity_reached");
});
