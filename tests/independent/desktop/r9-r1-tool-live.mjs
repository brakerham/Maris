import fs from 'node:fs';import path from 'node:path';import {fileURLToPath}from'node:url';
import {observe,write,must,sha}from'./r9-r1-observation.mjs';
const own=path.dirname(fileURLToPath(import.meta.url)),ev=path.join(own,'evidence/r9-r1/live-tool');
const ext='C:/MarisC12/C12-R9-R1-20261017-001500',output=path.join(ext,'tool-live');
const pwsh='C:/Users/xuhaolin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe';
must(fs.readFileSync(path.resolve(own,'../../../docs/coordination/control.md'),'utf8').includes('2026-10-16T18:15:00+08:00'),'control_changed');
fs.mkdirSync(ev);fs.mkdirSync(output);
const fd=fs.openSync(path.join(ev,'journal.jsonl'),'wx'),start=performance.now(),startedUtc=new Date().toISOString();
const record=(event,details)=>{fs.writeSync(fd,JSON.stringify({event,at:new Date().toISOString(),elapsedMs:performance.now()-start,details})+'\n');fs.fsyncSync(fd);};
let failure=null,known=[],observations=[];
try{
 for(const action of ['identity','resources']){
  const s=await observe({action,rootPid:process.pid,parentPid:process.ppid,startedUtc,executable:process.execPath,scriptPath:fileURLToPath(import.meta.url),known,output,evidence:ev,observerScript:path.join(own,'r9-r1-observer.ps1'),pwsh,deadline:start+20000,record,id:'LIVE-'+action});
  must(s.rootVerified&&s.commandPathMatched,'live_identity');known=s.owned;observations.push(s);
  if(action==='resources')must(s.resourceStatus==='success','live_resource_status');
 }
}catch(e){failure=e.safeCode??'unknown';record('first_failure',{code:failure});}
write(path.join(ev,'result.json'),{passed:!failure,failure,observations,controllerPid:process.pid,parentPid:process.ppid,controllerExpectedExit:failure?1:0,durationMs:performance.now()-start,products:0,helpers:0,purpose:'read-only current controller identity and resource query status only'});
record('finished',{passed:!failure});fs.closeSync(fd);process.exitCode=failure?1:0;
console.log(JSON.stringify({liveSelftestPassed:!failure,failure}));
