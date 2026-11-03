import fs from 'node:fs';import path from 'node:path';import {spawn}from'node:child_process';import {createRequire}from'node:module';
import cfg from './r11-r1-windows-config.cjs';import identity from './r9-r2-identity.cjs';
import {captured,write,must,sha,sleep}from'./r9-r2-observation.mjs';
const scene=process.argv[2];must(['W4','W5'].includes(scene),'scene_forbidden');
const ev=path.join(cfg.evidence,'windows-'+scene),output=path.join(cfg.ext,'output/'+scene),profile=path.join(cfg.ext,'profile-main');
const osScript=path.join(cfg.own,'r11-r1-windows-os.ps1'),workspace=path.join(cfg.fixed,'workspace'),packageRoot=path.dirname(cfg.product);
must(fs.readFileSync(path.join(cfg.repo,'docs/coordination/control.md'),'utf8').includes(cfg.controlVersion),'control_changed');
must(JSON.parse(fs.readFileSync(path.join(cfg.evidence,scene==='W4'?'helper-H2/process.json':'helper-H3/process.json'),'utf8')).passed,'retention_prior_gate');
const fresh=JSON.parse(fs.readFileSync(path.join(cfg.evidence,'fresh-process-check.json'),'utf8'));must(fresh.passed&&fresh.elevatedAdministrator===false,'ordinary_user_gate');
for(const line of fs.readFileSync(path.join(cfg.evidence,'retention-source.sha256'),'utf8').trimEnd().split('\n')){
 const [name,digest]=line.split('\t');must(sha(fs.readFileSync(path.join(cfg.own,name)))===digest,'source_changed');
}
must(sha(fs.readFileSync(cfg.product))==='c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b','product_changed');
must(identity.noReparse(profile)&&fs.readFileSync(cfg.markerFile,'utf8')===cfg.marker,'profile_boundary');
fs.mkdirSync(ev);fs.mkdirSync(output);
const settingsFile=path.join(profile,'device-settings.json'),beforeSettings=fs.readFileSync(settingsFile),stored=JSON.parse(beforeSettings);
const continuity=JSON.parse(fs.readFileSync(path.join(cfg.ext,'continuity.json'),'utf8'));
const baseline=JSON.parse(fs.readFileSync(path.join(cfg.own,'evidence/r9-r3/helper-H1/native-baseline.json'),'utf8'));
const start=performance.now(),startedUtc=new Date().toISOString(),fd=fs.openSync(path.join(ev,'journal.jsonl'),'wx');
const record=(event,details={})=>{fs.writeSync(fd,JSON.stringify({event,at:new Date().toISOString(),elapsedMs:performance.now()-start,details})+'\n');fs.fsyncSync(fd);};
const ids=new Set(),comparisons=[];let root=null,exit=null,known=[],seq=0,browser=null,firstFailure=null,cleanupError=null,forced=false,finalResources=null,closeReceipt=null,stage='preconditions',secondary=null,secondaryExit=null,secondaryStarted=null,productStarts=0;
const streams=[];
function check(id,expected,actual){must(!ids.has(id),'duplicate_assertion_id');ids.add(id);record('assert_enter',{id,expected});const c={id,expected,actual,passed:expected===actual};comparisons.push(c);record(c.passed?'assert_pass':'assert_fail',c);if(!c.passed)throw Object.assign(new Error('comparison_failed'),{safeCode:'comparison_failed',gateId:id});}
function safeEnum(value,allowed){return allowed.includes(value)?value:'unknown';}
async function bounded(p,ms=5000){let timer;try{return await Promise.race([p,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(new Error('operation_deadline'),{safeCode:'operation_deadline'})),Math.max(1,Math.min(ms,start+100000-performance.now())));})]);}finally{clearTimeout(timer);}}
async function wait(fn,ms,code){const until=Math.min(start+100000,performance.now()+ms);while(performance.now()<until){const v=await bounded(fn());if(v)return v;if(exit)break;await sleep(50);}must(false,code);}
function attachStreams(child,id){const pair={id,stdout:[],stderr:[]};streams.push(pair);for(const key of ['stdout','stderr'])child[key].on('data',b=>pair[key].push(b));}
async function os(action='snapshot',button='',deadline=start+100000,target=root,targetStarted=startedUtc,targetKnown=known){
 const id=scene+'-OS-'+(++seq),receipt=path.join(output,id+'.receipt.json');
 const d=identity.describe({executable:cfg.pwsh,script:osScript,boundary:cfg.own,markerFile:cfg.markerFile,marker:cfg.marker,output,callId:id});
 const args=['-NoProfile','-NonInteractive','-File',d.script,'-Action',action,'-RootPid',String(target.pid),'-ExpectedParentPid',String(process.pid),'-StartedUtc',targetStarted,'-KnownJson',JSON.stringify(targetKnown),'-ReceiptPath',receipt,'-CallId',id,'-Marker',cfg.marker,'-Output',output,'-StageLog',path.join(ev,id+'.stages.jsonl'),...(button?['-Button',button]:[])];
 const result=await captured({exe:cfg.pwsh,args,cwd:output,limitMs:Math.min(8000,Math.floor(deadline-performance.now())),id,record,rawDir:output,canCancel:(child,at)=>{
  if(!fs.existsSync(receipt))return false;const v=JSON.parse(fs.readFileSync(receipt,'utf8'));const ok=identity.receiptCheck(v,d,{pid:child.pid,parentPid:process.pid,receiptPath:receipt,expectedReceiptPath:receipt,startedUtc:at});record('observer_cancel_identity',{id,...ok});return ok.passed&&identity.canonical(v.executable)===d.executable;
 }});
 if(result.status!==0||result.timedOut){let safeDetail=null;try{const parsed=JSON.parse(result.stdout);if(parsed.ok===false)safeDetail={stage:parsed.stage,errorName:parsed.errorName,code:parsed.code,hresult:parsed.hresult??null,nativeErrorCode:parsed.nativeErrorCode??null,statusCode:parsed.statusCode??null,category:parsed.category??null};}catch{}record('os_failed',{id,action,status:result.status,signal:result.signal,error:result.error,timedOut:result.timedOut,safeDetail});throw Object.assign(new Error('os_observer_nonzero'),{safeCode:'os_observer_nonzero'});}
 let v;try{v=JSON.parse(result.stdout);}catch{throw Object.assign(new Error('os_json_invalid'),{safeCode:'os_json_invalid'});}
 if(action==='snapshot'){
  must(Array.isArray(v.owned)&&Array.isArray(v.listeners)&&Number.isInteger(v.windowCount)&&v.resourceStatus==='success','os_schema');
  if(target===root){known=[...new Map([...known,...v.owned].map(x=>[x.pid+':'+x.created,x])).values()];finalResources=v;}
  record('owned_snapshot',{id,...v});
 }else record('native_action',{id,action,...v});return v;
}
async function normalClose(){
 closeReceipt=await os('close','',start+110000);must(closeReceipt.closePosted,'close_not_posted');record('normal_close',{...closeReceipt,timeoutMs:10000,source:'owned_unique_main_WM_CLOSE',exitTimerAbsent:true});
 const deadline=Date.parse(closeReceipt.postedUtc)+10000;
 while(!exit&&Date.now()<deadline)await sleep(25);
 must(exit!==null,'normal_exit_timeout');must(exit.code===0,'normal_exit_nonzero');
 finalResources=await os('snapshot','',Math.min(start+120000,performance.now()+Math.max(1,deadline-Date.now())));
 must(finalResources.owned.length===0&&finalResources.listeners.length===0&&finalResources.windowCount===0,'normal_resources_remaining');
 must(Date.now()<=deadline,'normal_resource_deadline');
}
const env={...process.env,MARIS_E2E:'1',MARIS_E2E_USER_DATA:profile,MARIS_HOST_PROJECT_ROOT:path.join(packageRoot,'resources'),MARIS_PYTHON_EXECUTABLE:path.join(cfg.repo,'.venv/Scripts/python.exe'),PYTHONDONTWRITEBYTECODE:'1',APPDATA:path.join(cfg.ext,'os-env/appdata'),LOCALAPPDATA:path.join(cfg.ext,'os-env/localappdata'),TEMP:path.join(cfg.ext,'os-env/temp'),TMP:path.join(cfg.ext,'os-env/temp')};
for(const k of ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE','MARIS_E2E_EXIT_MS','ELECTRON_ENABLE_LOGGING','ELECTRON_LOG_FILE','MARIS_EXTERNAL_HOST_URL','MARIS_EXTERNAL_HOST_NONCE'])delete env[k];
let watchdog;
try{
 record('launch_plan',{id:scene,seriesOrdinal:scene==='W4'?5:6,maxProducts:8,profile:'W1_content_copy',totalMs:120000,normalExitMs:10000,settingsWritesBeforeSample:0});
 root=spawn(cfg.product,['--remote-debugging-address=127.0.0.1','--remote-debugging-port=0'],{cwd:packageRoot,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});must(root.pid,'spawn_failed');productStarts++;attachStreams(root,scene);record('product_spawn',{id:scene,pid:root.pid,parentPid:process.pid});
 root.once('exit',(code,signal)=>{exit={code,signal:signal??null,at:new Date().toISOString()};record('product_exit',{id:scene,...exit});});root.once('error',e=>record('product_error',{id:scene,name:e.name,code:['ENOENT','EACCES','EPERM'].includes(e.code)?e.code:'unknown'}));
 watchdog=setTimeout(()=>{firstFailure??={stage:'deadline',code:'business_deadline'};record('business_deadline');},100000);
 stage='ownership';check(scene+'-OWN-ROOT',true,(await os()).rootVerified);
 const active=path.join(profile,'DevToolsActivePort');await wait(()=>fs.existsSync(active)&&fs.statSync(active).mtimeMs>=Date.parse(startedUtc)-250,15000,'cdp_current_file_missing');
 const parts=fs.readFileSync(active,'utf8').trim().split(/\r?\n/),port=Number(parts[0]);must(Number.isInteger(port)&&parts[1]?.startsWith('/devtools/browser/'),'cdp_invalid');
 const snap=await os();check(scene+'-CDP-OWNED',true,snap.listeners.some(v=>v.port===port)&&snap.listeners.filter(v=>v.port===port).every(v=>v.loopback&&snap.owned.some(p=>p.pid===v.pid)));
 const require=createRequire(path.join(workspace,'node_modules/playwright/package.json'));const{chromium}=require('playwright');browser=await chromium.connectOverCDP('http://127.0.0.1:'+port,{timeout:8000});for(const c of browser.contexts())c.setDefaultTimeout(5000);
 const pages=()=>browser.contexts().flatMap(c=>c.pages());const main=await wait(async()=>{for(const p of pages())if(await p.title()==='Maris')return p;return null;},10000,'main_missing');
 const companion=await wait(async()=>{for(const p of pages())if(await p.title()==='毛毛')return p;return null;},5000,'companion_missing');
 stage='runtime';await wait(()=>main.evaluate(async()=>{const v=await window.maris.runtime.getSnapshot();return v.state==='online'&&v.authenticated;}),35000,'online_timeout');
 stage='retention_dialog';const decision=await os('dialog',scene==='W4'?'保留':'明确删除');check(scene+'-RETENTION-CHOICE-INVOKED',true,decision.invoked);
 stage='normal_close';await normalClose();
}catch(e){firstFailure??={stage,id:e.gateId??null,name:['Error','TypeError','TimeoutError'].includes(e.name)?e.name:'unknown',code:e.safeCode??'unknown'};record('first_failure',firstFailure);}
finally{
 clearTimeout(watchdog);stage='cleanup';
 try{
  if(root&&!exit){const current=JSON.parse(fs.readFileSync(settingsFile,'utf8'));if(current.closePolicy==='quit')await normalClose();else throw Object.assign(new Error('normal_close_not_available'),{safeCode:'normal_close_not_available'});}
  if(root&&(!finalResources||finalResources.owned.length||finalResources.listeners.length||finalResources.windowCount))finalResources=await os('snapshot','',start+120000);
 }catch(e){record('normal_cleanup_failure',{code:e.safeCode??'unknown'});
  try{if(root&&!exit){const owned=await os('snapshot','',start+113000);must(owned.rootVerified,'cleanup_identity');forced=true;const killed=await captured({exe:path.join(process.env.SystemRoot,'System32/taskkill.exe'),args:['/PID',String(root.pid),'/T','/F'],cwd:output,limitMs:Math.min(3000,Math.floor(start+116000-performance.now())),id:'W2-STOP',record,rawDir:output,canCancel:()=>false});must(killed.status===0,'cleanup_failed');while(!exit&&performance.now()<start+117000)await sleep(25);}finalResources=await os('snapshot','',start+120000);}catch(e2){cleanupError=e2.safeCode??'cleanup_unknown';}
 }
 if(secondary&&!secondaryExit){try{const second=await os('snapshot','',start+113000,secondary,secondaryStarted,[]);must(second.rootVerified,'secondary_cleanup_identity');forced=true;const kill=await captured({exe:path.join(process.env.SystemRoot,'System32/taskkill.exe'),args:['/PID',String(secondary.pid),'/T','/F'],cwd:output,limitMs:Math.min(3000,Math.floor(start+116000-performance.now())),id:'W3-STOP',record,rawDir:output,canCancel:()=>false});must(kill.status===0,'secondary_cleanup_failed');while(!secondaryExit&&performance.now()<start+117000)await sleep(25);const after=await os('snapshot','',start+120000,secondary,secondaryStarted,second.owned);must(!after.owned.length&&!after.listeners.length&&!after.windowCount,'secondary_remaining');}catch(e){cleanupError??=e.safeCode??'secondary_cleanup_unknown';}}

 if(root&&(!finalResources||finalResources.owned.length||finalResources.listeners.length||finalResources.windowCount))cleanupError??='remaining_resources';
 try{if(browser)await Promise.race([browser.close(),sleep(1000)]);}catch{record('cdp_disconnect_unknown');}
 const streamSummary=streams.map(v=>{const result={id:v.id};for(const key of ['stdout','stderr']){const b=Buffer.concat(v[key]);fs.writeFileSync(path.join(output,v.id+'.'+key),b,{flag:'wx'});result[key+'Bytes']=b.length;result[key+'Sha256']=sha(b);}return result;});
 const result={id:scene,passed:!firstFailure&&!cleanupError&&!forced&&exit?.code===0,firstFailure,cleanupError,forced,rootPid:root?.pid??null,exit,secondaryPid:secondary?.pid??null,secondaryExit,productStarts,helperStarts:0,seriesProductStarts:(scene==='W4'?4:5)+productStarts,seriesHelperStarts:scene==='W4'?4:5,durationMs:performance.now()-start,comparisons,known,closeReceipt,remainingOwned:finalResources?.owned.length??null,remainingListeners:finalResources?.listeners.length??null,remainingWindows:finalResources?.windowCount??null,streams:streamSummary};
 write(path.join(ev,'result.json'),result);record('finished',{passed:result.passed});fs.closeSync(fd);console.log(JSON.stringify({passed:result.passed,firstFailure,cleanupError,productStarts}));process.exitCode=result.passed?0:1;
}
