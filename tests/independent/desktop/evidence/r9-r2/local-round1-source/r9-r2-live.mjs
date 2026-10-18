import fs from 'node:fs';import path from 'node:path';import {fileURLToPath}from'node:url';
import cfg from './r9-r2-config.cjs';import identity from './r9-r2-identity.cjs';
import {observe,write,must}from'./r9-r2-observation.mjs';
const ev=path.join(cfg.evidence,'live'),output=path.join(cfg.ext,'tool-live');
must(fs.readFileSync(path.join(cfg.repo,'docs/coordination/control.md'),'utf8').includes(cfg.controlVersion),'control_changed');
fs.mkdirSync(ev);fs.mkdirSync(output);
const fd=fs.openSync(path.join(ev,'journal.jsonl'),'wx'),start=performance.now(),startedUtc=new Date().toISOString();
const record=(event,details)=>{fs.writeSync(fd,JSON.stringify({event,at:new Date().toISOString(),elapsedMs:performance.now()-start,details})+'\n');fs.fsyncSync(fd);};
const descriptor=identity.describe({executable:cfg.node,script:fileURLToPath(import.meta.url),boundary:cfg.own,markerFile:cfg.markerFile,marker:cfg.marker,output,callId:'LIVE'});
let failure=null,known=[];
try{
 for(const action of ['identity','resources']){
  const s=await observe({action,rootPid:process.pid,parentPid:process.ppid,startedUtc,descriptor,known,output,evidence:ev,observerScript:cfg.observer,parserScript:cfg.parser,pwsh:cfg.pwsh,deadline:start+20000,record,id:'LIVE-'+action});
  must(s.rootVerified,'live_identity');known=s.owned;
  if(action==='resources')must(s.resourceStatus==='success','live_resource_status');
 }
}catch(e){failure=e.safeCode??'unknown';record('first_failure',{code:failure});}
write(path.join(ev,'result.json'),{passed:!failure,failure,controllerPid:process.pid,parentPid:process.ppid,durationMs:performance.now()-start,products:0,helpers:0,known});
record('finished',{passed:!failure});fs.closeSync(fd);process.exitCode=failure?1:0;
console.log(JSON.stringify({livePassed:!failure,failure}));
