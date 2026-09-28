import { describe, expect, it } from "vitest";
import { LocalOwnerSession } from "../../electron/main/owner-session";

it("creates local owner safely and single-flights establish and refresh", async () => {
  let stored:any=null; let refreshes=0; let staged=false; let logins=0;
  const secrets={read:async()=>stored,stage:async(v:any)=>{staged=true;stored={...v,refreshToken:null,repairRequired:false};},commit:async(v:any)=>{stored={...v,repairRequired:false};},markRepair:async()=>{stored={...stored,repairRequired:true};}};
  const host={bootstrapStatus:async()=>({needsInitialization:true}),initialize:async()=>{expect(staged).toBe(true);},login:async()=>{logins++;await Promise.resolve();return {accessToken:"access",refreshToken:"refresh"};},refresh:async()=>{refreshes++;await Promise.resolve();return {accessToken:"next",refreshToken:"rotated"};}};
  const session=new LocalOwnerSession(host,secrets,()=>({handle:"local_owner",password:"virtual-password-123"})); expect(await Promise.all([session.establish(),session.establish()])).toEqual(["authenticated","authenticated"]); expect(logins).toBe(1); expect(session.accessToken()).toBe("access");
  const [a,b]=await Promise.all([session.refresh(),session.refresh()]); expect([a,b]).toEqual(["next","next"]); expect(refreshes).toBe(1); await session.revoke(); expect(await session.establish()).toBe("needs_repair");
});
