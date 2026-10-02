import {expect,test,vi} from 'vitest';
import {JSDOM,VirtualConsole} from 'jsdom';
import {act} from 'react';
import {dailyFinanceContribution} from '../../../apps/desktop/src/modules/daily-finance/contribution';

const fault=vi.hoisted(()=>({hits:0,receipts:[] as {stage:string;count:number;epochMs:number}[]}));
vi.mock('../../../apps/desktop/src/modules/daily-finance/DailyFinancePage',()=>{
  fault.hits++;fault.receipts.push({stage:'virtual_page_factory_throw',count:fault.hits,epochMs:Date.now()});
  throw Error('VIRTUAL_CHUNK_UNAVAILABLE');
});

test('R4-R1-UI-02-OBSERVED-FAILURE | original production entry and four business assertions with observed page fault',async()=>{
  const started=Date.now();const events:{source:string;kind:string;safeProduct:boolean;virtualFailure:boolean}[]=[];
  const calls={runtime:0,modules:0,subscribe:0,unsubscribe:0,activeSubscriptions:0};
  const record=(source:string,value:unknown)=>{const str=String(value);events.push({source,kind:'error_or_warning',safeProduct:str.includes('desktop_render_unavailable')||str.includes('desktop_module_unavailable'),virtualFailure:str.includes('VIRTUAL_CHUNK_UNAVAILABLE')});};
  const vc=new VirtualConsole();vc.on('jsdomError',e=>record('virtual_console_jsdom',e.type));vc.on('error',e=>record('virtual_console_error',e));vc.on('warn',e=>record('virtual_console_warn',e));
  const errorSpy=vi.spyOn(console,'error').mockImplementation((...values)=>record('console_error',values[0]));const warnSpy=vi.spyOn(console,'warn').mockImplementation((...values)=>record('console_warn',values[0]));
  const dom=new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>',{url:'http://127.0.0.1/',virtualConsole:vc});
  vi.stubGlobal('window',dom.window);vi.stubGlobal('document',dom.window.document);vi.stubGlobal('location',dom.window.location);vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);
  const unhandled=(event:any)=>record('window_unhandled_rejection',event.reason);dom.window.addEventListener('unhandledrejection',unhandled);
  const ui=dailyFinanceContribution;const host={module_id:ui.moduleId,version:ui.version,enabled:true,profile_ids:[ui.agentPanel.profileId],api_prefixes:[...ui.expectedApiPrefixes],settings_schema_version:1};
  Object.defineProperty(dom.window,'maris',{value:{runtime:{getSnapshot:async()=>{calls.runtime++;return {state:'online',mode:'managed',authenticated:true,errorCode:null};},subscribe:()=>{calls.subscribe++;calls.activeSubscriptions++;return()=>{calls.unsubscribe++;calls.activeSubscriptions--;};}},modules:{list:async()=>{calls.modules++;return [host];}},settings:{update:async()=>({ok:true})}}});
  let entry:typeof import('../../../apps/desktop/src/renderer/main')|undefined;let observedAt:number|null=null;let stopReason='waiting';
  const state=()=>({mockHits:fault.hits,hash:dom.window.location.hash,alertShown:Boolean(dom.window.document.querySelector('[role="alert"]')),shellPresent:Boolean(dom.window.document.querySelector('main.shell')),navigationPresent:Boolean(dom.window.document.querySelector('nav[aria-label="模块导航"]')),agentPanelPresent:Boolean(dom.window.document.querySelector('aside[aria-label="统一 Agent 面板"]')),contentHasText:Boolean(dom.window.document.querySelector('.content')?.textContent?.trim()),publicStatusCount:dom.window.document.querySelectorAll('[role="status"]').length});
  try{
    await act(async()=>{entry=await import('../../../apps/desktop/src/renderer/main');});
    const waitStart=Date.now();while(Date.now()-waitStart<5000){
      if(fault.hits>0&&dom.window.document.querySelector('[role="alert"]')){observedAt=Date.now();stopReason='fault_and_alert_observed';break;}
      await act(async()=>{await new Promise(resolve=>setTimeout(resolve,20));});
    }
    if(!observedAt)stopReason=fault.hits?'fault_hit_alert_missing':'fault_not_hit';
    console.log(JSON.stringify({caseId:'R4-R1-UI-02-OBSERVED-FAILURE',stopReason,state:state(),calls:{...calls},hostSummary:{moduleId:host.module_id,enabled:true,profileIds:host.profile_ids,apiPrefixCount:host.api_prefixes.length,schemaVersion:1},elapsedSinceEntryMs:Date.now()-waitStart,elapsedTotalMs:Date.now()-started,exceededOld200Ms:Date.now()-waitStart>200,faultReceipts:fault.receipts,events:[...events],data:'virtual_only'}));
    expect(fault.hits,'fault injection must actually execute before isolation can pass').toBeGreaterThan(0);
    const alert=dom.window.document.querySelector('[role="alert"]');const shell=dom.window.document.querySelector('main.shell');const navigation=dom.window.document.querySelector('nav[aria-label="模块导航"]');const agent=dom.window.document.querySelector('aside[aria-label="统一 Agent 面板"]');
    expect(alert?.textContent).toContain('页面暂时无法打开');
    expect(shell,'UI-02 requires local error isolation; Shell must remain usable').not.toBeNull();
    expect(navigation).not.toBeNull();expect(agent).not.toBeNull();
  }finally{
    if(entry)await act(async()=>{entry!.desktopRoot.unmount();});
    const rootEmpty=dom.window.document.getElementById('root')?.childElementCount===0;
    dom.window.removeEventListener('unhandledrejection',unhandled);dom.window.close();vi.unstubAllGlobals();errorSpy.mockRestore();warnSpy.mockRestore();
    console.log(JSON.stringify({caseId:'R4-R1-UI-02-OBSERVED-FAILURE',stage:'cleanup',rootUnmounted:Boolean(entry),rootEmpty,activeSubscriptions:calls.activeSubscriptions,subscriptions:calls.subscribe,unsubscribe:calls.unsubscribe,domClosed:true,globalsRestored:true,events,data:'virtual_only'}));
    expect(calls.activeSubscriptions).toBe(0);expect(rootEmpty).toBe(true);
  }
});
