import { describe, expect, it } from "vitest";
import { DesktopCompositionRoot } from "../../electron/main/composition-root";
import { dailyFinanceContribution } from "../../src/modules/daily-finance/contribution";
import { compileRegistry } from "../../src/modules/registry";

it("single-flights composition, intersects modules, publishes safe state, and shuts down once", async () => {
  let starts=0; let stops=0; let establishes=0; let flushes=0; let listener:()=>void=()=>{};
  const supervisor:any={snapshot:()=>({state:starts?"online":"stopped",mode:"managed",authenticated:false,errorCode:null}),subscribe:(value:()=>void)=>{listener=value;return()=>{};},start:async()=>{starts++;await Promise.resolve();return {state:"online",mode:"managed",authenticated:false,errorCode:null};},recover:async()=>({state:"online",mode:"managed",authenticated:false,errorCode:null}),shutdown:async()=>{stops++;},endpoint:()=>new URL("http://127.0.0.1:41000")};
  const owner:any={safeState:"authenticated",establish:async()=>{establishes++;await Promise.resolve();return "authenticated";},accessToken:()=>"a".repeat(48),refresh:async()=>"a".repeat(48),revoke:async()=>{}};
  const host:any={setAccessToken:()=>{},modules:async()=>[{module_id:"daily_finance",version:"1.0.0",display_name:"Daily Finance",enabled:true,profile_ids:["daily_finance.default"],api_prefixes:["/api/v1/finance"],settings_schema_version:1},{module_id:"unknown",version:"1.0.0",display_name:"Unknown",enabled:true,profile_ids:["unknown.default"],api_prefixes:["/api/v1/unknown"],settings_schema_version:1}]};
  const root=new DesktopCompositionRoot(supervisor,owner,host,compileRegistry([dailyFinanceContribution]),async()=>{flushes++;});
  let publications=0; root.subscribe(()=>{publications++;});
  const [a,b]=await Promise.all([root.start(),root.start()]); expect(a.authenticated).toBe(true); expect(b.authenticated).toBe(true); expect(starts).toBe(1); expect(establishes).toBe(1); expect(root.modules().map((item)=>item.module_id)).toEqual(["daily_finance"]);
  listener(); expect(publications).toBeGreaterThan(0);
  await Promise.all([root.shutdown(),root.shutdown()]); expect(stops).toBe(1); expect(flushes).toBe(1);
});
