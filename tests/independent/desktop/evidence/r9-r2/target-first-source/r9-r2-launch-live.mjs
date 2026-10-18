import fs from'node:fs';import path from'node:path';import{spawn}from'node:child_process';
import cfg from'./r9-r2-config.cjs';import identity from'./r9-r2-identity.cjs';import{must,write,sha}from'./r9-r2-observation.mjs';
must(fs.readFileSync(path.join(cfg.repo,'docs/coordination/control.md'),'utf8').includes(cfg.controlVersion),'control_changed');
for(const line of fs.readFileSync(path.join(cfg.evidence,'target-source.sha256'),'utf8').trimEnd().split('\n')){const [f,h]=line.split('\t');must(sha(fs.readFileSync(path.join(cfg.own,f)))===h,'frozen_source');}
const descriptor=identity.describe({executable:cfg.node,script:path.join(cfg.own,'r9-r2-live.mjs'),boundary:cfg.own,markerFile:cfg.markerFile,marker:cfg.marker,output:path.join(cfg.ext,'tool-live'),callId:'LIVE'});
write(path.join(cfg.ext,'live-launch.json'),descriptor);
const env={...process.env};delete env.NODE_OPTIONS;delete env.ELECTRON_RUN_AS_NODE;
const startedUtc=new Date().toISOString(),start=performance.now();let status=null,signal=null,error=null,forced=false,output=[],err=[];
const child=spawn(descriptor.executable,[descriptor.script],{shell:false,windowsHide:true,cwd:cfg.ext,env,stdio:['ignore','pipe','pipe']});
child.stdout.on('data',b=>output.push(b));child.stderr.on('data',b=>err.push(b));child.once('error',e=>{error=['EACCES','ENOENT','EPERM'].includes(e.code)?e.code:'spawn_error';});
const timer=setTimeout(()=>{
 const receiptPath=path.join(descriptor.output,'controller-ready.json');
 try{const r=JSON.parse(fs.readFileSync(receiptPath,'utf8'));const v=identity.receiptCheck(r,descriptor,{pid:child.pid,parentPid:process.pid,receiptPath,expectedReceiptPath:receiptPath,startedUtc});if(v.passed){forced=true;child.kill();}else{error='launcher_cleanup_identity_unknown';}}catch{error='launcher_cleanup_identity_unknown';}
},22000);
await new Promise(resolve=>{child.once('exit',(c,s)=>{status=c;signal=s??null;});child.once('close',resolve);});clearTimeout(timer);
const result={id:'LIVE-controller',pid:child.pid,parentPid:process.pid,status,signal,error,forced,durationMs:performance.now()-start,stdoutBytes:Buffer.concat(output).length,stdoutSha256:sha(Buffer.concat(output)),stderrBytes:Buffer.concat(err).length,stderrSha256:sha(Buffer.concat(err)),productStarts:0,helperStarts:0};
write(path.join(cfg.evidence,'live-controller.json'),result);console.log(JSON.stringify(result));process.exitCode=status===0&&!forced&&!error?0:1;
