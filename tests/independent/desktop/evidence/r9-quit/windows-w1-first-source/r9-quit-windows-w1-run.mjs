import fs from 'node:fs';
import path from 'node:path';
import {createHash,randomUUID} from 'node:crypto';
import {createRequire} from 'node:module';
import {spawn,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const own=path.dirname(fileURLToPath(import.meta.url));
const repo=path.resolve(own,'../../..');
const ev=path.join(own,'evidence/r9-quit');
const plan=JSON.parse(fs.readFileSync(path.join(ev,'windows-plan.json'),'utf8'));
const ext='C:/MarisQuitR7/R7-20261014-191500';
const workspace=path.join(ext,'workspace');
const packageRoot=path.join(workspace,'apps/desktop/out/Maris-win32-x64');
const exe=path.join(packageRoot,'Maris.exe');
const resources=path.join(packageRoot,'resources');
const pwsh='C:/Users/xuhaolin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe';
const profile=path.join(plan.externalRoot,'profile-main');
const osEnv=path.join(plan.externalRoot,'os-env');
const out=path.join(ev,'windows-W1');
const sha=b=>createHash('sha256').update(b).digest('hex');
const must=(ok,code)=>{if(!ok){const e=new Error(code);e.safeCode=code;throw e;}};
const writeNew=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
function boundary(p){
 const absolute=path.resolve(p);must(absolute===path.resolve('C:/MarisC12')||absolute.startsWith(path.resolve('C:/MarisC12')+path.sep),'external_boundary');
 let cursor=absolute;while(cursor!==path.dirname(cursor)){if(fs.existsSync(cursor))must(!fs.lstatSync(cursor).isSymbolicLink()&&fs.realpathSync(cursor).toLowerCase()===cursor.toLowerCase(),'external_reparse');cursor=path.dirname(cursor);}
 return absolute;
}
must(!fs.existsSync(out),'first_evidence_exists');
must(fs.readFileSync(path.join(plan.externalRoot,'r9-owned-marker.txt'),'utf8')==='P4-C12-R9-QUIT 20261016-011200','virtual_root_owner_changed');
must(!fs.existsSync(profile),'new_profile_exists');
must(fs.readFileSync(path.join(repo,'docs/coordination/control.md'),'utf8').includes('2026-10-16T00:51:00+08:00'),'control_changed');
const startAudit=JSON.parse(fs.readFileSync(path.join(ev,'start-audit.json'),'utf8'));
for(const [name,digest] of Object.entries(startAudit.artifacts))must(sha(fs.readFileSync(path.join(workspace,name)))===digest,'fixed_artifact_changed');
for(const line of fs.readFileSync(path.join(ev,'windows-w1-source.sha256'),'utf8').trimEnd().split(/\r?\n/)){const [name,digest]=line.split('\t');must(sha(fs.readFileSync(path.join(own,name)))===digest,'runner_source_changed');}
boundary(plan.externalRoot);fs.mkdirSync(plan.externalRoot,{recursive:true});
for(const p of [profile,osEnv,...['appdata','localappdata','temp'].map(n=>path.join(osEnv,n))]){boundary(p);fs.mkdirSync(p);}
fs.mkdirSync(out);
const sourceSettings=fs.readFileSync(path.join(repo,'apps/desktop/electron/main/device-settings.ts'),'utf8');
// A new virtual device fixture; no product source or real device setting is edited.
must(sourceSettings.includes('closePolicy: "hide_to_tray"'),'default_contract_changed');
const settings={schemaVersion:1,backendMode:'managed',closePolicy:'quit',closeHintShown:false,theme:'system',reducedMotion:false,privacyMode:false,companionVisible:true,companionAlwaysOnTop:false,companionAppearance:'daily_finance',companionFallback:false,mainBounds:null,companionBounds:null,launchAtLogin:false,externalFullscreenSupported:false,externalFullscreenEnabled:false,outboxVersion:1};
fs.writeFileSync(path.join(profile,'device-settings.json'),JSON.stringify(settings)+'\n',{flag:'wx'});
const marker=randomUUID();fs.writeFileSync(path.join(plan.externalRoot,'owner-marker.txt'),marker,{flag:'wx'});
const start=new Date().toISOString();const clock=performance.now();let seq=0,root=null,browser=null,rootExit=null,rootError=null,timer=null,stage='start',firstFailure=null,cleanupError=null,forced=false,timeout=false;
let known=[],latest=null,stdoutBytes=0,stderrBytes=0,stderrText='',consoleEvents=[],pageErrors=0,cdpPort=null,normalClose=false;
const journal=fs.openSync(path.join(out,'journal.jsonl'),'wx');
function record(stage,details={}){const b=Buffer.from(JSON.stringify({seq:++seq,event:stage,at:new Date().toISOString(),elapsedMs:performance.now()-clock,details})+'\n');fs.writeSync(journal,b);fs.fsyncSync(journal);}
const safe=v=>typeof v==='boolean'||typeof v==='number'&&Number.isFinite(v)||['online','managed','daily_finance','idle','unknown','system','dark','on','off','file:'].includes(v)?v:'unknown';
const assertionIds=new Set();
async function check(id,expected,observe){must(!assertionIds.has(id),'duplicate_assertion_id');assertionIds.add(id);record('assert_enter',{id,expected:safe(expected),operator:'eq',stage});let actual;try{actual=safe(await observe());}catch(e){record('assert_fail',{id,expected:safe(expected),actual:'unknown',operator:'eq',observationStage:stage,errorKind:['Error','TypeError','TimeoutError'].includes(e.name)?e.name:'other'});e.gateId=id;throw e;}record(actual===expected?'assert_pass':'assert_fail',{id,expected:safe(expected),actual,operator:'eq',stage});if(actual!==expected){const e=new Error('assertion_failed');e.safeCode='assertion_failed';e.gateId=id;throw e;}return actual;}
async function observePage(page,prefix){
 const end=performance.now()+5000;let sample=null;
 do{
  try{sample=await page.evaluate(()=>{
   const entries={DAILY:'#daily-title',SHELL:'main.shell',NAV:'nav[aria-label="模块导航"]',AGENT:'aside[aria-label="统一 Agent 面板"]'};
   const read=selector=>{const all=[...document.querySelectorAll(selector)],e=all[0];let visible=!!e;if(e){let n=e;while(n){const s=getComputedStyle(n);if(n.hidden||s.display==='none'||s.visibility==='hidden')visible=false;n=n.parentElement;}visible&&=e.getClientRects().length>0;}return{exists:!!e,count:all.length,visible};};
   return{elements:Object.fromEntries(Object.entries(entries).map(([k,v])=>[k,read(v)])),hash:['#/daily','#/settings','#/',''].includes(location.hash)?location.hash:'other',readyState:['loading','interactive','complete'].includes(document.readyState)?document.readyState:'unknown'};
  });}catch(e){record('page_observation_error',{id:prefix,stage,errorKind:['Error','TypeError','TimeoutError'].includes(e.name)?e.name:'other'});throw e;}
  if(Object.values(sample.elements).every(v=>v.exists&&v.count===1&&v.visible)&&sample.readyState==='complete')break;
  await sleep(75);
 }while(performance.now()<end);
 record('page_final_sample',{id:prefix,sample,observationLimitMs:5000});
 for(const [name,v]of Object.entries(sample.elements)){await check(prefix+'-'+name+'-EXISTS',true,()=>v.exists);await check(prefix+'-'+name+'-COUNT',1,()=>v.count);await check(prefix+'-'+name+'-VISIBLE',true,()=>v.visible);}
 await check(prefix+'-HASH',true,()=>sample.hash==='#/daily');await check(prefix+'-READY',true,()=>sample.readyState==='complete');
}
function os(action='snapshot',button=''){
 const r=spawnSync(pwsh,['-NoProfile','-NonInteractive','-File',path.join(own,'r9-quit-windows-os.ps1'),'-Action',action,'-RootPid',String(root.pid),'-ExpectedParentPid',String(process.pid),'-StartedUtc',start,'-KnownJson',JSON.stringify(known),...(button?['-Button',button]:[])],{encoding:'utf8',shell:false,windowsHide:true,timeout:8000,maxBuffer:1024*1024});
 must(r.status===0,'os_observer_error');const value=JSON.parse(r.stdout);
 if(action==='snapshot'){latest=value;known=[...new Map([...known,...value.owned].map(p=>[p.pid,p])).values()];record('owned_snapshot',{rootVerified:value.rootVerified,rootPresent:value.rootPresent,owned:value.owned,listeners:value.listeners,windowCount:value.windowCount});}
 return value;
}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function wait(fn,ms,code){const at=performance.now();while(performance.now()-at<ms){const v=await fn();if(v)return v;if(rootExit||rootError)break;await sleep(75);}must(false,code);}
function forceOwned(){
 const snap=os();if(!snap.rootPresent)return;must(snap.rootVerified,'cleanup_identity_unknown');
 must(fs.readFileSync(path.join(plan.externalRoot,'owner-marker.txt'),'utf8')===marker,'cleanup_marker_unknown');
 forced=true;const r=spawnSync('taskkill.exe',['/PID',String(root.pid),'/T','/F'],{shell:false,windowsHide:true,encoding:'utf8',timeout:8000});record('owned_force_cleanup',{status:r.status});
}
record('launch_plan',{id:'W1',ordinal:1,maxProducts:8,maxMs:120000,exitMode:'owned_native_close_quit_fixture',profileNew:true,markerDigest:sha(marker),directSpawn:true,osSettingsSuppressed:true});
try{
 const env={...process.env,MARIS_E2E:'1',MARIS_E2E_USER_DATA:profile,MARIS_HOST_PROJECT_ROOT:resources,MARIS_PYTHON_EXECUTABLE:path.join(repo,'.venv/Scripts/python.exe'),PYTHONDONTWRITEBYTECODE:'1',APPDATA:path.join(osEnv,'appdata'),LOCALAPPDATA:path.join(osEnv,'localappdata'),TEMP:path.join(osEnv,'temp'),TMP:path.join(osEnv,'temp')};
 for(const k of ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE','MARIS_E2E_EXIT_MS','ELECTRON_ENABLE_LOGGING','ELECTRON_LOG_FILE','MARIS_EXTERNAL_HOST_URL','MARIS_EXTERNAL_HOST_NONCE'])delete env[k];
 root=spawn(exe,['--remote-debugging-address=127.0.0.1','--remote-debugging-port=0'],{cwd:packageRoot,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});
 must(root.pid,'root_pid_missing');record('root_started',{pid:root.pid,startedUtc:start});
 root.stdout.on('data',b=>{stdoutBytes+=b.length;});root.stderr.on('data',b=>{stderrBytes+=b.length;if(stderrText.length<1048576)stderrText+=b.toString('utf8');});
 root.once('exit',(code,signal)=>{rootExit={code,signal:signal??null,elapsedMs:performance.now()-clock};record('root_exit',rootExit);});root.once('error',()=>{rootError='spawn_error';});
 timer=setTimeout(()=>{timeout=true;try{forceOwned();}catch{cleanupError='deadline_cleanup_unverified';}},90000);
 stage='ownership';await check('W1-OWN-ROOT',true,()=>os().rootVerified);
 stage='cdp';const active=path.join(profile,'DevToolsActivePort');await wait(()=>fs.existsSync(active)&&fs.statSync(active).size>0,15000,'cdp_file_missing');
 const lines=fs.readFileSync(active,'utf8').trim().split(/\r?\n/);cdpPort=Number(lines[0]);must(Number.isInteger(cdpPort)&&cdpPort>0&&cdpPort<65536&&lines[1].startsWith('/devtools/browser/'),'cdp_file_invalid');
 await check('W1-CDP-OWNED-LOOPBACK',true,()=>{const s=os();const list=s.listeners.filter(l=>l.port===cdpPort);return list.length>0&&list.every(l=>l.loopback&&s.owned.some(p=>p.pid===l.pid));});
 const require=createRequire(path.join(workspace,'node_modules/playwright/package.json'));const {chromium}=require('playwright');browser=await chromium.connectOverCDP('http://127.0.0.1:'+cdpPort,{timeout:10000});for(const c of browser.contexts()){c.setDefaultTimeout(5000);c.setDefaultNavigationTimeout(5000);}
 const bind=p=>{p.on('console',m=>{const t=m.text();consoleEvents.push({type:['error','warning','log'].includes(m.type())?m.type():'other',secretPattern:/eyJ[A-Za-z0-9_-]{10,}\.|Bearer\s+[A-Za-z0-9_-]{16,}|VIRTUAL_R8R1_BODY_CANARY/.test(t),internalPath:/[A-Z]:\\|\.py:[0-9]|node_modules/.test(t)});});p.on('pageerror',()=>{pageErrors++;});};
 for(const c of browser.contexts()){for(const p of c.pages())bind(p);c.on('page',bind);}
 const pages=()=>browser.contexts().flatMap(c=>c.pages());
 const main=await wait(async()=>{for(const p of pages())if(await p.title()==='Maris')return p;return null;},10000,'main_page_missing');
 const companion=await wait(async()=>{for(const p of pages())if(await p.title()==='毛毛')return p;return null;},10000,'companion_page_missing');
 stage='security';
 for(const [label,page] of [['MAIN',main],['COMPANION',companion]]){
  await check(`W1-SEC-${label}-NODE`,true,()=>page.evaluate(()=>['require','process','Buffer','ipcRenderer'].every(k=>typeof window[k]==='undefined')));
  await check(`W1-SEC-${label}-FILE`, 'file:',()=>page.evaluate(()=>location.protocol));
 }
 await check('W1-SEC-MAIN-BRIDGE',true,()=>main.evaluate(()=>{const keys={runtime:['getSnapshot','recover','subscribe'],window:['perform'],modules:['list'],settings:['update'],outbox:['enqueue'],external:['open']};return Object.keys(window.maris).sort().join(',')===Object.keys(keys).sort().join(',')&&Object.entries(keys).every(([k,v])=>Object.keys(window.maris[k]).sort().join(',')===v.sort().join(','));}));
 await check('W1-SEC-COMPANION-BRIDGE',true,()=>companion.evaluate(()=>Object.keys(window.companion).sort().join(',')==='getState,openMain'&&typeof window.maris==='undefined'));
 await check('W1-CSP-CONTRACT',true,()=>main.evaluate(()=>{const t=document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content??'';return ["script-src 'self'","connect-src 'none'","object-src 'none'","frame-src 'none'"].every(s=>t.includes(s));}));
 await main.evaluate(()=>{const s=document.createElement('script');s.textContent='window.__R8R1_INLINE_EXECUTED__=true';document.body.append(s);s.remove();});
 await check('W1-CSP-INLINE-BLOCKED',true,()=>main.evaluate(()=>window.__R8R1_INLINE_EXECUTED__!==true));
 await main.evaluate(()=>window.open('about:blank','r8r1_virtual_unknown'));
 await sleep(150);await check('W1-UNKNOWN-WINDOW-DENIED',2,()=>pages().length);
 stage='runtime';await wait(async()=>await main.evaluate(async()=>{const r=await window.maris.runtime.getSnapshot();return r.state==='online'&&r.authenticated;}),35000,'managed_online_timeout');
 await check('W1-RUNTIME-ONLINE',true,()=>main.evaluate(async()=>{const r=await window.maris.runtime.getSnapshot();return r.state==='online'&&r.mode==='managed'&&r.authenticated&&r.errorCode===null;}));
 await check('W1-MODULE-CANONICAL',true,()=>main.evaluate(async()=>{const m=await window.maris.modules.list();return m.length===1&&m[0].module_id==='daily_finance'&&m[0].enabled&&m[0].profile_ids.includes('daily_finance.assistant@1');}));
 await observePage(main,'W1-PAGE');
 await check('W1-COMPANION-STATE',true,()=>companion.evaluate(async()=>{const s=await window.companion.getState();return s.state==='idle'&&s.appearanceId==='daily_finance';}));
 const chunk=await main.evaluate(()=>({protocol:location.protocol,completedJs:performance.getEntriesByType('resource').filter(e=>e.name.endsWith('.js')&&e.responseEnd>0).length,dailyChunkCompleted:performance.getEntriesByType('resource').some(e=>/DailyFinancePage.*\.js(?:$|\?)/.test(e.name)&&e.responseEnd>0),complete:document.readyState==='complete',dailyPresent:!!document.querySelector('#daily-title')}));
 record('real_chunk_unverified',{reason:'current_real_daily_module_already_loaded_when_observer_attached_no_fault_injected',protocol:'file:',completedJs:chunk.completedJs,pageComplete:chunk.complete,dailyPresent:chunk.dailyPresent,dailyChunkCompleted:chunk.dailyChunkCompleted,injectionCount:0});
 stage='ipc';const settingsBefore=sha(fs.readFileSync(path.join(profile,'device-settings.json')));
 await check('W1-IPC-INVALID-REJECTED',4,()=>main.evaluate(async()=>{let n=0;for(const fn of [()=>window.maris.settings.update({theme:'virtual_invalid'}),()=>window.maris.window.perform('virtual_invalid'),()=>window.maris.external.open('virtual_invalid'),()=>window.maris.outbox.enqueue({draftId:'not_uuid',body:'virtual'})]){try{await fn();}catch{n++;}}return n;}));
 await check('W1-IPC-NO-SETTINGS-WRITE',true,()=>settingsBefore===sha(fs.readFileSync(path.join(profile,'device-settings.json'))));
 await check('W1-IPC-NO-EXTRA-WINDOW',2,()=>pages().length);
 const draftId=randomUUID();let eventId=null;
 await check('W1-OUTBOX-SAME-ID',true,()=>main.evaluate(async id=>{const a=await window.maris.outbox.enqueue({draftId:id,body:'VIRTUAL_R8R1_BODY_CANARY'});const b=await window.maris.outbox.enqueue({draftId:id,body:'VIRTUAL_R8R1_BODY_CANARY'});return {same:a.clientEventId===b.clientEventId,id:a.clientEventId};},draftId).then(v=>{eventId=v.id;return v.same;}));
 writeNew(path.join(plan.externalRoot,'continuity.json'),{draftId,eventId,body:'VIRTUAL_R8R1_BODY_CANARY'});
 stage='settings';await main.getByLabel('主题',{exact:true}).selectOption('dark');await main.getByLabel('隐私模式',{exact:true}).check();await main.getByRole('link',{name:'设置',exact:true}).click();
 await check('W1-SETTINGS-UI',true,()=>main.evaluate(()=>document.querySelector('main.shell')?.dataset.theme==='dark'&&document.querySelector('main.shell')?.dataset.privacy==='on'&&location.hash==='#/settings'));
 await check('W1-SETTINGS-PERSISTED',true,async()=>wait(()=>{const s=JSON.parse(fs.readFileSync(path.join(profile,'device-settings.json'),'utf8'));return s.theme==='dark'&&s.privacyMode;},2000,'settings_save_timeout'));
 await check('W1-RENDERER-STORAGE-NO-SECRET',true,()=>main.evaluate(()=>{const text=JSON.stringify({...localStorage})+JSON.stringify({...sessionStorage});return !/VIRTUAL_R8R1_BODY_CANARY|refreshToken|password|eyJ[A-Za-z0-9_-]{10,}\./.test(text);}));
 stage='host-boundary';const snap=os();await check('W1-OWNED-LISTENERS-LOOPBACK',true,()=>snap.listeners.length>0&&snap.listeners.every(l=>l.loopback));
 const ports=[...new Set(snap.listeners.filter(l=>snap.owned.some(p=>p.pid===l.pid&&p.kind==='python')).map(l=>l.port))];must(ports.length===1,'host_listener_ambiguous');
 await check('W1-HOST-NONCE-DENIED',503,async()=>{const r=await fetch(`http://127.0.0.1:${ports[0]}/api/v1/desktop/readyz`,{headers:{'X-Maris-Startup-Nonce':'virtual_invalid_nonce'},signal:AbortSignal.timeout(2000)});return r.status;});
 await check('W1-HOST-UNAUTH-DENIED',true,async()=>{const r=await fetch(`http://127.0.0.1:${ports[0]}/api/v1/modules`,{signal:AbortSignal.timeout(2000)});return [401,403].includes(r.status);});
 await check('W1-CONSOLE-NO-SECRET',true,()=>consoleEvents.every(e=>!e.secretPattern));
 stage='recover';record('recover_enter',{expectedCalls:1});await main.evaluate(()=>window.maris.runtime.recover());record('recover_return');await check('W1-RECOVER-ONLINE',true,()=>main.evaluate(async()=>{const r=await window.maris.runtime.getSnapshot();return r.state==='online'&&r.authenticated;}));await main.getByRole('link',{name:'日常财务',exact:true}).click({timeout:5000});await observePage(main,'W1-RECOVER-PAGE');await check('W1-RECOVER-THEME',true,()=>main.evaluate(()=>document.querySelector('main.shell')?.dataset.theme==='dark'&&document.querySelector('main.shell')?.dataset.privacy==='on'));
 stage='normal-close';const closed=os('close');record('normal_close_source',{...closed,method:'owned_unique_main_WM_CLOSE',exitTimerAbsent:!('MARIS_E2E_EXIT_MS' in env)});normalClose=closed.closePosted;await check('W1-NATIVE-CLOSE-POSTED',true,()=>normalClose);const closeDeadline=Date.parse(closed.postedUtc)+10000;while(!rootExit&&Date.now()<closeDeadline)await sleep(75);await check('W1-NORMAL-EXIT-OBSERVED',true,()=>!!rootExit);
 await check('W1-NORMAL-EXIT-CODE',0,()=>rootExit.code);
 const natural=os();record('normal_exit_resources',{elapsedSinceCloseMs:Date.now()-Date.parse(closed.postedUtc),owned:natural.owned.length,listeners:natural.listeners.length,windowCount:natural.windowCount});
 await check('W1-NORMAL-OWNED-GONE',0,()=>natural.owned.length);await check('W1-NORMAL-LISTENERS-GONE',0,()=>natural.listeners.length);await check('W1-NORMAL-WINDOWS-GONE',0,()=>natural.windowCount);
 await check('W1-NORMAL-RESOURCE-DEADLINE',true,()=>Date.now()<=closeDeadline);
}catch(e){firstFailure={stage,id:e.gateId??null,kind:['AssertionError','TypeError','Error'].includes(e.name)?e.name:'other',code:e.safeCode??'operation_error'};record('first_failure',firstFailure);}
finally{
 clearTimeout(timer);stage='cleanup';
 try{if(root&&!rootExit){forceOwned();await wait(()=>!!rootExit,3000,'cleanup_exit_timeout');}if(root){const after=os();must(after.owned.length===0&&after.listeners.length===0&&after.windowCount===0,'owned_resources_remain');record('cleanup_confirmed',{registered:known.length,remainingOwned:0,remainingListeners:0,remainingWindows:0});}}
 catch(e){cleanupError=e.safeCode??'cleanup_unverified';record('cleanup_failure',{code:cleanupError});}
 try{if(browser)await Promise.race([browser.close(),sleep(2000)]);}catch{record('cdp_disconnect_unverified');}
 const gpuOverlayErrors=(stderrText.match(/GetGpuDriverOverlayInfo: Failed to retrieve video device/g)||[]).length;record('native_stderr_summary',{rawBytes:stderrBytes,gpuOverlayErrors,recognizedMessage:gpuOverlayErrors?'GetGpuDriverOverlayInfo: Failed to retrieve video device':null,rawNotPersisted:true});
 const result={id:'W1',startedUtc:start,durationMs:performance.now()-clock,firstFailure,cleanupError,timeout,forced,rootPid:root?.pid??null,rootExit,normalClose,registered:known,stdoutBytes,stderrBytes,gpuOverlayErrors,rawLogsSaved:false,consoleEvents,pageErrors,productStarts:1,helperStarts:0,chunkInjectionCount:0,profileAlias:'new_R9_main',remainingOwned:latest?.owned?.length??null,remainingListeners:latest?.listeners?.length??null,remainingWindows:latest?.windowCount??null,passed:!firstFailure&&!cleanupError&&!timeout&&!forced&&rootExit?.code===0};
 record('runner_finished',{passed:result.passed,durationMs:result.durationMs});writeNew(path.join(out,'result.json'),result);fs.closeSync(journal);process.stdout.write(JSON.stringify({id:'W1',passed:result.passed,firstFailure,cleanupError,productStarts:1})+'\n');if(!result.passed)process.exitCode=1;
}
