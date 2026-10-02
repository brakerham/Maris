import {expect,test,vi} from 'vitest';
import {JSDOM,VirtualConsole} from 'jsdom';
import {act} from 'react';

// Only the lazy page's import port fails; router, Shell and renderer startup are real product code.
vi.mock('../../../apps/desktop/src/modules/daily-finance/DailyFinancePage',()=>{throw Error('VIRTUAL_CHUNK_UNAVAILABLE');});

test('R3-UI-02-LAZY | lazy chunk failure leaves Shell and other navigation available',async()=>{
  const virtualConsole=new VirtualConsole();const dom=new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>',{url:'http://127.0.0.1/',virtualConsole});
  vi.stubGlobal('window',dom.window);vi.stubGlobal('document',dom.window.document);vi.stubGlobal('location',dom.window.location);vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT',true);
  Object.defineProperty(dom.window,'maris',{value:{runtime:{getSnapshot:async()=>({state:'online',mode:'managed',authenticated:true,errorCode:null}),subscribe:()=>()=>{}},modules:{list:async()=>[{module_id:'daily_finance',version:'1.0.0',enabled:true,profile_ids:['daily_finance.assistant@1'],api_prefixes:['/api/v1/finance'],settings_schema_version:1}]},settings:{update:async()=>({ok:true})}}});
  try{
    await act(async()=>{await import('../../../apps/desktop/src/renderer/main');});
    for(let i=0;i<20&&!dom.window.document.querySelector('[role="alert"]');i++)await act(async()=>{await new Promise(resolve=>setTimeout(resolve,10));});
    const alert=dom.window.document.querySelector('[role="alert"]');const shell=dom.window.document.querySelector('main.shell');const navigation=dom.window.document.querySelector('nav[aria-label="模块导航"]');const agent=dom.window.document.querySelector('aside[aria-label="统一 Agent 面板"]');
    console.log(JSON.stringify({caseId:'R3-UI-02-LAZY',chunkFailureShown:Boolean(alert),shellPresent:Boolean(shell),navigationPresent:Boolean(navigation),agentPanelPresent:Boolean(agent),data:'virtual_only',evidenceLayer:'real_renderer_in_jsdom_with_virtual_bridge_and_failed_chunk'}));
    expect(alert?.textContent).toContain('页面暂时无法打开');
    expect(shell,'UI-02 requires local error isolation; Shell must remain usable').not.toBeNull();
    expect(navigation).not.toBeNull();expect(agent).not.toBeNull();
  }finally{dom.window.close();vi.unstubAllGlobals();}
});
