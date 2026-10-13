import { test, vi } from 'vitest';
const record=(globalThis as any).__r8Record;
const {JSDOM,VirtualConsole}=(globalThis as any).__r8Dom;
const React=await import('react');
const {act,createElement:h,StrictMode}=React;
const online={state:'online',mode:'managed',authenticated:true,errorCode:null};
const offline={state:'offline',mode:'managed',authenticated:false,errorCode:null};
const privateError='R8_VIRTUAL_PRIVATE_CANARY C:/virtual_only/private/chunk.js';
const deferred=()=>{let resolve:any,reject:any;const promise=new Promise<any>((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};};
const contribution=(name:string,order:number)=>({moduleId:name,version:'1.0.0',hostUiMajor:1,expectedApiPrefixes:[`/api/v1/${name}`],navigation:{label:name,order},routes:[{routeId:name,path:`/${name}`}],agentPanel:{profileId:`${name}.assistant@1`,title:name},settings:[],companion:{appearanceId:name,label:name}});
const host=(name:string,extra:any={})=>({module_id:name,version:'1.0.0',enabled:true,profile_ids:[`${name}.assistant@1`],api_prefixes:[`/api/v1/${name}`],settings_schema_version:1,...extra});

async function scenario(id:string,strict:boolean,run:(s:any)=>Promise<void>){
 record('body_enter',{id}); const begin=performance.now(),deadline=begin+15000;
 let failed=false,root:any,dom:any,unhandled=0,consoleLeak=false,consoleIncomplete=false,jsdomErrors=0;
 let mounted=false,cleanupStart=0;
 const spies:any[]=[]; const listeners=new Set<any>(); const savedGlobals=new Map<string,PropertyDescriptor|undefined>();
 const count={list:0,snapshot:0,subscribe:0,unsubscribe:0,settings:0,alpha:0,beta:0,gamma:0,denied:0,recover:0,auth:0,provider:0,outbox:0,finance:0};
 const used=new Set<string>();
 const scalar=(v:any)=>typeof v==='boolean'||typeof v==='number'&&Number.isFinite(v)||['unknown','dark','on','off','system','#/alpha','#/beta','#/settings'].includes(v)?v:'unknown';
 const check=(name:string,get:()=>any,expected:any,operator='eq')=>{
  const aid=`${id}.${name}`; if(used.has(aid))throw Error('r8_duplicate_assertion');used.add(aid);
  record('assert_enter',{id:aid,kind:'gate',operator,expected:scalar(expected)});let actual:any='unknown',passed=false;
  try{actual=scalar(get());passed=actual!=='unknown'&&(operator==='lte'?actual<=expected:operator==='positive'?Number.isSafeInteger(actual)&&actual>expected:actual===expected);}catch{}
  record(passed?'assert_pass':'assert_fail',{id:aid,kind:'gate',operator,expected:scalar(expected),actual});if(!passed)failed=true;return passed;
 };
 const guard=()=>{if(failed)throw Error('r8_gate_failed');if(performance.now()>=deadline)throw Error('r8_body_deadline');};
 const op=async(name:string,fn:()=>any)=>{guard();const oid=`${id}.${name}`;record('operation_enter',{id:oid});const start=performance.now();try{const x=await fn();record('operation_pass',{id:oid,durationMs:performance.now()-start});return x;}catch(e){record('operation_fail',{id:oid,durationMs:performance.now()-start,errorKind:e instanceof TypeError?'TypeError':'Error'});failed=true;throw Error('r8_operation_failed');}};
 const pause=async(ms=40)=>{await act(async()=>{await new Promise(r=>setTimeout(r,ms));});};
 const wait=async(name:string,fn:()=>boolean)=>op(name,async()=>{const end=Math.min(deadline-50,performance.now()+5000);let actual=fn();while(!actual&&performance.now()<end){await pause(5);actual=fn();}check(`${name}.READY`,()=>actual,true);});
 const q=(sel:string)=>dom.window.document.querySelector(sel);
 const ui=(name:string,selector:string,expected=true)=>{
  check(`${name}.EXISTS`,()=>q(selector)!==null,expected);
  check(`${name}.COUNT`,()=>dom.window.document.querySelectorAll(selector).length,expected?1:0);
  check(`${name}.CSS_VISIBLE`,()=>{const e=q(selector);if(!e)return false;let x=e;while(x){const st=dom.window.getComputedStyle(x);if(x.hidden||st.display==='none'||st.visibility==='hidden')return false;x=x.parentElement;}return true;},expected);
 };
 const leak=(text:string)=>/R8_VIRTUAL_PRIVATE_CANARY|virtual_only\/private|C:[\\/]virtual_only/.test(text);
 const inspect=(values:any[])=>{const seen=new Set<any>();const walk=(v:any,n:number)=>{if(typeof v==='string'){consoleLeak ||=leak(v);return;}if(v==null||typeof v!=='object'||seen.has(v))return;if(n>8){consoleIncomplete=true;return;}seen.add(v);for(const key of new Set([...Object.keys(v),'message','stack','cause','reason','error'])){try{walk(v[key],n+1);}catch{consoleIncomplete=true;}}};values.forEach(v=>walk(v,0));};
 const denied=(key:keyof typeof count='denied')=>(..._v:any[])=>{count[key]++;throw Error('r8_forbidden_call');};
 const unknown:any=new Proxy(denied(),{get:()=>unknown});
 const section=(v:any)=>new Proxy(v,{get:(t,k)=>Reflect.has(t,k)?Reflect.get(t,k):unknown});
 const s:any={count,check,guard,op,pause,wait,q,ui,dom:null,rows:[],snapshot:()=>Promise.resolve(offline),read:()=>Promise.resolve(s.rows),pages:{},mounted:false};
 const emitRaw=(v=online)=>{for(const fn of [...listeners])fn({...v});};
 s.emitRaw=emitRaw;s.emit=(name:string,v=online)=>op(name,()=>act(async()=>emitRaw(v)));
 s.settle=(name:string,fn:()=>void)=>op(name,()=>act(async()=>fn()));
 s.link=(path:string)=>q(`nav a[href="#/${path}"]`);
 s.click=(name:string,el:any)=>op(name,async()=>{check(`${name}.PRESENT`,()=>Boolean(el),true);guard();await act(async()=>el.click());});
 s.chrome=(name:string)=>{ui(`${name}.SHELL`,'main.shell');ui(`${name}.NAV`,'nav[aria-label="模块导航"]');ui(`${name}.AGENT`,'aside[aria-label="统一 Agent 面板"]');};
 s.settings=async(name:string)=>{await op(`${name}.THEME`,()=>act(async()=>{const e=q('select');e.value='dark';e.dispatchEvent(new dom.window.Event('change',{bubbles:true}));}));await s.click(`${name}.PRIVACY`,q('input[type="checkbox"]'));};
 s.state=(name:string)=>{check(`${name}.THEME`,()=>q('main.shell')?.getAttribute('data-theme'),'dark');check(`${name}.PRIVACY`,()=>q('main.shell')?.getAttribute('data-privacy'),'on');};
 s.active=()=>listeners.size;
 const windowReject=(e:any)=>{unhandled++;inspect([e.reason]);};
 try{
  const vc=new VirtualConsole();
  for(const key of ['error','warn','log','info','debug','trace','dir','dirxml','table','assert'] as const){spies.push(vi.spyOn(console,key).mockImplementation((...v:any[])=>inspect(v)));vc.on(key,(...v:any[])=>inspect(v));}
  vc.on('jsdomError',(e:any)=>{jsdomErrors++;inspect([e]);});
  dom=new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>',{url:'http://127.0.0.1/',virtualConsole:vc});s.dom=dom;
  for(const [key,value] of Object.entries({window:dom.window,document:dom.window.document,location:dom.window.location,IS_REACT_ACT_ENVIRONMENT:true,fetch:denied(),XMLHttpRequest:denied(),WebSocket:denied(),EventSource:denied()})){savedGlobals.set(key,Object.getOwnPropertyDescriptor(globalThis,key));Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});}
  for(const key of ['fetch','XMLHttpRequest','WebSocket','EventSource'])Object.defineProperty(dom.window,key,{configurable:true,value:denied()});
  dom.window.addEventListener('unhandledrejection',windowReject);
  record('product_import_enter',{id});
  const {createRoot}=await import('react-dom/client');
  const {compileRegistry}=await import('../../../apps/desktop/src/modules/registry');
  const {DesktopApp,rendererRootOptions}=await import('../../../apps/desktop/src/renderer/module-routes');
  record('product_import_resolved',{id});
  const registry=compileRegistry(['alpha','beta','gamma'].map((n,i)=>contribution(n,i)));
  const Page=(name:string)=>()=>h('h1',{id:`r8-${name}`},`Virtual ${name}`);
  s.Page=Page;s.rows=[host('alpha')];
  const bridge=section({runtime:section({getSnapshot:()=>{count.snapshot++;return s.snapshot();},subscribe:(fn:any)=>{count.subscribe++;listeners.add(fn);return()=>{if(listeners.delete(fn))count.unsubscribe++;};},recover:denied('recover')}),modules:section({list:()=>{count.list++;return s.read(count.list);}}),settings:section({update:async(v:any)=>{count.settings++;const safe=(v.theme==='dark'&&Object.keys(v).length===1)||(v.privacyMode===true&&Object.keys(v).length===1);check(`SETTINGS_${count.settings}.PAYLOAD`,()=>safe,true);return{ok:true};}}),auth:unknown,provider:unknown,outbox:section({enqueue:denied('outbox')}),finance:unknown});
  Object.defineProperty(dom.window,'maris',{value:bridge});
  const loaders=Object.fromEntries(['alpha','beta','gamma'].map(name=>[name,async()=>{count[name as 'alpha']++;return s.pages[name]?s.pages[name]():Page(name);} ]));
  s.mount=()=>op('MOUNT',()=>act(async()=>{root=createRoot(q('#root'),rendererRootOptions);mounted=true;const tree=h(DesktopApp,{registry,loaders});root.render(strict?h(StrictMode,null,tree):tree);}));
  s.unmount=()=>op('UNMOUNT_EARLY',()=>act(async()=>{root.unmount();mounted=false;}));
  await run(s);s.chrome('FINAL');guard();record('body_pass',{id,bodyMs:performance.now()-begin});
 }finally{
  cleanupStart=performance.now();record('cleanup_enter',{id,bodyMs:cleanupStart-begin});
  try{
   check('SAFETY.DOM_LEAK',()=>dom?leak(dom.window.document.documentElement.outerHTML):false,false);
   check('SAFETY.CONSOLE_LEAK',()=>consoleLeak,false);check('SAFETY.CONSOLE_COMPLETE',()=>consoleIncomplete,false);check('SAFETY.UNHANDLED',()=>unhandled,0);check('SAFETY.JSDOM',()=>jsdomErrors,0);
   for(const key of ['denied','recover','auth','provider','outbox','finance'] as const)check(`SIDE_EFFECT.${key.toUpperCase()}`,()=>count[key],0);
   try{if(mounted){await act(async()=>root.unmount());mounted=false;}check('CLEAN.ACTIVE_SUBSCRIPTIONS',()=>listeners.size,0);check('CLEAN.SUBSCRIPTIONS_BALANCED',()=>count.unsubscribe,count.subscribe);}
   finally{
    try{dom?.window.removeEventListener('unhandledrejection',windowReject);dom?.window.close();}
    finally{for(const spy of spies)spy.mockRestore();for(const [key,descriptor]of savedGlobals){if(descriptor)Object.defineProperty(globalThis,key,descriptor);else Reflect.deleteProperty(globalThis,key);}}
   }
   check('CLEAN.ROOT_UNMOUNTED',()=>mounted,false);check('CLEAN.GLOBALS_RESTORED',()=>[...savedGlobals].every(([k,v])=>v?Object.getOwnPropertyDescriptor(globalThis,k)?.value===v.value:!Object.hasOwn(globalThis,k)),true);
   check('CLEAN.BUDGET_MS',()=>performance.now()-cleanupStart,5000,'lte');
  }finally{record('cleanup_terminal',{id,cleanupMs:performance.now()-cleanupStart,passed:!failed});}
 }
 if(failed)throw Error('r8_gate_failed');
}

for(const [id,strict]of [['R8-01',false],['R8-02',true]] as const)test(`${id} | empty then identical ready notifications`,()=>scenario(id,strict,async s=>{
 s.rows=[];await s.mount();await s.wait('EMPTY',()=>!!s.q('main.shell'));s.check('INITIAL.READ_OCCURRED',()=>s.count.list,0,'positive');s.ui('INITIAL.ALPHA_NAV','nav a[href="#/alpha"]',false);s.check('INITIAL.NO_PRELOAD',()=>s.count.alpha,0);
 await s.emit('READY_BEFORE_MODULES');s.ui('BEFORE.ALPHA_NAV','nav a[href="#/alpha"]',false);
 s.rows=[host('alpha')];await s.emit('READY_AFTER_MODULES');await s.wait('PAGE',()=>!!s.q('#r8-alpha'));s.ui('PAGE.ALPHA','#r8-alpha');s.ui('PAGE.ALPHA_NAV','nav a[href="#/alpha"]');s.check('PAGE.HASH',()=>s.dom.window.location.hash,'#/alpha');
 const base=s.count.list;await s.op('QUIET',()=>s.pause(80));s.check('NO_POLL',()=>s.count.list,base);
}));
for(const [id,strict]of [['R8-03',false],['R8-04',true]] as const)test(`${id} | already ready mount`,()=>scenario(id,strict,async s=>{s.snapshot=()=>Promise.resolve(online);await s.mount();await s.wait('PAGE',()=>!!s.q('#r8-alpha'));s.ui('PAGE.ALPHA','#r8-alpha');s.check('RUNTIME.ONLINE',()=>s.q('header [role="status"]').textContent.includes('online'),true);}));
test('R8-05 | late initial snapshot cannot replace notification',()=>scenario('R8-05',false,async s=>{
 const late=deferred();s.snapshot=()=>late.promise;s.rows=[];await s.mount();s.rows=[host('alpha')];await s.emit('ONLINE');await s.wait('PAGE',()=>!!s.q('#r8-alpha'));await s.settle('LATE_SNAPSHOT',()=>late.resolve(offline));s.check('RUNTIME.STAYS_ONLINE',()=>s.q('header [role="status"]').textContent.includes('online'),true);s.ui('PAGE.ALPHA','#r8-alpha');
}));
test('R8-06 | synchronous notification inside initial module read',()=>scenario('R8-06',false,async s=>{
 s.read=(n:number)=>{if(n===1){s.emitRaw();return Promise.resolve([]);}return Promise.resolve([host('alpha')]);};await s.mount();await s.wait('PAGE',()=>!!s.q('#r8-alpha'));s.check('READS.BOUNDED',()=>s.count.list,2);s.ui('PAGE.ALPHA','#r8-alpha');
}));
test('R8-07 | burst coalescing discards older in-flight result',()=>scenario('R8-07',false,async s=>{
 const old=deferred();s.read=(n:number)=>n===1?old.promise:Promise.resolve([host('beta')]);await s.mount();await s.op('BURST',()=>act(async()=>{for(let i=0;i<12;i++)s.emitRaw();}));s.check('INFLIGHT.SINGLE',()=>s.count.list,1);await s.settle('OLD_RESULT',()=>old.resolve([host('alpha')]));await s.wait('BETA',()=>!!s.q('#r8-beta'));s.check('READS.COALESCED',()=>s.count.list,2);s.ui('OLD.ALPHA','#r8-alpha',false);s.ui('OLD.NAV','nav a[href="#/alpha"]',false);s.check('OLD.NO_PRELOAD',()=>s.count.alpha,0);await s.op('QUIET',()=>s.pause(80));s.check('NO_POLL',()=>s.count.list,2);
}));
test('R8-08 | read rejections and offline retain usable page',()=>scenario('R8-08',false,async s=>{
 s.snapshot=()=>Promise.reject(Error(privateError));s.read=()=>Promise.reject(Error(privateError));await s.mount();await s.wait('SAFE_EMPTY',()=>!!s.q('main.shell'));s.ui('EMPTY.PAGE','#r8-alpha',false);s.read=()=>Promise.resolve([host('alpha')]);await s.emit('RECOVER_LIST');await s.wait('PAGE',()=>!!s.q('#r8-alpha'));const shell=s.q('main.shell'),loads=s.count.alpha;
 s.read=()=>Promise.reject(Error(privateError));await s.emit('REJECT_LATER');await s.emit('OFFLINE',offline);s.ui('RETAIN.PAGE','#r8-alpha');s.check('RETAIN.SHELL',()=>s.q('main.shell')===shell,true);s.check('RETAIN.LOADS',()=>s.count.alpha,loads);
}));
test('R8-09 | equivalent lists preserve failed route and explicit retry',()=>scenario('R8-09',true,async s=>{
 let failing=true;s.pages.alpha=()=>{if(failing)throw Error(privateError);return s.Page('alpha');};s.rows=[host('alpha'),host('beta')];await s.mount();await s.wait('LOCAL_ERROR',()=>!!s.q('.content [role="alert"]'));const base=s.count.alpha,shell=s.q('main.shell'),subs=s.count.subscribe;
 s.check('LOADS.POSITIVE_BASE',()=>base,0,'positive');s.ui('ERROR.LOCAL','.content [role="alert"]');s.chrome('ERROR');
 s.rows=[host('beta'),host('alpha'),host('unrelated')];await s.emit('EQUIVALENT_NOTICE');await s.settings('SET');await s.emit('OFFLINE',offline);await s.op('QUIET',()=>s.pause(80));s.check('NO_IMPLICIT_LOAD',()=>s.count.alpha,base);s.check('NO_PRELOAD_BETA',()=>s.count.beta,0);s.check('SHELL.STABLE',()=>s.q('main.shell')===shell,true);s.check('SUBSCRIPTIONS.STABLE',()=>s.count.subscribe,subs);s.check('SUBSCRIPTIONS.ONE_ACTIVE',()=>s.active(),1);s.state('BEFORE_RETRY');
 failing=false;await s.click('EXPLICIT_RETRY',s.q('.content [role="alert"] button'));await s.wait('RECOVERED',()=>!!s.q('#r8-alpha'));s.check('RETRY.EXACT_INCREMENT',()=>s.count.alpha-base,1);s.state('AFTER_RETRY');s.check('RETRY.SHELL_STABLE',()=>s.q('main.shell')===shell,true);s.check('RETRY.SUBSCRIPTIONS_STABLE',()=>s.count.subscribe,subs);s.check('SETTINGS.TWO',()=>s.count.settings,2);
 await s.click('HEALTHY',s.link('beta'));await s.wait('HEALTHY_PAGE',()=>!!s.q('#r8-beta'));const healthy=s.count.beta;await s.emit('HEALTHY_REFRESH');s.check('HEALTHY.NO_RELOAD',()=>s.count.beta,healthy);s.ui('HEALTHY.KEPT','#r8-beta');
 await s.click('SETTINGS',s.link('settings'));await s.wait('SETTINGS_PAGE',()=>s.q('.content h1')?.textContent==='设置');await s.emit('SETTINGS_REFRESH');s.check('SETTINGS.HASH',()=>s.dom.window.location.hash,'#/settings');s.check('SETTINGS.CONTENT',()=>s.q('.content h1')?.textContent==='设置',true);s.check('SETTINGS.NO_RELOAD',()=>s.count.beta,healthy);s.state('SETTINGS_STATE');
}));
test('R8-10 | effective intersection changes remove active content',()=>scenario('R8-10',true,async s=>{
 s.rows=[host('alpha',{enabled:false}),host('beta',{version:'2.0.0'}),host('unknown')];await s.mount();await s.wait('EMPTY',()=>!!s.q('main.shell'));for(const n of ['alpha','beta','gamma']){s.ui(`DENIED.${n.toUpperCase()}`,`nav a[href="#/${n}"]`,false);s.check(`NO_PRELOAD.${n.toUpperCase()}`,()=>s.count[n],0);}
 s.rows=[host('alpha')];await s.emit('ADD_ALPHA');await s.wait('ALPHA',()=>!!s.q('#r8-alpha'));await s.settings('SET');s.rows=[host('beta')];await s.emit('REMOVE_ALPHA_ADD_BETA');await s.wait('REMOVED',()=>!s.q('#r8-alpha')&&!!s.link('beta'));s.ui('REMOVED.PAGE','#r8-alpha',false);s.ui('REMOVED.NAV','nav a[href="#/alpha"]',false);s.ui('ADDED.NAV','nav a[href="#/beta"]');s.chrome('REMOVED');s.state('REMOVED_STATE');s.check('ADDED.NO_PRELOAD',()=>s.count.beta,0);await s.click('OPEN_BETA',s.link('beta'));await s.wait('BETA',()=>!!s.q('#r8-beta'));s.ui('ADDED.PAGE','#r8-beta');
}));
test('R8-11 | pending old page cannot revive removed module',()=>scenario('R8-11',false,async s=>{
 const late=deferred();s.pages.alpha=()=>late.promise;await s.mount();await s.wait('LOADER_PENDING',()=>s.count.alpha>0);s.rows=[host('beta')];await s.emit('REPLACE_SET');await s.wait('BETA_NAV',()=>!!s.link('beta'));await s.click('OPEN_BETA',s.link('beta'));await s.wait('BETA',()=>!!s.q('#r8-beta'));await s.settle('OLD_PAGE_RESULT',()=>late.resolve(s.Page('alpha')));await s.op('QUIET',()=>s.pause(60));s.ui('STALE.ALPHA','#r8-alpha',false);s.ui('CURRENT.BETA','#r8-beta');s.check('CURRENT.HASH',()=>s.dom.window.location.hash,'#/beta');
}));
test('R8-12 | local render error after route-set replacement',()=>scenario('R8-12',true,async s=>{
 await s.mount();await s.wait('ALPHA',()=>!!s.q('#r8-alpha'));s.pages.beta=()=>()=>{throw Error(privateError);};s.rows=[host('beta')];await s.emit('REPLACE_SET');await s.wait('BETA_NAV',()=>!!s.link('beta'));await s.click('OPEN_BETA',s.link('beta'));await s.wait('LOCAL_ERROR',()=>!!s.q('.content [role="alert"]'));s.ui('ERROR.LOCAL','.content [role="alert"]');s.chrome('ERROR');const base=s.count.beta;s.rows=[host('beta')];await s.emit('EQUIVALENT');await s.op('QUIET',()=>s.pause(60));s.check('ERROR.NO_AUTO_RETRY',()=>s.count.beta,base);
}));
test('R8-13 | StrictMode old effect and unmount replies stay inert',()=>scenario('R8-13',true,async s=>{
 const old=deferred(),pending=deferred();s.read=(n:number)=>n===1?old.promise:Promise.resolve([host('beta')]);await s.mount();await s.wait('BETA',()=>!!s.q('#r8-beta'));s.check('STRICT.SUBSCRIBE_POSITIVE',()=>s.count.subscribe,1,'positive');await s.settle('OLD_EFFECT_RESULT',()=>old.resolve([host('alpha')]));s.ui('CURRENT.BETA','#r8-beta');s.ui('OLD.ALPHA','#r8-alpha',false);
 s.read=()=>pending.promise;await s.emit('PENDING_BEFORE_UNMOUNT');s.chrome('BEFORE_UNMOUNT');await s.unmount();const base=s.count.list;await s.settle('AFTER_UNMOUNT_RESULT',()=>pending.resolve([host('alpha')]));s.check('UNMOUNT.DOM_EMPTY',()=>s.q('#root')?.childElementCount,0);s.check('UNMOUNT.NO_MORE_READS',()=>s.count.list,base);s.check('UNMOUNT.SUBSCRIPTIONS_ZERO',()=>s.active(),0);
 // Final chrome checks are for mounted cases only; temporarily use the empty-root contract here.
 s.chrome=(name:string)=>s.check(`${name}.EMPTY_ROOT`,()=>s.q('#root')?.childElementCount,0);
}));
