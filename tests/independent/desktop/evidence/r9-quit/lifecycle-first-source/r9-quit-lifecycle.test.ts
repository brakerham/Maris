import { EventEmitter } from 'node:events';
import { it, vi } from 'vitest';

// Independent boundary fixture: the real main, composition, companion and retention
// controllers run together. Only OS, persistence and backend ports are controlled.
const record = (globalThis as any).__r9Record;
const tooling = (globalThis as any).__r9Tooling;
const tick = async () => { for (let n=0;n<90;n++) await Promise.resolve(); };
const cancelEvent = () => ({defaultPrevented:false,preventDefault(){this.defaultPrevented=true;}});
function deferred<T=void>() {
  let resolve!:(value:T)=>void, reject!:(reason:Error)=>void;
  const promise=new Promise<T>((ok,no)=>{resolve=ok;reject=no;});
  return {promise,resolve,reject};
}
const base='../../../apps/desktop/electron/main/';
const boundaryNames=['device-settings','outbox','managed-host-port','backend-supervisor','owner-session','owner-auth-client','owner-secret-store','host-client'];
const allIds=new Set<string>();

async function scenario(id:string, options:Record<string,unknown>, exercise:(f:any,c:any)=>Promise<void>) {
  const started=performance.now(); let bodyPassed=false, error:any=null, cleaned=false;
  let stage='body', fixture:any=null;
  const c=(suffix:string,expected:boolean|number,actual:boolean|number,operator='eq')=>{
    const assertionId=id+'.'+suffix;
    tooling.claim(allIds,assertionId,id,record,stage);
    record('assert_enter',{id:assertionId,nodeId:id,stage,operator,expected});
    const passed=operator==='lte'?actual<=expected:actual===expected;
    record(passed?'assert_pass':'assert_fail',{id:assertionId,nodeId:id,stage,operator,expected,actual,passed});
    if(!passed)throw new tooling.GateError('comparison');
  };
  record('body_enter',{id});
  try {
    fixture=makeFixture(options);
    record('product_import_enter',{id});
    await fixture.start();
    record('product_import_terminal',{id});
    c('START.MAIN',1,fixture.windows.filter((w:any)=>w.title==='Maris').length);
    c('START.AUTH',true,fixture.sent.some((r:any)=>r.state==='online'&&r.authenticated===true));
    c('START.OWNED',1,fixture.count.start);
    c('START.SESSION',1,fixture.count.establish);
    c('START.WINDOWS',options.companionVisible===false?1:2,fixture.live.size);
    await exercise(fixture,c);
    c('NO.RECOVER',0,fixture.count.recover);
    c('NO.REVOKE',0,fixture.count.revoke);
    c('NO.REFRESH',0,fixture.count.refresh);
    c('NO.BUSINESS.WRITE',0,fixture.count.enqueue);
    c('NO.UNHANDLED',0,fixture.unhandled.length);
    c('BODY.BUDGET',15000,performance.now()-started,'lte');
    bodyPassed=true;
  } catch(e) {
    error=e;
    const kind=tooling.classify(e);
    if(kind==='unknown')record('unknown_error',{nodeId:id,errorKind:['Error','TypeError','AssertionError'].includes((e as any)?.name)?(e as any).name:'other',stage});
  } finally {
    stage='cleanup'; const cleanupStart=performance.now();
    record('cleanup_enter',{id,bodyMs:cleanupStart-started});
    try {
      await fixture?.dispose();
      c('CLEANUP.LIVE',0,fixture?.live.size??0);
      c('CLEANUP.LISTENERS',0,fixture?.app.eventNames().length??0);
      c('CLEANUP.BUDGET',5000,performance.now()-cleanupStart,'lte');
      cleaned=true;
    }catch(e){if(error===null)error=e;record('cleanup_error',{nodeId:id,errorKind:'cleanup',stage});}
    record('cleanup_terminal',{id,passed:cleaned,cleanupMs:performance.now()-cleanupStart});
    record('node_terminal',{id,passed:tooling.nodePassed(bodyPassed,error,cleaned),durationMs:performance.now()-started});
  }
  if(error!==null)throw error;
  if(!bodyPassed||!cleaned)throw Error('scenario_incomplete');
}

function makeFixture(overrides:Record<string,unknown>) {
  vi.resetModules();
  const app:any=new EventEmitter(), live=new Set<any>(), windows:any[]=[], sent:any[]=[], trace:string[]=[], unhandled:any[]=[];
  const count={start:0,establish:0,save:0,flush:0,stop:0,recover:0,revoke:0,refresh:0,enqueue:0,quit:0,final:0,allClosed:0,trayDestroy:0};
  const saveGate=deferred(), stopGate=deferred();
  let hold=false, disposing=false, depth=0, persisted:any, menu:any[]=[], tray:any;
  const prompts:any[]=[], pending:any[]=[];
  const onUnhandled=(e:any)=>unhandled.push(e);
  process.on('unhandledRejection',onUnhandled);
  class Window extends EventEmitter {
    title:string; destroyed=false; visible=false; hides=0; destroys=0;
    webContents={setWindowOpenHandler:()=>{},on:()=>{},send:(_channel:string,value:any)=>sent.push(value)};
    constructor(options:any){super();this.title=options.title;windows.push(this);live.add(this);}
    show(){this.visible=true;} hide(){if(this.destroyed)throw Error('invalid_window_operation');this.visible=false;this.hides++;}
    focus(){} setAlwaysOnTop(){} async loadFile(){} async loadURL(){}
    isDestroyed(){return this.destroyed;} isVisible(){return this.visible;}
    close(){const e=cancelEvent();this.emit('close',e);if(!e.defaultPrevented&&!this.destroyed)this.destroy();return e;}
    destroy(){
      if(this.destroyed)throw Error('duplicate_window_destroy');
      this.destroyed=true;this.destroys++;live.delete(this);trace.push('destroy:'+this.title);this.emit('closed');
      if(live.size===0&&!disposing){count.allClosed++;app.emit('window-all-closed');}
    }
  }
  // This models Electron's public event contract, not the product shutdown function.
  const quit=()=>{
    count.quit++;if(++depth>10)throw Error('unbounded_quit_reentry');
    try {
      const before=cancelEvent();app.emit('before-quit',before);
      if(before.defaultPrevented)return;
      for(const window of [...live])window.close();
      if(live.size!==0)return;
      const will=cancelEvent();app.emit('will-quit',will);
      if(!will.defaultPrevented){count.final++;app.emit('quit',cancelEvent(),0);}
    }finally{depth--;}
  };
  Object.assign(app,{getPath:()=> 'R9-virtual-profile',getAppPath:()=> 'R9-virtual-app',isPackaged:false,
    requestSingleInstanceLock:()=>true,whenReady:async()=>{},quit,setLoginItemSettings:()=>{}});
  class Tray {
    destroyed=false;
    constructor(){tray=this;} setToolTip(){} on(){} setContextMenu(value:any[]){menu=value;}
    destroy(){if(this.destroyed)throw Error('duplicate_tray_destroy');this.destroyed=true;count.trayDestroy++;trace.push('destroy:tray');}
  }
  const dialog=vi.fn(async(_window:any,options:any)=>{prompts.push(options);const gate=deferred<{response:number}>();pending.push(gate);return gate.promise;});
  const consoleErrors:any[]=[];
  const f:any={app,live,windows,sent,count,trace,unhandled,saveGate,stopGate,prompts,consoleErrors,
    get main(){return windows.find(w=>w.title==='Maris');},get tray(){return tray;},
    get persisted(){return {...persisted};}, holdSave(){hold=true;},
    respond(response:number){const gate=pending.shift();if(!gate)throw Error('missing_prompt');gate.resolve({response});},
    trayQuit(){const entry=menu.find(m=>m.label==='退出');if(!entry)throw Error('missing_tray_entry');entry.click();},
    async start(){
      vi.stubEnv('MARIS_E2E','');vi.stubEnv('MARIS_E2E_EXIT_MS','');vi.stubEnv('MARIS_EXTERNAL_HOST_URL','');vi.stubEnv('MARIS_EXTERNAL_HOST_NONCE','');
      for(const name of ['MAIN_WINDOW','COMPANION_WINDOW']){vi.stubGlobal(name+'_VITE_DEV_SERVER_URL','');vi.stubGlobal(name+'_VITE_NAME',name.toLowerCase());}
      vi.spyOn(console,'error').mockImplementation((...args)=>consoleErrors.push(args));
      const actual=await import('../../../apps/desktop/electron/main/device-settings');
      persisted={...actual.defaultSettings,closePolicy:'quit',closeHintShown:false,companionVisible:true,...overrides};
      class Settings {
        async load(){return {...persisted};}
        async save(value:any){count.save++;trace.push('save_enter');if(hold)await saveGate.promise;persisted={...value};trace.push('save_done');}
      }
      class Outbox {
        async load(){} async cleanup(){count.flush++;trace.push('flush');}
        async retentionCandidates(){return [];} async deleteConfirmed(){throw Error('unexpected_retention_delete');}
        async prepare(){count.enqueue++;throw Error('unexpected_business_write');}
      }
      class Supervisor {
        snapshot(){return {state:'online',mode:'managed',authenticated:false,errorCode:null};}
        subscribe(){} async start(){count.start++;return this.snapshot();}
        async shutdown(){count.stop++;trace.push('stop_enter');await stopGate.promise;trace.push('stop_done');}
        async recover(){count.recover++;return this.snapshot();}
      }
      class Owner {
        safeState='authenticated';async establish(){count.establish++;return this.safeState;}
        accessToken(){return 'R9_VIRTUAL_TOKEN';}async refresh(){count.refresh++;}async revoke(){count.revoke++;}
      }
      class Host {setAccessToken(){} async modules(){return [{module_id:'daily_finance',version:'1.0.0',enabled:true,profile_ids:['daily_finance.assistant@1'],api_prefixes:['/api/v1/finance'],settings_schema_version:1}];}}
      class Port {}
      vi.doMock('electron',()=>({app,BrowserWindow:Window,Tray,dialog:{showMessageBox:dialog},ipcMain:{handle(){}},
        Menu:{buildFromTemplate:(v:any)=>v},nativeImage:{createFromDataURL(){}},safeStorage:{},shell:{},
        screen:{getPrimaryDisplay:()=>({workArea:{x:0,y:0,width:1280,height:800}})},
        session:{defaultSession:{setPermissionRequestHandler(){},setPermissionCheckHandler(){}}}}));
      vi.doMock(base+'device-settings',()=>({...actual,DeviceSettingsStore:Settings}));
      vi.doMock(base+'outbox',()=>({EncryptedOutbox:Outbox}));
      vi.doMock(base+'managed-host-port',()=>({ManagedHostPort:Port}));
      vi.doMock(base+'backend-supervisor',()=>({BackendSupervisor:Supervisor}));
      vi.doMock(base+'owner-session',()=>({LocalOwnerSession:Owner}));
      vi.doMock(base+'owner-auth-client',()=>({OwnerAuthClient:Port}));
      vi.doMock(base+'owner-secret-store',()=>({OwnerSecretStore:Port}));
      vi.doMock(base+'host-client',()=>({HostClient:Host}));
      await import('../../../apps/desktop/electron/main/index');await tick();
      for(const w of windows)w.emit('ready-to-show');await tick();
      count.flush=0;trace.length=0;
    },
    async dispose(){
      // Cleanup cannot stand in for successful product exit.
      disposing=true;saveGate.resolve();stopGate.resolve();
      while(pending.length)pending.shift().resolve({response:2});await tick();
      app.removeAllListeners();
      for(const w of [...live]){w.removeAllListeners();w.destroy();}
      if(tray&&!tray.destroyed)tray.destroy();
      process.off('unhandledRejection',onUnhandled);
      vi.doUnmock('electron');for(const name of boundaryNames)vi.doUnmock(base+name);
      vi.restoreAllMocks();vi.unstubAllGlobals();vi.unstubAllEnvs();
    }};
  return f;
}

async function finish(f:any,c:any,saves=1) {
  f.stopGate.resolve();await tick();
  c('END.NATURAL',1,f.count.final);c('END.WINDOWS',0,f.live.size);c('END.TRAY',1,f.count.trayDestroy);
  c('END.SAVE',saves,f.count.save);c('END.FLUSH',1,f.count.flush);c('END.STOP',1,f.count.stop);
  c('END.ALLCLOSED',1,f.count.allClosed);c('END.DESTROY.ONCE',true,f.windows.every((w:any)=>w.destroys===1));
  c('END.QUIT.BOUNDED',5,f.count.quit,'lte');
  const stopped=f.trace.indexOf('stop_done');
  c('END.ORDER',true,stopped>=0&&f.trace.filter((x:string)=>x.startsWith('destroy:')).every((x:string)=>f.trace.indexOf(x)>stopped));
}

it('R9-Q01 | quit waits for flush and owned stop; repeated requests and final-window reentry',()=>scenario('R9-Q01',{},async(f,c)=>{
  f.holdSave();c('CLOSE.CANCELLED',true,f.main.close().defaultPrevented);await tick();
  c('FLUSH.WAIT.SAVE',1,f.count.save);c('FLUSH.WAIT.OUTBOX',0,f.count.flush);c('FLUSH.WAIT.STOP',0,f.count.stop);
  c('FLUSH.WAIT.WINDOWS',2,f.live.size);c('FLUSH.WAIT.TRAY',0,f.count.trayDestroy);c('FLUSH.WAIT.EXIT',0,f.count.final);
  c('REPEAT.CLOSE',true,f.main.close().defaultPrevented);f.trayQuit();f.trayQuit();await tick();c('REPEAT.SAVE',1,f.count.save);
  f.saveGate.resolve();await tick();c('STOP.WAIT.COUNT',1,f.count.stop);c('STOP.WAIT.FLUSH',1,f.count.flush);
  c('STOP.WAIT.WINDOWS',2,f.live.size);c('STOP.WAIT.EXIT',0,f.count.final);c('QUIT.NO.PROMPT',0,f.prompts.length);
  c('ORDER.FLUSH',true,f.trace.indexOf('save_done')<f.trace.indexOf('flush')&&f.trace.indexOf('flush')<f.trace.indexOf('stop_enter'));
  await finish(f,c);c('HINT.UNCHANGED',false,f.persisted.closeHintShown);c('NO.HIDE',0,f.main.hides);
}));

it('R9-Q02 | previously acknowledged quit with companion disabled',()=>scenario('R9-Q02',{closeHintShown:true,companionVisible:false},async(f,c)=>{
  f.main.close();await tick();c('PENDING.WINDOW',1,f.live.size);c('PENDING.EXIT',0,f.count.final);c('NO.PROMPT',0,f.prompts.length);await finish(f,c);
}));

it('R9-Q03 | hide first hint saves before hide, second close then virtual Tray shutdown',()=>scenario('R9-Q03',{closePolicy:'hide_to_tray'},async(f,c)=>{
  f.holdSave();f.main.close();await tick();c('HINT.BUTTONS',true,JSON.stringify(f.prompts[0]?.buttons)==='["知道了"]');
  c('HINT.VISIBLE',true,f.main.visible);c('HINT.NO.SAVE',0,f.count.save);f.respond(0);await tick();
  c('SAVE.WAIT.VISIBLE',true,f.main.visible);c('SAVE.WAIT.STOP',0,f.count.stop);f.saveGate.resolve();await tick();
  c('HINT.SAVED',true,f.persisted.closeHintShown);c('HINT.HIDDEN',false,f.main.visible);
  f.main.show();f.main.close();await tick();c('SECOND.HIDES',2,f.main.hides);c('SECOND.PROMPTS',1,f.prompts.length);c('SECOND.STOP',0,f.count.stop);
  f.trayQuit();await tick();await finish(f,c,2);
}));

it('R9-Q04 | ask first hint priority, then cancel, hide and explicit quit',()=>scenario('R9-Q04',{closePolicy:'ask_every_time'},async(f,c)=>{
  f.main.close();await tick();c('FIRST.INFO',true,f.prompts[0]?.type==='info');f.respond(0);await tick();
  c('FIRST.SAVED',true,f.persisted.closeHintShown);c('FIRST.HIDDEN',false,f.main.visible);
  f.main.show();f.main.close();await tick();const q=f.prompts[1];
  c('ASK.BUTTONS',true,JSON.stringify(q?.buttons)==='["隐藏到托盘","退出","取消"]');c('ASK.DEFAULT',0,q.defaultId);c('ASK.CANCEL',2,q.cancelId);
  f.respond(2);await tick();c('CANCEL.VISIBLE',true,f.main.visible);c('CANCEL.STOP',0,f.count.stop);
  f.main.close();await tick();f.respond(0);await tick();c('HIDE.VISIBLE',false,f.main.visible);c('HIDE.STOP',0,f.count.stop);
  f.main.show();f.main.close();await tick();f.respond(1);await tick();await finish(f,c,2);
}));

it('R9-Q05 | late first-hint reply after completed quit cannot save or hide',()=>scenario('R9-Q05',{closePolicy:'hide_to_tray'},async(f,c)=>{
  f.main.close();await tick();c('PENDING.PROMPT',1,f.prompts.length);f.trayQuit();await tick();await finish(f,c);
  f.respond(0);await tick();c('LATE.SAVE',1,f.count.save);c('LATE.HIDE',0,f.main.hides);c('LATE.HINT',false,f.persisted.closeHintShown);c('LATE.EXIT',1,f.count.final);
}));

it('R9-Q06 | late ask reply on externally destroyed main is ignored',()=>scenario('R9-Q06',{closePolicy:'ask_every_time',closeHintShown:true},async(f,c)=>{
  f.main.close();await tick();c('PENDING.PROMPT',1,f.prompts.length);f.main.destroy();f.respond(0);await tick();
  c('LATE.HIDE',0,f.main.hides);c('LATE.SAVE',0,f.count.save);c('LATE.STOP',0,f.count.stop);c('LATE.NO.EXIT',0,f.count.final);
  c('REMAINING.COMPANION',1,f.live.size);
  // Teardown of this destroyed-window boundary is separately recorded, never a quit pass.
}));

it('R9-Q07 | owned stop rejection retains resources, coalesces requests, redacts error',()=>scenario('R9-Q07',{closeHintShown:true},async(f,c)=>{
  f.main.close();await tick();f.stopGate.reject(new Error('R9_PRIVATE_VIRTUAL_STOP_DETAIL'));await tick();
  c('REJECT.NO.EXIT',0,f.count.final);c('REJECT.WINDOWS',2,f.live.size);c('REJECT.TRAY',0,f.count.trayDestroy);
  f.main.close();f.trayQuit();const e=cancelEvent();f.app.emit('before-quit',e);await tick();
  c('REPEAT.CANCELLED',true,e.defaultPrevented);c('REPEAT.STOP',1,f.count.stop);c('REPEAT.SAVE',1,f.count.save);c('REPEAT.FLUSH',1,f.count.flush);
  c('REJECT.SAFE.CODE',true,JSON.stringify(f.consoleErrors)==='[["desktop_shutdown_failed"]]');
  c('REJECT.NO.PRIVATE',true,!JSON.stringify(f.consoleErrors).includes('R9_PRIVATE_VIRTUAL_STOP_DETAIL'));
}));

it('R9-Q08 | virtual session-end with unseen hint and companion disabled',()=>scenario('R9-Q08',{closePolicy:'hide_to_tray',companionVisible:false},async(f,c)=>{
  f.main.emit('session-end');await tick();c('PENDING.WINDOW',1,f.live.size);c('NO.PROMPT',0,f.prompts.length);c('PENDING.EXIT',0,f.count.final);await finish(f,c);
}));
