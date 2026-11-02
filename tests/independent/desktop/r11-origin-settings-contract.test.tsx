import {test,vi} from 'vitest';
import {makeFixture} from './r11-origin-settings-main-fixture';
import {CompareError} from './r11-origin-settings-record.mjs';
const rec=(globalThis as any).__r10;
const {JSDOM,VirtualConsole}=(globalThis as any).__r10Dom;
const tick=async()=>{for(let i=0;i<90;i++)await Promise.resolve();};
const saved={theme:'dark',reducedMotion:true,privacyMode:true};
const noRaw=(v:any)=>!JSON.stringify(v).includes('R10_PRIVATE');
const deferred=()=>{let resolve:any,reject:any;const promise=new Promise<any>((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
async function node(id:string,setup:()=>any,run:(f:any,c:any)=>Promise<void>){
 let f:any,first:any=null,clean=false;rec.emit('node_enter',{id});
 const c=(suffix:string,expected:any,actual:any)=>rec.check(id+'.'+suffix,expected,actual);
 try{f=setup();await f.start?.();await run(f,c);}catch(e){first=e;rec.error(id,e);}
 finally{rec.emit('cleanup_enter',{id});try{await f?.dispose?.();clean=true;}catch(e){rec.error(id,e,'cleanup');first??=e;}
  rec.emit('cleanup_terminal',{id,passed:clean});rec.emit('node_terminal',{id,passed:!first&&clean});}
 if(first)throw first;if(!clean)throw new Error('cleanup_incomplete');
}
const main=(origin='')=>makeFixture({...saved,closePolicy:'quit',mainBounds:{x:1,y:2,width:1000,height:700,displayId:'R10_PRIVATE_DISPLAY'}},origin);
function invoke(f:any,args:any[]=[],event?:any){return f.handlers.get('settings:get-snapshot@1')(event??{sender:f.main.webContents,senderFrame:f.main.webContents.mainFrame},...args);}
function failure(fn:()=>any){try{fn();return null;}catch(e){return e;}}
function errorCode(e:any){return ['ipc_sender_rejected','ipc_origin_rejected'].includes(e?.message)?e.message:e?.name==='ZodError'?'ZodError':e===null?null:'unknown';}

test('R10-I06 | development getter binds exact origin not a port prefix',()=>node('R10-I06',()=>main('http://127.0.0.1:5173'),async(f,c)=>{
 f.main.webContents.mainFrame.url='http://127.0.0.1:5173/index.html';c('TRUSTED',saved.theme,invoke(f).theme);
 f.main.webContents.mainFrame.url='http://127.0.0.1:51730/index.html';
 const error=failure(()=>invoke(f));c('DIFFERENT_PORT_REJECTED','ipc_origin_rejected',errorCode(error));
 c('NO_SAVE',0,f.count.save);
}));
// Independent, pre-frozen input tables. No network traffic or executor oracle.
const noFixture=()=>({dispose(){vi.restoreAllMocks();}});
test('R11-O01 | canonical network origins and same-origin resources',()=>node('R11-O01',noFixture,async(_f,c)=>{
 const {isTrustedRenderer}=await import('../../../apps/desktop/electron/main/security');
 const rows=[
  ['http://127.0.0.1:5173','http://127.0.0.1:5173/'],
  ['http://127.0.0.1:5173/','http://127.0.0.1:5173/other?x=1#part'],
  ['http://EXAMPLE.test','http://example.test:80/other'],
  ['http://example.test:80/a','http://EXAMPLE.test/b?c#d'],
  ['https://EXAMPLE.test','https://example.test:443/path'],
  ['https://example.test:443/','https://EXAMPLE.test/?q#fragment'],
 ];
 rows.forEach(([configured,actual],i)=>c('ALLOW_'+i,true,isTrustedRenderer(actual,configured)));
}));
test('R11-O02 | distinct network origins stay distinct in both directions',()=>node('R11-O02',noFixture,async(_f,c)=>{
 const {isTrustedRenderer}=await import('../../../apps/desktop/electron/main/security');
 const rows=[
  ['http://127.0.0.1:5173','http://127.0.0.1:51730/'],
  ['http://127.0.0.1:51730','http://127.0.0.1:5173/'],
  ['http://127.0.0.1:5173','https://127.0.0.1:5173/'],
  ['http://example.test:5173','http://example.test.evil.test:5173/'],
  ['http://example.test:5173','http://other.test:5173/'],
  ['http://localhost:5173','http://127.0.0.1:5173/'],
  ['http://127.0.0.1:5173','http://localhost:5173/'],
  ['https://example.test','https://example.test:444/'],
 ];
 rows.forEach(([configured,actual],i)=>c('REJECT_'+i,false,isTrustedRenderer(actual,configured)));
}));
test('R11-O03 | invalid or credential-bearing URLs fail without parse leakage',()=>node('R11-O03',noFixture,async(_f,c)=>{
 const {isTrustedRenderer}=await import('../../../apps/desktop/electron/main/security');
 const good='http://127.0.0.1:5173/';
 const invalid=['','/relative','not a url','http://[','http://127.0.0.1:99999','http://virtual-user@127.0.0.1:5173/','http://virtual-user:virtual-pass@127.0.0.1:5173/'];
 invalid.forEach((value,i)=>{
  for(const [kind,configured,actual] of [['CONFIG',value,good],['REQUEST',good,value]]){
   let result:any=null;const error=failure(()=>{result=isTrustedRenderer(actual,configured);});
   c(kind+'_'+i+'_ERROR',null,errorCode(error));c(kind+'_'+i+'_REJECT',false,result);
  }
 });
}));
test('R11-O04 | opaque protocols and original production resources',()=>node('R11-O04',noFixture,async(_f,c)=>{
 const {isTrustedRenderer}=await import('../../../apps/desktop/electron/main/security');
 const opaque=['data:text/plain,virtual','javascript:void(0)','ftp://example.test/a','blob:http://127.0.0.1:5173/virtual-id','null'];
 opaque.forEach((value,i)=>{c('SAME_OPAQUE_'+i,false,isTrustedRenderer(value,value));c('NETWORK_CONFIG_'+i,false,isTrustedRenderer(value,'http://127.0.0.1:5173'));});
 const resources=[['file:///virtual/index.html',true],['maris://app/index.html',true],['filex:///virtual/index.html',false],['maris://app.evil/index.html',false],['maris://other/index.html',false]] as const;
 for(const [j,configured]of ['http://127.0.0.1:5173','invalid-config'].entries())for(const [i,[actual,expected]]of resources.entries())c('PRODUCTION_'+j+'_'+i,expected,isTrustedRenderer(actual,configured));
}));
test('R11-O05 | real validation preserves identity origin and schema order',()=>node('R11-O05',noFixture,async(_f,c)=>{
 const {validateIpc}=await import('../../../apps/desktop/electron/main/ipc-contract');
 const frame={url:'http://127.0.0.1:5173/'},contents={mainFrame:frame},window:any={webContents:contents};
 const event:any={sender:contents,senderFrame:frame},origin='http://127.0.0.1:5173';
 const call=(channel:any,args:any[],ev=event)=>validateIpc(ev,window,channel,args,origin);
 const invalid=[{token:'R11_PRIVATE'}];
 frame.url='http://127.0.0.1:51730/';
 c('WRONG_SENDER_FIRST','ipc_sender_rejected',errorCode(failure(()=>call('settings:update@1',invalid,{sender:{},senderFrame:frame}))));
 c('SUBFRAME_FIRST','ipc_sender_rejected',errorCode(failure(()=>call('settings:update@1',invalid,{sender:contents,senderFrame:{url:frame.url}}))));
 c('ORIGIN_BEFORE_SCHEMA','ipc_origin_rejected',errorCode(failure(()=>call('settings:update@1',invalid))));
 frame.url=origin+'/valid';
 c('GETTER_EMPTY',0,call('settings:get-snapshot@1',[]).length);
 c('GETTER_STRICT','ZodError',errorCode(failure(()=>call('settings:get-snapshot@1',[{}]))));
 c('UPDATE_STRICT','ZodError',errorCode(failure(()=>call('settings:update@1',invalid))));
 c('UPDATE_CLOSE_FORBIDDEN','ZodError',errorCode(failure(()=>call('settings:update@1',[{closePolicy:'quit'}]))));
 c('UPDATE_TYPE_STRICT','ZodError',errorCode(failure(()=>call('settings:update@1',[{privacyMode:'true'}]))));
 c('UPDATE_ALLOWED',true,JSON.stringify(call('settings:update@1',[saved]))===JSON.stringify([saved]));
}));
const effects=(f:any)=>JSON.stringify({count:f.count,persisted:f.persisted,windows:f.windows.map((w:any)=>({shows:w.shows,focuses:w.focuses,hides:w.hides,destroys:w.destroys,visible:w.visible})),sent:f.sent.length,prompts:f.prompts.length});
test('R11-O06 | real main handlers reject without incremental effects',()=>node('R11-O06',()=>main('http://127.0.0.1:5173/'),async(f,c)=>{
 const event={sender:f.main.webContents,senderFrame:f.main.webContents.mainFrame};
 const update=(value:any)=>f.handlers.get('settings:update@1')(event,value);
 const beforeSave=f.count.save;
 c('TRUSTED_GETTER','dark',invoke(f).theme);c('TRUSTED_WRITE',true,(await update({theme:'light'})).accepted);
 c('ONE_SAVE',beforeSave+1,f.count.save);c('CURRENT_GETTER','light',invoke(f).theme);
 const before=effects(f);event.senderFrame.url='http://127.0.0.1:51730/settings';
 c('GET_REJECT','ipc_origin_rejected',errorCode(failure(()=>invoke(f))));
 c('WRITE_REJECT','ipc_origin_rejected',errorCode(failure(()=>update({theme:'dark'}))));
 await tick();c('NO_INCREMENTAL_EFFECTS',true,before===effects(f));
}));
test('R11-O07 | companion handlers use own origin identity and narrow arguments',()=>node('R11-O07',()=>makeFixture(saved,'http://127.0.0.1:5173','http://127.0.0.1:5174'),async(f,c)=>{
 const companion=f.windows.find((w:any)=>w!==f.main),frame=companion.webContents.mainFrame;
 const event={sender:companion.webContents,senderFrame:frame};
 const call=(channel:string,args:any[]=[],ev:any=event)=>f.handlers.get(channel)(ev,...args);
 c('TRUSTED_STATE',true,typeof call('companion:get-state@1').state==='string');
 const shows=f.main.shows,focuses=f.main.focuses;
 c('TRUSTED_OPEN',true,call('companion:open-main@1').accepted);
 c('SHOW_ONCE',shows+1,f.main.shows);c('FOCUS_ONCE',focuses+1,f.main.focuses);
 for(const [i,channel]of ['companion:get-state@1','companion:open-main@1'].entries()){
  c('STRICT_'+i,'ZodError',errorCode(failure(()=>call(channel,[{}]))));
  c('IDENTITY_'+i,'ipc_sender_rejected',errorCode(failure(()=>call(channel,[],{sender:f.main.webContents,senderFrame:frame}))));
  c('SUBFRAME_'+i,'ipc_sender_rejected',errorCode(failure(()=>call(channel,[],{sender:companion.webContents,senderFrame:{url:frame.url}}))));
 }
 const before=effects(f);frame.url='http://127.0.0.1:5173/companion';
 c('MAIN_ORIGIN_STATE_REJECT','ipc_origin_rejected',errorCode(failure(()=>call('companion:get-state@1'))));
 c('MAIN_ORIGIN_OPEN_REJECT','ipc_origin_rejected',errorCode(failure(()=>call('companion:open-main@1'))));
 await tick();c('NO_INCREMENTAL_EFFECTS',true,before===effects(f));
}));
test('R11-O08 | adjacent main and companion ports are isolated both ways',()=>node('R11-O08',()=>makeFixture(saved,'http://127.0.0.1:5173','http://127.0.0.1:51730'),async(f,c)=>{
 const companion=f.windows.find((w:any)=>w!==f.main),mainFrame=f.main.webContents.mainFrame,companionFrame=companion.webContents.mainFrame;
 const event={sender:companion.webContents,senderFrame:companionFrame};
 const getCompanion=()=>f.handlers.get('companion:get-state@1')(event);
 c('MAIN_POSITIVE','dark',invoke(f).theme);c('COMPANION_POSITIVE',true,typeof getCompanion().state==='string');
 const before=effects(f);mainFrame.url='http://127.0.0.1:51730/main';companionFrame.url='http://127.0.0.1:5173/companion';
 c('MAIN_CROSS_REJECT','ipc_origin_rejected',errorCode(failure(()=>invoke(f))));
 c('COMPANION_CROSS_REJECT','ipc_origin_rejected',errorCode(failure(getCompanion)));
 c('MAIN_FRAME_SAME',true,mainFrame===f.main.webContents.mainFrame);c('COMPANION_FRAME_SAME',true,companionFrame===companion.webContents.mainFrame);
 await tick();c('NO_INCREMENTAL_EFFECTS',true,before===effects(f));
}));
test('R10-I07 | actual preloads expose fixed getter only to main',()=>node('R10-I07',()=>({dispose(){vi.doUnmock('electron');vi.restoreAllMocks();}}),async(_f,c)=>{
 vi.resetModules();const exposed=new Map<string,any>(),calls:any[]=[];
 vi.doMock('electron',()=>({contextBridge:{exposeInMainWorld:(k:string,v:any)=>exposed.set(k,v)},ipcRenderer:{invoke:async(...args:any[])=>{calls.push(args);return saved;},on(){},removeListener(){}}}));
 await import('../../../apps/desktop/electron/preload/index');await import('../../../apps/desktop/electron/preload/companion');
 const bridge=exposed.get('maris'),companion=exposed.get('companion');
 c('SETTINGS_KEYS',true,JSON.stringify(Object.keys(bridge.settings).sort())==='["getSnapshot","update"]');
 c('NO_GENERIC_INVOKE',true,!('invoke' in bridge));await bridge.settings.getSnapshot('ignored');
 c('FIXED_ZERO_ARGS',true,JSON.stringify(calls)==='[["settings:get-snapshot@1"]]');
 c('COMPANION_NARROW',true,JSON.stringify(Object.keys(companion).sort())==='["getState","openMain"]');
 c('NO_COMPANION_SETTINGS',true,!('settings' in companion));
}));

async function uiFixture(options:any={}){
 const React=await import('react'),{act,createElement:h,StrictMode}=React;
 const globals=new Map<string,PropertyDescriptor|undefined>(),listeners=new Set<any>(),spies:any[]=[];
 let root:any,dom:any,mounted=false,leaks=false,unhandled=0,denied=0;
 const count={read:0,write:0,load:0,list:0,recover:0},writes:any[]=[];
 const vc=new VirtualConsole();vc.on('jsdomError',()=>{unhandled++;});
 dom=new JSDOM('<!doctype html><div id="root"></div>',{url:'http://127.0.0.1/',virtualConsole:vc});
 const reject=()=>{denied++;throw Error('unexpected_external_call');};
 for(const [key,value] of Object.entries({window:dom.window,document:dom.window.document,location:dom.window.location,IS_REACT_ACT_ENVIRONMENT:true,fetch:reject,XMLHttpRequest:reject,WebSocket:reject,EventSource:reject})){
  globals.set(key,Object.getOwnPropertyDescriptor(globalThis,key));Object.defineProperty(globalThis,key,{configurable:true,writable:true,value});}
 for(const key of ['fetch','XMLHttpRequest','WebSocket','EventSource'])Object.defineProperty(dom.window,key,{configurable:true,value:reject});
 for(const key of ['error','warn','log'] as const)spies.push(vi.spyOn(console,key).mockImplementation((...args:any[])=>{leaks ||=args.some(x=>String(x).includes('R10_PRIVATE'));}));
 const runtime={state:'online',mode:'managed',authenticated:true,errorCode:null};
 const row={module_id:'daily_finance',version:'1.0.0',enabled:true,profile_ids:['daily_finance.assistant@1'],api_prefixes:['/api/v1/finance'],settings_schema_version:1};
 const f:any={count,writes,dom,rows:options.empty?[]:[row],row,listeners,read:options.read??(()=>Promise.resolve(saved)),load:options.load??(()=>Promise.resolve(()=>h('h1',{id:'r10-page'},'Virtual only')))};
 const emit=(value=runtime)=>{for(const fn of listeners)fn({...value});};
 const bridge={settings:{getSnapshot:()=>{count.read++;return f.read(count.read);},update:async(v:any)=>{count.write++;writes.push(v);return{accepted:true};}},modules:{list:async()=>{count.list++;return f.rows;}},runtime:{getSnapshot:async()=>runtime,subscribe:(fn:any)=>{listeners.add(fn);return()=>listeners.delete(fn);},recover:async()=>{count.recover++;emit({...runtime,state:'recovering'});emit();return runtime;}},outbox:{enqueue:reject},external:{open:reject},window:{perform:reject}};
 Object.defineProperty(dom.window,'maris',{value:bridge});f.bridge=bridge;
 f.dispose=async()=>{let cleanupError:any=null;try{await f.unmount();if(listeners.size||denied||unhandled||leaks||dom.window.document.body.textContent.includes('R10_PRIVATE'))throw new Error('ui_cleanup_safety');}catch(e){cleanupError=e;}finally{try{dom.window.close();}finally{for(const spy of spies)spy.mockRestore();for(const [key,desc]of globals){if(desc)Object.defineProperty(globalThis,key,desc);else Reflect.deleteProperty(globalThis,key);}}}if(cleanupError)throw cleanupError;};
 try{
 const {createRoot}=await import('react-dom/client');
 const {DesktopApp,rendererRootOptions}=await import('../../../apps/desktop/src/renderer/module-routes');
 const {dailyFinanceContribution}=await import('../../../apps/desktop/src/modules/daily-finance/contribution');
 const {compileRegistry}=await import('../../../apps/desktop/src/modules/registry');
 const registry=compileRegistry([dailyFinanceContribution]),loaders={daily_finance_home:()=>{count.load++;return f.load();}};
 f.q=(selector:string)=>dom.window.document.querySelector(selector);
 f.flush=()=>act(async()=>{await new Promise(r=>setTimeout(r,15));});
 f.emit=()=>act(async()=>emit());f.resolve=(fn:()=>void)=>act(async()=>fn());
 f.wait=async(c:any,suffix:string,fn:()=>boolean)=>{const until=performance.now()+5000;while(!fn()&&performance.now()<until)await f.flush();c(suffix,true,!!fn());};
 f.mount=async()=>{root=createRoot(f.q('#root'),rendererRootOptions);mounted=true;await act(async()=>root.render(options.strict?h(StrictMode,null,h(DesktopApp,{registry,loaders})):h(DesktopApp,{registry,loaders})));};
 f.unmount=async()=>{if(mounted){await act(async()=>root.unmount());mounted=false;}};
 f.state=(c:any,prefix:string,value=saved)=>{c(prefix+'_THEME',value.theme,f.q('main.shell')?.dataset.theme??null);c(prefix+'_PRIVACY',value.privacyMode?'on':'off',f.q('main.shell')?.dataset.privacy??null);c(prefix+'_SELECT',value.theme,f.q('select')?.value??null);c(prefix+'_CHECKBOX',value.privacyMode,f.q('input[type=checkbox]')?.checked??null);};
 f.choose=async()=>act(async()=>{const select=f.q('select');select.value='light';select.dispatchEvent(new dom.window.Event('change',{bubbles:true}));f.q('input[type=checkbox]').click();});

 return f;
 }catch(e){try{await f.dispose();}catch{}throw e;}
}
// The asynchronous fixture is acquired before mount and always released by node().
async function uiNode(id:string,options:any,run:(f:any,c:any)=>Promise<void>){let fixture:any;return node(id,()=>({async start(){fixture=await uiFixture(options);},async dispose(){await fixture?.dispose();}}),async(_f,c)=>{await run(fixture,c);});}
let n=0;
for(const theme of ['system','light','dark','high_contrast'])for(const privacyMode of [false,true])for(const reducedMotion of [false,true]){
 const id='R10-U'+String(++n).padStart(2,'0');test(id+' | valid snapshot combination',()=>uiNode(id,{read:async()=>({theme,privacyMode,reducedMotion})},async(f,c)=>{
  await f.mount();await f.wait(c,'READY',()=>!!f.q('#r10-page'));f.state(c,'RESTORED',{theme,privacyMode,reducedMotion});c('READ_ONCE',1,f.count.read);c('NO_WRITE',0,f.count.write);
 }));
}
const invalid=[{...saved,theme:'sepia'},{...saved,privacyMode:'true'},{...saved,reducedMotion:0},{theme:'dark',privacyMode:true},{...saved,token:'R10_PRIVATE_SECRET'},null,[],{...saved,theme:null}];
invalid.forEach((value,index)=>{const id='R10-U'+String(17+index).padStart(2,'0');test(id+' | malformed response safe finite error',()=>uiNode(id,{read:async()=>value},async(f,c)=>{await f.mount();await f.wait(c,'ERROR',()=>!!f.q('[role=alert]'));c('NO_SHELL',true,!f.q('main.shell'));c('NO_PAGE',true,!f.q('#r10-page'));c('SAFE_TEXT',true,!f.dom.window.document.body.textContent.includes('R10_PRIVATE'));await f.flush();c('NO_LOOP',1,f.count.read);c('NO_WRITE',0,f.count.write);}));});
test('R10-U25 | pending settings hide business and writable controls',()=>{const pending=deferred();return uiNode('R10-U25',{read:()=>pending.promise},async(f,c)=>{await f.mount();c('LOADING',true,!!f.q('[role=status]'));c('NO_PAGE',true,!f.q('#r10-page'));c('NO_CONTROLS',true,!f.q('select')&&!f.q('input'));c('NO_WRITE',0,f.count.write);await f.resolve(()=>pending.resolve(saved));await f.wait(c,'READY',()=>!!f.q('#r10-page'));f.state(c,'RESOLVED');});});
test('R10-U26 | rejected read remains safe without defaults or retry loop',()=>uiNode('R10-U26',{read:()=>Promise.reject(Error('R10_PRIVATE_TOKEN_PATH'))},async(f,c)=>{await f.mount();await f.wait(c,'ERROR',()=>!!f.q('[role=alert]'));c('NO_SHELL',true,!f.q('main.shell'));c('NO_RAW',true,!f.dom.window.document.body.textContent.includes('R10_PRIVATE'));await f.emit();await f.flush();c('ONE_READ',1,f.count.read);c('ZERO_WRITES',0,f.count.write);}));
test('R10-U27 | StrictMode stale response cannot overwrite current choice',()=>{const old=deferred();return uiNode('R10-U27',{strict:true,read:(i:number)=>i===1?old.promise:Promise.resolve(saved)},async(f,c)=>{await f.mount();await f.wait(c,'READY',()=>!!f.q('#r10-page'));const before=f.count.read;await f.choose();await f.resolve(()=>old.resolve({theme:'system',privacyMode:false,reducedMotion:false}));f.state(c,'CHOICE',{theme:'light',privacyMode:false});c('NO_REREAD',before,f.count.read);c('TWO_EXPLICIT_WRITES',2,f.count.write);});});
test('R10-U28 | response after unmount stays inert',()=>{const late=deferred();return uiNode('R10-U28',{read:()=>late.promise},async(f,c)=>{await f.mount();const reads=f.count.read;await f.unmount();await f.resolve(()=>late.resolve(saved));c('EMPTY',0,f.q('#root').childElementCount);c('NO_LISTENERS',0,f.listeners.size);c('READS_UNCHANGED',reads,f.count.read);c('NO_WRITE',0,f.count.write);});});
test('R10-U29 | notices and recovery preserve user state without implicit page reload',()=>uiNode('R10-U29',{},async(f,c)=>{await f.mount();await f.wait(c,'READY',()=>!!f.q('#r10-page'));await f.choose();const base={...f.count},page=f.q('#r10-page');await f.emit();await f.resolve(()=>{void f.bridge.runtime.recover();});await f.flush();f.state(c,'CHOICE',{theme:'light',privacyMode:false});c('NO_REHYDRATE',base.read,f.count.read);c('NO_RELOAD',base.load,f.count.load);c('PAGE_IDENTITY',true,page===f.q('#r10-page'));c('NO_IMPLICIT_WRITE',base.write,f.count.write);}));
test('R10-U30 | settings hydrate before modules become available',()=>uiNode('R10-U30',{empty:true},async(f,c)=>{await f.mount();await f.wait(c,'EMPTY_SHELL',()=>!!f.q('main.shell'));f.state(c,'EMPTY');c('ZERO_PAGE_LOAD',0,f.count.load);f.rows=[f.row];await f.emit();await f.wait(c,'READY',()=>!!f.q('#r10-page'));f.state(c,'LATE_MODULE');c('READ_ONCE',1,f.count.read);c('NO_WRITE',0,f.count.write);}));
test('R10-U31 | runtime notices do not retry a failed page or rehydrate settings',()=>uiNode('R10-U31',{load:()=>Promise.reject(Error('R10_PRIVATE_CHUNK'))},async(f,c)=>{await f.mount();await f.wait(c,'LOCAL_ERROR',()=>!!f.q('.content [role=alert]'));await f.choose();const base={...f.count};await f.emit();await f.flush();c('NO_RETRY',base.load,f.count.load);c('NO_REHYDRATE',base.read,f.count.read);f.state(c,'CHOICE',{theme:'light',privacyMode:false});c('SHELL_AND_AGENT',true,!!f.q('main.shell')&&!!f.q('aside'));}));
