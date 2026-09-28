import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os"; import path from "node:path";
import { describe, expect, it } from "vitest";
import { defaultSettings, DeviceSettingsStore } from "../../electron/main/device-settings";
import { SecureStore } from "../../electron/main/secure-store";

describe("device and secure storage", () => {
  it("round trips strict settings and falls back from corruption", async () => {
    const dir=await mkdtemp(path.join(tmpdir(),"maris-settings-")); const file=path.join(dir,"settings.json"); const store=new DeviceSettingsStore(file);
    expect(await store.load()).toEqual(defaultSettings); await store.save({...defaultSettings,theme:"dark"}); expect((await store.load()).theme).toBe("dark");
    expect((await readFile(file,"utf8"))).not.toContain("token"); await writeFile(file,"{bad"); expect(await store.load()).toEqual(defaultSettings);
    await expect(store.save({...defaultSettings,token:"no"} as any)).rejects.toThrow();
  });
  it("fails closed without encryption and hides plaintext", () => {
    const unavailable=new SecureStore({isEncryptionAvailable:()=>false,encryptString:()=>Buffer.alloc(0),decryptString:()=>""}); expect(()=>unavailable.seal({x:1})).toThrow("secure_storage_unavailable");
    const available=new SecureStore({isEncryptionAvailable:()=>true,encryptString:(value)=>Buffer.from(value).reverse(),decryptString:(value)=>Buffer.from(value).reverse().toString()}); const sealed=available.seal({password:"virtual-secret"}); expect(sealed.toString()).not.toContain("virtual-secret"); expect(available.open(sealed)).toEqual({password:"virtual-secret"});
  });
});
