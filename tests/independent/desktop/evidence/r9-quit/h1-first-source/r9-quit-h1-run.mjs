import fs from 'node:fs';import path from 'node:path';import{spawn,spawnSync}from'node:child_process';import{createHash}from'node:crypto';import{fileURLToPath}from'node:url';
const own=path.dirname(fileURLToPath(import.meta.url)),repo=path.resolve(own,'../../..'),ev=path.join(own,'evidence/r9-quit');
const ext='C:/MarisC12/C12-R9-QUIT-20261016-011200',out=path.join(ext,'output/H1'),evidence=path.join(ev,'helper-H1');
const fixed='C:/MarisQuitR7/R7-20261014-191500',exe=path.join(fixed,'workspace/node_modules/electron/dist/electron.exe');
const pwsh='C:/Users/xuhaolin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe';
const must=(ok,code)=>{if(!ok)throw Object.assign(new Error(code),{safeCode:code});};
const sha=v=>createHash('sha256').update(v).digest('hex');
const write=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
must(fs.readFileSync(path.join(repo,'docs/coordination/control.md'),'utf8').includes('2026-10-16T00:51:00+08:00'),'control_changed');
must(JSON.parse(fs.readFileSync(path.join(ev,'windows-W1/result.json'),'utf8')).passed,'w1_not_passed');
must(!fs.existsSync(out)&&!fs.existsSync(evidence),'first_exists');
for(const p of [ext,path.join(ext,'output'),path.join(ext,'profile-main')])must(!fs.lstatSync(p).isSymbolicLink()&&fs.realpathSync(p).toLowerCase()===path.resolve(p).toLowerCase(),'reparse');
must(fs.readFileSync(path.join(ext,'r9-owned-marker.txt'),'utf8')==='P4-C12-R9-QUIT 20261016-011200','owner_marker');
const distManifest=fs.readFileSync(path.join(fixed,'evidence/inputs/electron-dist-final.sha256'));
must(sha(distManifest)==='ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f','dist_manifest_changed');
const distRow=distManifest.toString('utf8').trimEnd().split(/\r?\n/).map(l=>l.split('\t')).find(v=>v[0]==='electron.exe');
must(!!distRow&&sha(fs.readFileSync(exe))===distRow[1],'helper_exe_changed');
for(const line of fs.readFileSync(path.join(ev,'h1-source.sha256'),'utf8').trimEnd().split(/\r?\n/)){const [name,digest]=line.split('\t');must(sha(fs.readFileSync(path.join(own,name)))===digest,'source_changed');}
fs.mkdirSync(out);fs.mkdirSync(evidence);fs.mkdirSync(path.join(ext,'helper-profile-H1'));
const script=path.join(out,'main.cjs');fs.copyFileSync(path.join(own,'r9-quit-h1-native.cjs'),script,fs.constants.COPYFILE_EXCL);
const env={...process.env,APPDATA:path.join(ext,'os-env/appdata'),LOCALAPPDATA:path.join(ext,'os-env/localappdata'),TEMP:path.join(ext,'os-env/temp'),TMP:path.join(ext,'os-env/temp')};
for(const k of ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE','MARIS_E2E','MARIS_E2E_USER_DATA','MARIS_E2E_EXIT_MS','ELECTRON_ENABLE_LOGGING','ELECTRON_LOG_FILE'])delete env[k];
const started=new Date().toISOString(),clock=performance.now();let root,exit=null,known=[],firstFailure=null,forced=false,stdoutBytes=0,stderrBytes=0,timer=null;
const fd=fs.openSync(path.join(evidence,'journal.jsonl'),'wx');let seq=0;
function record(event,details={}){fs.writeSync(fd,JSON.stringify({seq:++seq,event,at:new Date().toISOString(),elapsedMs:performance.now()-clock,details})+'\n');fs.fsyncSync(fd);}
function snapshot(){const r=spawnSync(pwsh,['-NoProfile','-NonInteractive','-File',path.join(own,'r9-quit-helper-os.ps1'),'-RootPid',String(root.pid),'-ExpectedParentPid',String(process.pid),'-StartedUtc',started,'-KnownJson',JSON.stringify(known)],{shell:false,windowsHide:true,encoding:'utf8',timeout:8000});must(r.status===0,'ownership_observer_error');const s=JSON.parse(r.stdout);known=[...new Map([...known,...s.owned].map(p=>[p.pid,p])).values()];record('owned_snapshot',s);return s;}
function force(){const s=snapshot();if(s.rootPresent){must(s.rootVerified,'cleanup_ownership_unknown');forced=true;const r=spawnSync('taskkill.exe',['/PID',String(root.pid),'/T','/F'],{shell:false,windowsHide:true,encoding:'utf8',timeout:5000});record('forced_cleanup',{status:r.status});}}
try{
 record('launch_plan',{id:'H1',maxHelpers:4,maxMs:60000,productImported:false});
 root=spawn(exe,[script],{cwd:out,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});must(root.pid,'spawn_failed');record('root_started',{pid:root.pid});
 root.stdout.on('data',b=>{stdoutBytes+=b.length;});root.stderr.on('data',b=>{stderrBytes+=b.length;});
 root.once('exit',(code,signal)=>{exit={code,signal:signal??null};record('root_exit',exit);});root.once('error',()=>{firstFailure='spawn_error';});
 timer=setTimeout(()=>{firstFailure??='deadline';try{force();}catch{firstFailure='deadline_cleanup_unverified';}},48000);
 const readyDeadline=performance.now()+15000;
 while(!fs.existsSync(path.join(out,'ready.json'))&&!exit&&performance.now()<readyDeadline)await sleep(50);
 must(fs.existsSync(path.join(out,'ready.json')),'ready_timeout');must(snapshot().rootVerified,'root_identity');
 write(path.join(out,'release.json'),{authorized:true});
 const end=performance.now()+10000;while(!exit&&performance.now()<end)await sleep(50);
 must(exit?.code===0,'native_helper_failed');
 const native=JSON.parse(fs.readFileSync(path.join(out,'result.json'),'utf8'));write(path.join(evidence,'native-result.json'),native);must(native.passed,'native_comparison_failed');
}catch(e){firstFailure??=e.safeCode??'unknown_error';record('first_failure',{code:firstFailure});}
finally{
 clearTimeout(timer);let remaining=null,cleanupError=null;
 try{if(root&&!exit)force();const end=performance.now()+2000;while(!exit&&performance.now()<end)await sleep(25);if(root){remaining=snapshot();must(remaining.owned.length===0&&remaining.listeners.length===0&&remaining.windowCount===0,'resources_remain');}}catch(e){cleanupError=e.safeCode??'cleanup_unknown';}
 const result={id:'H1',passed:!firstFailure&&!cleanupError&&!forced&&exit?.code===0,firstFailure,cleanupError,forced,exit,rootPid:root?.pid??null,durationMs:performance.now()-clock,registered:known,remainingOwned:remaining?.owned.length??null,remainingListeners:remaining?.listeners.length??null,remainingWindows:remaining?.windowCount??null,stdoutBytes,stderrBytes,productStarts:0,helperStarts:1};
 write(path.join(evidence,'process.json'),result);record('finished',{passed:result.passed});fs.closeSync(fd);console.log(JSON.stringify({id:'H1',passed:result.passed,firstFailure,cleanupError}));if(!result.passed)process.exitCode=1;
}
