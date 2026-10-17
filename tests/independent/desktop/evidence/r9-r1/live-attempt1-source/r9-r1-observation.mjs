import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
export const sha=v=>createHash('sha256').update(v).digest('hex');
export const write=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
export const must=(ok,code)=>{if(!ok)throw Object.assign(new Error(code),{safeCode:code});};
export const sleep=ms=>new Promise(r=>setTimeout(r,ms));
export const safeError=e=>({type:['Error','TypeError','SyntaxError','AbortError'].includes(e?.name)?e.name:'other',code:['EACCES','EPERM','ENOENT','ETIMEDOUT','ABORT_ERR','ESRCH'].includes(e?.code)?e.code:null});
export function classify(r){
  if(r.timedOut)return {kind:'timeout',value:null};
  if(r.error?.code==='EACCES'||r.error?.code==='EPERM')return {kind:'access_denied',value:null};
  if(r.status!==0){let value=null;try{value=JSON.parse(r.stdout);}catch{}return {kind:value?.error?.category==='access_denied'?'access_denied':'nonzero',value};}
  let value;try{value=JSON.parse(r.stdout);}catch{return {kind:'parse_failure',value:null};}
  if(value?.ok!==true||typeof value.rootVerified!=='boolean'||!Array.isArray(value.owned))return {kind:'schema_failure',value:null};
  if(value.resourceStatus==='success'&&(!Array.isArray(value.listeners)||!Number.isInteger(value.windowCount)))return {kind:'schema_failure',value:null};
  return {kind:'success',value};
}
// Every call owns a direct child and preserves real exit/stream state. No synchronous OS query.
export async function captured({exe,args,cwd,env,limitMs,id,record,rawDir,canCancel}){
  must(limitMs>0&&limitMs<=8000,'observer_budget');const start=performance.now(),startedUtc=new Date().toISOString();
  record('observer_enter',{id,startedUtc,limitMs});
  let child,status=null,signal=null,error=null,timedOut=false,cancelVerified=false,stdout=[],stderr=[];
  await new Promise(resolve=>{
    let done=false,timer;
    const finish=()=>{if(done)return;done=true;clearTimeout(timer);resolve();};
    try{child=spawn(exe,args,{cwd,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});}
    catch(e){error=safeError(e);finish();return;}
    record('observer_spawn',{id,pid:child.pid??null,parentPid:process.pid});
    child.stdout.on('data',b=>stdout.push(b));child.stderr.on('data',b=>stderr.push(b));
    child.once('error',e=>{error=safeError(e);if(!child.pid)finish();});
    child.once('exit',(code,sig)=>{status=code;signal=sig??null;record('observer_exit',{id,status,signal});});
    child.once('close',finish);
    timer=setTimeout(()=>{
      timedOut=true;
      try{cancelVerified=canCancel(child,startedUtc);if(cancelVerified)child.kill();}
      catch(e){error=safeError(e);}
      record('observer_deadline',{id,cancelVerified});
      // No second unbounded wait. If cancellation cannot be verified, keep status unknown.
      setTimeout(()=>{child.stdout.destroy();child.stderr.destroy();child.unref();finish();},200).unref();
    },Math.max(1,limitMs-250));
  });
  const out=Buffer.concat(stdout),err=Buffer.concat(stderr);
  if(rawDir){fs.writeFileSync(path.join(rawDir,id+'.stdout'),out,{flag:'wx'});fs.writeFileSync(path.join(rawDir,id+'.stderr'),err,{flag:'wx'});}
  const terminal={id,startedUtc,endedUtc:new Date().toISOString(),durationMs:performance.now()-start,status,signal,error,timedOut,cancelVerified,pid:child?.pid??null,stdoutBytes:out.length,stdoutSha256:sha(out),stderrBytes:err.length,stderrSha256:sha(err)};
  record('observer_terminal',terminal);
  return {...terminal,stdout:out.toString('utf8')};
}
export async function observe({action,rootPid,parentPid,startedUtc,executable,scriptPath,known,output,evidence,observerScript,pwsh,deadline,record,id}){
  const limitMs=Math.min(8000,Math.floor(deadline-performance.now()));must(limitMs>=500,'remaining_observation_budget');
  const receipt=path.join(output,id+'.receipt.json');
  const request={callId:id,action,rootPid,parentPid,startedUtc,executable:path.resolve(executable),scriptPath:path.resolve(scriptPath),known,receipt,stageLog:path.join(evidence,id+'.stages.jsonl')};
  const requestPath=path.join(output,id+'.request.json');write(requestPath,request);
  const digest=sha(fs.readFileSync(observerScript));
  const result=await captured({exe:pwsh,args:['-NoProfile','-NonInteractive','-File',observerScript,'-RequestPath',requestPath],cwd:output,limitMs,id,record,rawDir:output,
    canCancel:(child,start)=>{
      if(!fs.existsSync(receipt))return false;
      const r=JSON.parse(fs.readFileSync(receipt,'utf8'));
      return r.pid===child.pid&&r.callId===id&&path.resolve(r.executable).toLowerCase()===path.resolve(pwsh).toLowerCase()&&r.scriptSha256===digest&&path.resolve(r.scriptPath)===path.resolve(observerScript)&&Date.parse(r.created)>=Date.parse(start)-2000;
    }});
  const c=classify(result);record('observer_classification',{id,kind:c.kind});
  if(c.kind!=='success')throw Object.assign(new Error('observer_'+c.kind),{safeCode:'observer_'+c.kind,observer:result.id});
  must(c.value.callId===id&&c.value.action===action,'observer_receipt_binding');
  record('owned_observation',{id,...c.value});return c.value;
}
