// One restricted path/receipt contract used by local cases, live controller and H1.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
function canonical(value){
 if(typeof value!=='string'||! /^[A-Z]:[\\/]/.test(value)||/[\x00"<>|?*]/.test(value)||value.slice(2).includes(':')||/~\d/.test(value))throw Error('path_syntax');
 return path.win32.normalize(value.replaceAll('/','\\'));
}
function within(value,boundary){const p=canonical(value),b=canonical(boundary);return p===b||p.startsWith(b.endsWith('\\')?b:b+'\\');}
function noReparse(value){
 const p=canonical(value);let cursor=p;
 for(;;){if(fs.lstatSync(cursor).isSymbolicLink())return false;const parent=path.win32.dirname(cursor);if(parent===cursor)break;cursor=parent;}
 return fs.realpathSync.native(p)===p;
}
function fileCheck(actual,expected,boundary,digest){
 const checks={absoluteSyntax:false,insideBoundary:false,exactPath:false,noReparse:false,digestEqual:false};
 try{const a=canonical(actual),e=canonical(expected);checks.absoluteSyntax=true;checks.insideBoundary=within(a,boundary)&&within(e,boundary);checks.exactPath=a===e;
  if(checks.insideBoundary&&checks.exactPath){checks.noReparse=noReparse(a);checks.digestEqual=checks.noReparse&&sha(fs.readFileSync(a))===digest;}
 }catch{}
 return {passed:Object.values(checks).every(Boolean),checks};
}
function describe({executable,script,boundary,markerFile,marker,output,callId}){
 const d={executable:canonical(executable),script:canonical(script),boundary:canonical(boundary),markerFile:canonical(markerFile),marker,output:canonical(output),callId};
 d.scriptSha256=sha(fs.readFileSync(d.script));d.executableSha256=sha(fs.readFileSync(d.executable));
 if(!fileCheck(d.script,d.script,d.boundary,d.scriptSha256).passed)throw Error('descriptor_script');
 if(fs.readFileSync(d.markerFile,'utf8')!==marker)throw Error('descriptor_marker');
 return d;
}
function argvCheck(parsed,d){
 const checks={parseSucceeded:parsed?.ok===true,argvCount:false,exeArgument:false,scriptArgument:false};
 let script=null;
 if(checks.parseSucceeded&&Array.isArray(parsed.argv)){
  checks.argvCount=parsed.argv.length===2;
  if(checks.argvCount){try{checks.exeArgument=canonical(parsed.argv[0])===d.executable;}catch{}
   script=fileCheck(parsed.argv[1],d.script,d.boundary,d.scriptSha256);checks.scriptArgument=script.passed;}
 }
 return {passed:Object.values(checks).every(Boolean),checks,scriptChecks:script?.checks??null};
}
function rootCheck(raw,d,{pid,parentPid,startedUtc}){
 const argv=argvCheck(raw?.parsed,d);
 const checks={rootPresent:raw?.present===true,pidEqual:raw?.pid===pid,parentEqual:raw?.parentPid===parentPid,
  creationWithinStart:typeof raw?.created==='string'&&Date.parse(raw.created)>=Date.parse(startedUtc)-2000,
  executableEqual:false,executableHashEqual:sha(fs.readFileSync(d.executable))===d.executableSha256,
  actualPathNoReparse:raw?.pathNoReparse===true,scriptArgv:argv.passed,markerEqual:fs.readFileSync(d.markerFile,'utf8')===d.marker};
 try{checks.executableEqual=canonical(raw.executable)===d.executable;}catch{}
 return {passed:Object.values(checks).every(Boolean),checks,argv};
}
function receiptCheck(receipt,d,{pid,receiptPath,expectedReceiptPath,startedUtc=null,parentPid=null}){
 const pathResult=fileCheck(receipt?.scriptPath,d.script,d.boundary,d.scriptSha256);
 const checks={present:!!receipt,pidEqual:receipt?.pid===pid,callIdEqual:receipt?.callId===d.callId,markerEqual:receipt?.marker===d.marker,
  scriptEqual:pathResult.passed,reportedDigestEqual:receipt?.scriptSha256===d.scriptSha256,outputEqual:false,receiptPathEqual:false,creationValid:startedUtc===null,parentEqual:parentPid===null||receipt?.parentPid===parentPid};
 try{checks.outputEqual=canonical(receipt.output)===d.output;checks.receiptPathEqual=canonical(receiptPath)===canonical(expectedReceiptPath)&&within(receiptPath,d.output);}catch{}
 if(startedUtc!==null)checks.creationValid=Date.parse(receipt?.created)>=Date.parse(startedUtc)-2000;
 return {passed:Object.values(checks).every(Boolean),checks,pathChecks:pathResult.checks};
}
module.exports={sha,canonical,within,noReparse,fileCheck,describe,argvCheck,rootCheck,receiptCheck};
