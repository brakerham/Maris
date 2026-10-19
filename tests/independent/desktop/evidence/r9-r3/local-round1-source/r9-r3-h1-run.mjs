import fs from 'node:fs';import path from 'node:path';import {spawn}from'node:child_process';
import cfg from './r9-r3-config.cjs';import storage from './r9-r3-storage.cjs';import identity from './r9-r2-identity.cjs';
import {observe,captured,write,must,sha,sleep}from'./r9-r2-observation.mjs';
must(fs.readFileSync(path.join(cfg.repo,'docs/coordination/control.md'),'utf8').includes(cfg.controlVersion),'control_changed');
must(JSON.parse(fs.readFileSync(path.join(cfg.own,'evidence/r9-r2/live/result.json'),'utf8')).passed,'live_gate');
for(const line of fs.readFileSync(path.join(cfg.evidence,'target-source.sha256'),'utf8').trimEnd().split('\n')){
 const [name,digest]=line.split('\t');must(sha(fs.readFileSync(path.join(cfg.own,name)))===digest,'source_changed');
}
const output=path.join(cfg.ext,'output/H1'),ev=path.join(cfg.evidence,'helper-H1'),script=path.join(output,'main.cjs');
fs.mkdirSync(output);fs.mkdirSync(ev);const preparation=storage.createRecorder(path.join(ev,'context-preparation.jsonl'));
try{const prepared=storage.prepareContext({source:path.join(cfg.ext,'profile-main/Local State'),helper:path.join(cfg.ext,'helper-profile-H1'),boundary:cfg.ext,rec:preparation});write(path.join(ev,'context-preparation.json'),{passed:true,...prepared});}finally{preparation.close();}
fs.copyFileSync(path.join(cfg.own,'r9-r3-h1-native.cjs'),script,fs.constants.COPYFILE_EXCL);
const descriptor=identity.describe({executable:cfg.electron,script,boundary:cfg.ext,markerFile:cfg.markerFile,marker:cfg.marker,output,callId:'H1'});
must(descriptor.executableSha256==='bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e','electron_digest');
write(path.join(output,'launch.json'),descriptor);
const original=fs.readFileSync(path.join(cfg.evidence,'original-profile.tsv'),'utf8').trimEnd().split('\n').map(l=>l.split('\t'));
const checkProfile=()=>original.every(([p,n,h])=>{const f=path.join(cfg.ext,p);return fs.statSync(f).size===Number(n)&&sha(fs.readFileSync(f))===h;});
must(checkProfile(),'profile_before');
const env={...process.env,APPDATA:path.join(cfg.ext,'os-env/appdata'),LOCALAPPDATA:path.join(cfg.ext,'os-env/localappdata'),TEMP:path.join(cfg.ext,'os-env/temp'),TMP:path.join(cfg.ext,'os-env/temp')};
for(const k of ['NODE_OPTIONS','ELECTRON_RUN_AS_NODE','MARIS_E2E','MARIS_E2E_USER_DATA','MARIS_E2E_EXIT_MS','ELECTRON_ENABLE_LOGGING','ELECTRON_LOG_FILE'])delete env[k];
const fd=fs.openSync(path.join(ev,'journal.jsonl'),'wx'),start=performance.now(),startedUtc=new Date().toISOString();
const record=(event,details)=>{fs.writeSync(fd,JSON.stringify({event,at:new Date().toISOString(),elapsedMs:performance.now()-start,details})+'\n');fs.fsyncSync(fd);};
let root,exit=null,known=[],seq=0,failure=null,cleanupError=null,forced=false,stdout=[],stderr=[],remaining=null,released=false,native=null,nativeCollected=false;
const obs=async(action,deadline)=>{
 const s=await observe({action,rootPid:root.pid,parentPid:process.pid,startedUtc,descriptor,known,output,evidence:ev,observerScript:cfg.observer,parserScript:cfg.parser,pwsh:cfg.pwsh,deadline,record,id:'H1-OBS-'+(++seq)});
 known=[...new Map([...known,...s.owned].map(v=>[v.pid+':'+v.created,v])).values()];return s;
};
try{
 record('launch_plan',{id:'H1',remainingHelperLimit:4,cumulativeBefore:2,totalMs:60000,cleanupReserveMs:10000,scriptDigest:descriptor.scriptSha256});
 root=spawn(descriptor.executable,[descriptor.script],{cwd:output,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});
 must(root.pid,'helper_spawn');record('helper_spawn',{pid:root.pid,parentPid:process.pid,helperStarts:1,cumulativeHelpers:3});
 root.stdout.on('data',b=>stdout.push(b));root.stderr.on('data',b=>stderr.push(b));
 root.once('exit',(code,signal)=>{exit={code,signal:signal??null};record('helper_exit',exit);});
 root.once('error',e=>{failure??='spawn_error';record('helper_error',{type:e.name,code:['EACCES','ENOENT','EPERM'].includes(e.code)?e.code:null});});
 const readyPath=path.join(output,'ready.json');
 while(!fs.existsSync(readyPath)&&!exit&&performance.now()<start+15000)await sleep(25);
 must(fs.existsSync(readyPath),'ready_missing');
 const s=await obs('identity',start+50000);must(s.rootVerified,'root_identity');
 const ready=JSON.parse(fs.readFileSync(readyPath,'utf8'));
 const checked=identity.receiptCheck(ready,descriptor,{pid:root.pid,receiptPath:readyPath,expectedReceiptPath:readyPath});
 record('ready_comparisons',{id:'H1-READY',expected:true,checks:checked.checks,pathChecks:checked.pathChecks});must(checked.passed,'ready_identity');must(ready.context?.userDataEqual&&ready.context?.sessionDataEqual&&ready.context?.sameEncryptedFields,'ready_context');record('ready_context',{id:'H1-READY-CONTEXT',expected:true,actual:ready.context});
 must(performance.now()<start+50000,'native_budget');write(path.join(output,'release.json'),{authorized:true,callId:'H1',pid:root.pid});released=true;record('release',{id:'H1-RELEASE',pid:root.pid});
 while(!exit&&performance.now()<start+50000)await sleep(25);
 must(exit!==null,'helper_deadline');
 native=storage.collectNative(output,ev,exit.code);nativeCollected=true;write(path.join(ev,'native-collection.json'),native);record('native_collection',native);
 must(exit.code===0,'native_helper_nonzero');must(native.resultPresent&&native.nativePassed&&native.collectionErrors.length===0&&native.uniqueIds,'native_comparison');
}catch(e){failure??=e.safeCode??'unknown';record('first_failure',{code:failure});}
finally{
 try{
  if(root&&!exit){
   const current=await obs('identity',start+55000);must(current.rootVerified,'cleanup_identity');forced=true;
   const kill=await captured({exe:path.join(process.env.SystemRoot,'System32/taskkill.exe'),args:['/PID',String(root.pid),'/T','/F'],cwd:output,limitMs:Math.min(3000,Math.floor(start+57000-performance.now())),id:'H1-STOP',record,rawDir:output,canCancel:()=>false});
   must(kill.status===0,'cleanup_command');
  }
  while(root&&!exit&&performance.now()<start+57000)await sleep(25);
  if(root){remaining=await obs('resources',start+60000);must(remaining.owned.length===0&&remaining.listeners.length===0&&remaining.windowCount===0,'remaining_resources');}
 }catch(e){cleanupError=e.safeCode??'cleanup_unknown';record('cleanup_failure',{code:cleanupError});}
 let unchanged=null;try{unchanged=checkProfile();}catch{failure??='profile_read_unknown';}
 record('profile_readonly_comparison',{id:'H1-PROFILE-UNCHANGED',expected:true,actual:unchanged});
 if(!unchanged)failure??='profile_changed';
 // Collect stages and native first error independently of a nonzero exit or absent result.
 if(!nativeCollected){native=storage.collectNative(output,ev,exit?.code??null);nativeCollected=true;write(path.join(ev,'native-collection.json'),native);record('native_collection',native);}
 const result={id:'H1',passed:!failure&&!cleanupError&&!forced&&exit?.code===0&&unchanged,failure,cleanupError,forced,exit,rootPid:root?.pid??null,durationMs:performance.now()-start,released,nativeFirstError:native?.firstNativeError??null,nativeResultPresent:native?.resultPresent??false,profileUnchanged:unchanged,known,remainingOwned:remaining?.owned.length??null,remainingListeners:remaining?.listeners.length??null,remainingWindows:remaining?.windowCount??null,stdoutBytes:Buffer.concat(stdout).length,stdoutSha256:sha(Buffer.concat(stdout)),stderrBytes:Buffer.concat(stderr).length,stderrSha256:sha(Buffer.concat(stderr)),productStarts:0,helperStarts:root?.pid?1:0};
 write(path.join(ev,'process.json'),result);record('finished',{passed:result.passed});fs.closeSync(fd);process.exitCode=result.passed?0:1;console.log(JSON.stringify({H1Passed:result.passed,failure,cleanupError}));
}
