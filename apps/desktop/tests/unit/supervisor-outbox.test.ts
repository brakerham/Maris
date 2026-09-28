import { createHash } from "node:crypto"; import { describe, expect, it } from "vitest";
import { BackendSupervisor } from "../../electron/main/backend-supervisor";
import { EncryptedOutbox } from "../../electron/main/outbox"; import { SecureStore } from "../../electron/main/secure-store";

it("single-flights managed start, validates identity, and makes stop idempotent", async () => {
  let starts=0; let stopped=0;
  const port:any={delay:async()=>{},ready:async()=>true,health:async()=>true,baseUrl:(child:any)=>new URL(`http://127.0.0.1:${child.port}`),start:async({instanceId,nonce}:any)=>{starts++;await Promise.resolve();return {instanceId,nonceDigest:createHash("sha256").update(nonce).digest("hex"),port:41000,handle:{},stop:async()=>{stopped++;},forceStopTree:async()=>{stopped+=10;}}}};
  const managed=new BackendSupervisor("managed",port,()=>1000);
  const [first,second]=await Promise.all([managed.start(),managed.start()]); expect(first.state).toBe("online"); expect(second.state).toBe("online"); expect(starts).toBe(1);
  expect((await managed.stop()).state).toBe("stopped"); expect((await managed.stop()).state).toBe("stopped"); expect(stopped).toBe(1);
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
