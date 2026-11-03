import fs from 'node:fs';import path from 'node:path';import {fileURLToPath}from'node:url';
import {captured,write,sha,must}from'./r9-r2-observation.mjs';
const own=path.dirname(fileURLToPath(import.meta.url)),ev=path.join(own,'evidence/r11-r1-windows');
const script=path.join(own,'r11-r1-windows-observe-v3.ps1'),receipt=path.join(ev,'observer-v3-receipt.json');
const pwsh='C:/Users/xuhaolin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe';
must(fs.readFileSync(path.resolve(own,'../../../docs/coordination/control.md'),'utf8').includes('2026-11-03T00:05:00+08:00'),'control_changed');
must(JSON.parse(fs.readFileSync(path.join(ev,'selftest-v3.json'),'utf8')).passed,'selftest_failed');
const fd=fs.openSync(path.join(ev,'observer-v3-controller.jsonl'),'wx');const record=(event,details)=>{fs.writeSync(fd,JSON.stringify({at:new Date().toISOString(),event,details})+'\n');fs.fsyncSync(fd);};
let result=null,first=null,parsed=null;
try{
 result=await captured({exe:pwsh,args:['-NoProfile','-NonInteractive','-File',script,'-Mode','Observe','-ReceiptPath',receipt,'-ControllerPid',String(process.pid),'-LauncherPid',process.argv[2],'-LauncherExe',process.argv[3]],cwd:own,limitMs:8000,id:'OBS-R1-V3',record,rawDir:ev,
 canCancel:(child,started)=>{if(!fs.existsSync(receipt))return false;const r=JSON.parse(fs.readFileSync(receipt,'utf8'));return r.pid===child.pid&&r.parentVerified&&r.parentPid===process.pid&&path.resolve(r.executable)===path.resolve(pwsh)&&r.scriptSha256===sha(fs.readFileSync(script))&&Math.abs(Date.parse(r.created)-Date.parse(started))<2000;}});
 try{parsed=JSON.parse(result.stdout);}catch{first={stage:'result_parse',code:'missing_or_invalid_result'};}
 if(!first&&(result.status!==0||result.timedOut||result.error||!parsed?.passed))first=parsed?.firstError??{stage:'observer',code:'nonzero_or_incomplete'};
}catch(e){first??={stage:'controller',code:e.safeCode??'unknown',type:e.name};}
finally{const {stdout,...processResult}=result??{};write(path.join(ev,'observer-v3-process.json'),{passed:!first,firstError:first,process:processResult,returnedResult:parsed,productStarts:0,helperStarts:0});record('finished',{passed:!first});fs.closeSync(fd);}
console.log(JSON.stringify({passed:!first,firstError:first,status:result?.status??null,timedOut:result?.timedOut??null,durationMs:result?.durationMs??null}));process.exitCode=first?1:0;
