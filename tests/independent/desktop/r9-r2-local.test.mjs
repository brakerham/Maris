import fs from 'node:fs';import path from 'node:path';
import cfg from './r9-r2-config.cjs';import identity from './r9-r2-identity.cjs';
import {captured,write,must}from'./r9-r2-observation.mjs';
const round=Number(process.argv[2]);must([1,2,3].includes(round),'round_number');
const e=path.join(cfg.evidence,'local-round'+round),f=path.join(e,'fixtures');fs.mkdirSync(f,{recursive:true});
const a=path.join(f,'中文 空格'),other=path.join(f,'other');fs.mkdirSync(a);fs.mkdirSync(other);
const script=path.join(a,'entry.cjs'),duplicate=path.join(other,'entry.cjs'),long=script+'.more.cjs';
for(const p of [script,duplicate,long])fs.writeFileSync(p,'// inert virtual path fixture\n',{flag:'wx'});
const markerFile=path.join(f,'marker.txt');fs.writeFileSync(markerFile,'virtual marker');
const d=identity.describe({executable:cfg.node,script,boundary:f,markerFile,marker:'virtual marker',output:f,callId:'VIRTUAL'});
const q=v=>'"'+v+'"';const line=(s,extra='')=>q(d.executable)+' '+q(s)+extra;
const inputs=[
 ['PATH-01-backslash',line(d.script),true],['PATH-02-forwardslash',line(d.script.replaceAll('\\','/')),true],
 ['PATH-03-spaces-chinese-quotes',line(d.script),true],['PATH-04-different-cwd',line(d.script),true],
 ['PATH-05-wrong-script',line(duplicate),false],['PATH-06-same-name-other-dir',line(duplicate),false],
 ['PATH-07-only-other-argument',line(duplicate,' '+q(d.script)),false],['PATH-08-longer-substring',line(long),false],
 ['PATH-09-extra-arg',line(d.script,' --extra'),false],['PATH-10-missing-script',q(d.executable),false],
 ['PATH-11-empty','',false],['PATH-12-unparseable','\0',false],['PATH-13-relative',line('entry.cjs'),false],
 ['PATH-14-drive-relative',line('D:entry.cjs'),false],['PATH-15-root-relative',line('\\entry.cjs'),false],
 ['PATH-16-UNC',line('\\\\server\\share\\entry.cjs'),false],['PATH-17-device',line('\\\\?\\'+d.script),false],
 ['PATH-18-case-alias',line(d.script.replace('entry.cjs','ENTRY.cjs')),false],['PATH-19-short-alias',line(path.join(f,'SHORT~1','entry.cjs')),false]
];
const input=path.join(e,'parser-input.json'),output=path.join(e,'parser-output.json');write(input,inputs.map(([id,command])=>({id,command})));
const fd=fs.openSync(path.join(e,'journal.jsonl'),'wx');const record=(event,details)=>{fs.writeSync(fd,JSON.stringify({event,at:new Date().toISOString(),details})+'\n');fs.fsyncSync(fd);};
let checks=[],failure=null;
function check(id,expected,actual){must(!checks.some(x=>x.id===id),'duplicate_id');const value={id,expected,actual,passed:expected===actual};checks.push(value);record('comparison',value);if(!value.passed)throw Object.assign(Error('local_comparison'),{safeCode:'local_comparison',id});}
try{
 const result=await captured({exe:cfg.pwsh,args:['-NoProfile','-NonInteractive','-File',path.join(cfg.own,'r9-r2-parse-batch.ps1'),'-InputPath',input,'-OutputPath',output],cwd:other,limitMs:8000,id:'LOCAL-PARSER-'+round,record,rawDir:e,canCancel:()=>false});
 check('PARSER-EXIT',0,result.status);const parsed=JSON.parse(fs.readFileSync(output,'utf8'));
 for(const [id,,expected]of inputs){const row=parsed.find(p=>p.id===id);check(id,expected,identity.argvCheck(row.parsed,d).passed);}
 const parsedGood=parsed[0].parsed;
 check('PATH-20-digest-drift',false,identity.argvCheck(parsedGood,{...d,scriptSha256:'0'.repeat(64)}).passed);
 check('PATH-21-boundary-drift',false,identity.argvCheck(parsedGood,{...d,boundary:other}).passed);
 const receiptPath=path.join(f,'ready.json'),base={pid:123,scriptPath:d.script,scriptSha256:d.scriptSha256,marker:d.marker,output:d.output,callId:d.callId,created:new Date().toISOString()};
 const args={pid:123,receiptPath,expectedReceiptPath:receiptPath};
 for(const [id,receipt,expected]of [
  ['READY-01-valid',base,true],['READY-02-wrong-pid',{...base,pid:456},false],
  ['READY-03-old-output',{...base,output:other},false],['READY-04-old-marker',{...base,marker:'old'},false],
  ['READY-05-wrong-path',{...base,scriptPath:duplicate},false],['READY-06-wrong-hash',{...base,scriptSha256:'0'.repeat(64)},false],
  ['READY-07-missing',null,false],['READY-08-call-id',{...base,callId:'old'},false],['READY-09-forward-path',{...base,scriptPath:d.script.replaceAll('\\','/')},true]
 ])check(id,expected,identity.receiptCheck(receipt,d,args).passed);
 check('READY-10-old-receipt-path',false,identity.receiptCheck(base,d,{...args,receiptPath:path.join(other,'ready.json')}).passed);
 check('CANCEL-01-stale-created',false,identity.receiptCheck({...base,created:'2020-01-01T00:00:00Z'},d,{...args,startedUtc:new Date().toISOString()}).passed);
 check('CANCEL-02-parent-match',true,identity.receiptCheck({...base,parentPid:456},d,{...args,parentPid:456,startedUtc:new Date().toISOString()}).passed);
 check('CANCEL-03-parent-mismatch',false,identity.receiptCheck({...base,parentPid:789},d,{...args,parentPid:456,startedUtc:new Date().toISOString()}).passed);
 const now=new Date().toISOString(),raw={present:true,pid:123,parentPid:456,created:now,executable:d.executable,parsed:parsedGood,pathNoReparse:true};
 check('ROOT-01-valid',true,identity.rootCheck(raw,d,{pid:123,parentPid:456,startedUtc:now}).passed);
 check('ROOT-02-parent',false,identity.rootCheck({...raw,parentPid:999},d,{pid:123,parentPid:456,startedUtc:now}).passed);
 check('ROOT-03-reparse',false,identity.rootCheck({...raw,pathNoReparse:false},d,{pid:123,parentPid:456,startedUtc:now}).passed);
}catch(e){failure={code:e.safeCode??'unknown',id:e.id??null};record('failure',failure);}
write(path.join(e,'result.json'),{round,passed:!failure,failure,checks,productImported:false,productStarts:0,helperStarts:0});fs.closeSync(fd);process.exitCode=failure?1:0;console.log(JSON.stringify({round,passed:!failure,checks:checks.length,failure}));
