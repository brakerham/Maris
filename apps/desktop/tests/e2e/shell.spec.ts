import { _electron as electron, expect, test } from "@playwright/test";

test("packaged shell preserves sandbox and a single companion window", async () => {
  const executablePath=process.env.MARIS_ELECTRON_EXE; if(!executablePath) throw new Error("MARIS_ELECTRON_EXE is required");
  const realExecutable=process.env.MARIS_REAL_EXE==="1"; const packagedApp=process.env.MARIS_PACKAGED_APP; if(!realExecutable&&!packagedApp) throw new Error("MARIS_PACKAGED_APP is required");
  const userData=process.env.MARIS_E2E_USER_DATA; if(!userData) throw new Error("MARIS_E2E_USER_DATA is required");
  const application=await electron.launch({executablePath,args:["--disable-gpu",...(packagedApp?[packagedApp]:[])],env:{...process.env,MARIS_E2E:"1"}});
  try {
    await expect.poll(async()=>Promise.all(application.windows().map((window)=>window.title()))).toContain("Maris");
    const titles=await Promise.all(application.windows().map((window)=>window.title())); expect(titles.filter((title)=>title==="Maris")).toHaveLength(1); expect(titles.filter((title)=>title==="毛毛").length).toBeLessThanOrEqual(1);
    const windows=application.windows(); const windowTitles=await Promise.all(windows.map((window)=>window.title())); const main=windows[windowTitles.indexOf("Maris")] ?? await application.firstWindow();
    expect(await main.evaluate(()=>({node:typeof (globalThis as any).require,process:typeof (globalThis as any).process,csp:document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.getAttribute("content")}))).toEqual(expect.objectContaining({node:"undefined",process:"undefined"}));
    const counts=await application.evaluate(({BrowserWindow})=>BrowserWindow.getAllWindows().length); expect(counts).toBeLessThanOrEqual(2);
    await expect.poll(()=>main.evaluate(()=>(window as any).maris.runtime.getSnapshot()),{timeout:30_000}).toMatchObject({state:"online",authenticated:true,errorCode:null});
    await expect.poll(()=>main.evaluate(()=>(window as any).maris.modules.list()),{timeout:10_000}).toEqual([expect.objectContaining({module_id:"daily_finance",enabled:true})]);
    await expect(main.evaluate(()=>(window as any).maris.runtime.recover())).resolves.toMatchObject({state:"online",authenticated:true,errorCode:null});
    await expect(main.evaluate(()=>(window as any).maris.modules.list())).resolves.toEqual([expect.objectContaining({module_id:"daily_finance",enabled:true})]);
  } finally {
    const closed=application.waitForEvent("close",{timeout:10_000}).catch(()=>undefined);
    await application.evaluate(({app})=>app.quit()).catch(()=>undefined);
    await closed;
  }
});
