// R10-only mechanical external-boundary fixture from independent R9; no old business nodes.
import {EventEmitter} from 'node:events';
import {vi} from 'vitest';
const tick = async () => { for (let n=0;n<90;n++) await Promise.resolve(); };
const cancelEvent = () => ({defaultPrevented:false,preventDefault(){this.defaultPrevented=true;}});
function deferred<T=void>() {
  let resolve!:(value:T)=>void, reject!:(reason:Error)=>void;
  const promise=new Promise<T>((ok,no)=>{resolve=ok;reject=no;});
  return {promise,resolve,reject};
}
const base='../../../apps/desktop/electron/main/';
const boundaryNames=['device-settings','outbox','managed-host-port','backend-supervisor','owner-session','owner-auth-client','owner-secret-store','host-client'];
export function makeFixture(overrides:Record<string,unknown>, origin="", companionOrigin=origin) {
  vi.resetModules(); const handlers=new Map<string,any>();
  const app:any=new EventEmitter(), live=new Set<any>(), windows:any[]=[], sent:any[]=[], trace:string[]=[], unhandled:any[]=[];
  const count={start:0,establish:0,save:0,flush:0,stop:0,recover:0,revoke:0,refresh:0,enqueue:0,quit:0,final:0,allClosed:0,trayDestroy:0};
  const saveGate=deferred(), stopGate=deferred();
  let hold=false, disposing=false, depth=0, persisted:any, menu:any[]=[], tray:any;
  const prompts:any[]=[], pending:any[]=[];
  const onUnhandled=(e:any)=>unhandled.push(e);
  process.on('unhandledRejection',onUnhandled);
  class Window extends EventEmitter {
    title:string; destroyed=false; visible=false; hides=0; destroys=0; shows=0; focuses=0;
    webContents={mainFrame:{url:origin||"file:///r10-virtual/index.html"},setWindowOpenHandler:()=>{},on:()=>{},send:(_channel:string,value:any)=>sent.push(value)};
    constructor(options:any){super();this.title=options.title;this.webContents.mainFrame.url=(this.title==='Maris'?origin:companionOrigin)||"file:///r10-virtual/index.html";windows.push(this);live.add(this);}
    show(){this.shows++;this.visible=true;} hide(){if(this.destroyed)throw Error('invalid_window_operation');this.visible=false;this.hides++;}
    focus(){this.focuses++;} setAlwaysOnTop(){} async loadFile(){} async loadURL(){}
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
  const f:any={app,live,windows,sent,count,trace,unhandled,saveGate,stopGate,prompts,consoleErrors,handlers,
    get main(){return windows.find(w=>w.title==='Maris');},get tray(){return tray;},
    get persisted(){return {...persisted};}, holdSave(){hold=true;},
    respond(response:number){const gate=pending.shift();if(!gate)throw Error('missing_prompt');gate.resolve({response});},
    trayQuit(){const entry=menu.find(m=>m.label==='退出');if(!entry)throw Error('missing_tray_entry');entry.click();},
    async start(){
      vi.stubEnv('MARIS_E2E','');vi.stubEnv('MARIS_E2E_EXIT_MS','');vi.stubEnv('MARIS_EXTERNAL_HOST_URL','');vi.stubEnv('MARIS_EXTERNAL_HOST_NONCE','');
      for(const name of ['MAIN_WINDOW','COMPANION_WINDOW']){vi.stubGlobal(name+'_VITE_DEV_SERVER_URL',name==='MAIN_WINDOW'?origin:companionOrigin);vi.stubGlobal(name+'_VITE_NAME',name.toLowerCase());}
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
      vi.doMock('electron',()=>({app,BrowserWindow:Window,Tray,dialog:{showMessageBox:dialog},ipcMain:{handle:(channel:string,handler:any)=>handlers.set(channel,handler)},
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
      app.removeAllListeners(); handlers.clear();
      for(const w of [...live]){w.removeAllListeners();w.destroy();}
      if(tray&&!tray.destroyed)tray.destroy();
      process.off('unhandledRejection',onUnhandled);
      vi.doUnmock('electron');for(const name of boundaryNames)vi.doUnmock(base+name);
      vi.restoreAllMocks();vi.unstubAllGlobals();vi.unstubAllEnvs();
    }};
  return f;
}

