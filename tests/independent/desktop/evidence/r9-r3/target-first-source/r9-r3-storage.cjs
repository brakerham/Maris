'use strict';
// Restricted tester helpers. No Electron or product imports; identical functions run in H1.
const fs=require('node:fs'),path=require('node:path');
const identity=require('./r9-r2-identity.cjs');
const {sha}=identity;
const known=new Set(['context_missing_key','context_mismatch','path_binding_mismatch','context_boundary','helper_not_fresh','comparison_failed','duplicate_id','receipt_missing']);
function fail(code){throw Object.assign(new Error(code),{safeCode:code});}
function classify(error,operation){
 const name=['Error','TypeError','SyntaxError','RangeError','AggregateError'].includes(error?.name)?error.name:'unknown';
 let code='unknown';
 if(['ENOENT','EACCES','EPERM','EIO','EEXIST','ENOTDIR','EBUSY'].includes(error?.code))code=error.code;
 else if(known.has(error?.safeCode))code=error.safeCode;
 else if(operation==='parse'&&error instanceof SyntaxError)code='json_parse_failed';
 // Exact fixed Electron 44.4.5 synchronous-library literals; never emit message/stack.
 else if(operation==='decrypt'&&error?.message==='Error while decrypting the ciphertext provided to safeStorage.decryptString.')code='native_decrypt_failed';
 else if(operation==='decrypt'&&error?.message==='Error while decrypting the ciphertext provided to safeStorage.decryptString. Decryption is not available.')code='native_decrypt_unavailable';
 else if(operation==='decrypt'&&error?.message==='Error while decrypting the ciphertext provided to safeStorage.decryptString. Ciphertext does not appear to be encrypted.')code='native_ciphertext_format';
 return {name,code};
}
function createRecorder(file,io=fs){
 const fd=io.openSync(file,'wx'),ids=new Set(),checks=[];let firstError=null;
 const emit=v=>{io.writeSync(fd,JSON.stringify(v)+'\n');io.fsyncSync(fd);};
 function run(id,role,operation,fn,summarize=()=>({})){ 
  if(ids.has(id))fail('duplicate_id');ids.add(id);
  const begin=performance.now();emit({id,event:'enter',role,operation,at:new Date().toISOString()});
  try {const v=fn();emit({id,event:'terminal',role,operation,at:new Date().toISOString(),durationMs:performance.now()-begin,category:'success',...summarize(v)});return v;}
  catch(error){const c=checks.find(v=>v.id===id);const terminal={id,event:'terminal',role,operation,at:new Date().toISOString(),durationMs:performance.now()-begin,category:'error',error:classify(error,operation),...(c?{expected:c.expected,actual:c.actual,passed:c.passed}:{})};firstError??=terminal;emit(terminal);throw error;}
 }
 function check(id,expected,actual){return run(id,'business_comparison','compare',()=>{
  const c={id,operator:'eq',expected,actual,passed:expected===actual};checks.push(c);
  if(!c.passed)fail('comparison_failed');return c;
 },c=>({expected:c.expected,actual:c.actual,passed:c.passed}));}
 return {run,check,checks,get firstError(){return firstError;},close:()=>io.closeSync(fd)};
}
function encryptedFields(state){
 if(!state||typeof state.os_crypt?.encrypted_key!=='string'||!state.os_crypt.encrypted_key.length)fail('context_missing_key');
 return Object.fromEntries(Object.entries(state.os_crypt).filter(([k])=>k==='encrypted_key'||k.endsWith('_encrypted_key')).sort(([a],[b])=>a.localeCompare(b)));
}
function readContext(file,rec,prefix,io=fs){
 const blob=rec.run(prefix+'-READ','local_state','read',()=>io.readFileSync(file),v=>({bytes:v.length,fileSha256:sha(v)}));
 const obj=rec.run(prefix+'-PARSE','local_state','parse',()=>JSON.parse(blob.toString('utf8')));
 const fields=rec.run(prefix+'-FIELDS','local_state','validate',()=>encryptedFields(obj),v=>({requiredFieldPresent:true,fieldCount:Object.keys(v).length}));
 return {blob,fields};
}
function prepareContext({source,helper,boundary,rec,io=fs}){
 rec.run('CTX-PREP-BOUNDARY','helper_context','validate',()=>{
  if(!identity.within(source,boundary)||!identity.within(helper,boundary)||!identity.noReparse(source)||!identity.noReparse(path.dirname(helper)))fail('context_boundary');
  if(io.existsSync(helper))fail('helper_not_fresh');
 });
 const before=readContext(source,rec,'CTX-SOURCE',io);
 rec.run('CTX-COPY','helper_local_state','copy',()=>{io.mkdirSync(helper);io.writeFileSync(path.join(helper,'Local State'),before.blob,{flag:'wx'});});
 const copied=readContext(path.join(helper,'Local State'),rec,'CTX-COPIED',io);
 return rec.run('CTX-PREP-COMPARE','helper_context','compare',()=>{
  const result={sameBytes:before.blob.length===copied.blob.length&&sha(before.blob)===sha(copied.blob),sameEncryptedFields:JSON.stringify(before.fields)===JSON.stringify(copied.fields),sourceUnchanged:sha(io.readFileSync(source))===sha(before.blob),bytes:before.blob.length,fileSha256:sha(before.blob)};
  if(!result.sameBytes||!result.sameEncryptedFields||!result.sourceUnchanged)fail('context_mismatch');return result;
 },v=>v);
}
function verifyContext({source,helper,userData,sessionData,boundary,rec,prefix,io=fs}){
 const paths=rec.run(prefix+'-PATHS','helper_context','validate',()=>{
  const v={userDataEqual:identity.canonical(userData)===identity.canonical(helper),sessionDataEqual:identity.canonical(sessionData)===identity.canonical(helper),insideBoundary:identity.within(helper,boundary),noReparse:identity.noReparse(helper)};
  if(!Object.values(v).every(Boolean))fail('path_binding_mismatch');return v;
 },v=>v);
 const a=readContext(source,rec,prefix+'-SOURCE',io),b=readContext(path.join(helper,'Local State'),rec,prefix+'-HELPER',io);
 return rec.run(prefix+'-EQUAL','helper_context','compare',()=>{
  const sameEncryptedFields=JSON.stringify(a.fields)===JSON.stringify(b.fields);if(!sameEncryptedFields)fail('context_mismatch');
  return {...paths,requiredFieldsPresent:true,sameEncryptedFields,fieldCount:Object.keys(a.fields).length};
 },v=>v);
}
const business=[['H1-NATIVE-AVAILABLE',true],['H1-OWNER-SCHEMA',true],['H1-OWNER-READY',true],['H1-OWNER-NO-PLAIN',true],['H1-OUTBOX-COUNT',1],['H1-OUTBOX-CONTINUITY',true],['H1-OUTBOX-NO-PLAIN',true]];
function runH1({rec,profile,continuityFile,safeStorage,io=fs}){
 const available=rec.run('H1-OP-AVAILABILITY','native_storage','availability',()=>safeStorage.isEncryptionAvailable(),v=>({available:v}));
 rec.check('H1-NATIVE-AVAILABLE',true,available);
 const ownerBlob=rec.run('H1-OP-OWNER-READ','owner_ciphertext','read',()=>io.readFileSync(path.join(profile,'owner-session.bin')),v=>({bytes:v.length}));
 const ownerText=rec.run('H1-OP-OWNER-DECRYPT','owner_ciphertext','decrypt',()=>safeStorage.decryptString(ownerBlob));
 const owner=rec.run('H1-OP-OWNER-PARSE','owner_plaintext','parse',()=>JSON.parse(ownerText));
 rec.check('H1-OWNER-SCHEMA',true,owner.schemaVersion===1&&typeof owner.handle==='string'&&typeof owner.password==='string');
 rec.check('H1-OWNER-READY',true,owner.password.length>0&&typeof owner.refreshToken==='string'&&owner.refreshToken.length>0&&!owner.repairRequired);
 rec.check('H1-OWNER-NO-PLAIN',true,!ownerBlob.includes(Buffer.from(owner.password))&&!ownerBlob.includes(Buffer.from(owner.refreshToken)));
 const continuityText=rec.run('H1-OP-CONTINUITY-READ','continuity_fixture','read',()=>io.readFileSync(continuityFile,'utf8'));
 const continuity=rec.run('H1-OP-CONTINUITY-PARSE','continuity_fixture','parse',()=>JSON.parse(continuityText));
 const boxBlob=rec.run('H1-OP-OUTBOX-READ','outbox_ciphertext','read',()=>io.readFileSync(path.join(profile,'outbox.bin')),v=>({bytes:v.length}));
 const boxText=rec.run('H1-OP-OUTBOX-DECRYPT','outbox_ciphertext','decrypt',()=>safeStorage.decryptString(boxBlob));
 const entries=rec.run('H1-OP-OUTBOX-PARSE','outbox_plaintext','parse',()=>JSON.parse(boxText));
 rec.check('H1-OUTBOX-COUNT',1,entries.length);const item=entries[0];
 rec.check('H1-OUTBOX-CONTINUITY',true,item.draftId===continuity.draftId&&item.clientEventId===continuity.eventId&&item.body===continuity.body&&item.digest===sha(continuity.body));
 rec.check('H1-OUTBOX-NO-PLAIN',true,!boxBlob.includes(Buffer.from(continuity.body)));
 return {ownerIdentityDigest:sha(JSON.stringify([owner.handle,owner.password])),refreshPresent:true,draftDigest:sha(item.draftId),eventDigest:sha(item.clientEventId),payloadDigest:item.digest,entries:entries.length};
}
function finish({rec,output,baseline=null,error=null,io=fs}){
 let finishError=null;
 if(baseline&&!error){try{rec.run('H1-OP-BASELINE-WRITE','safe_baseline','write',()=>io.writeFileSync(path.join(output,'baseline.json'),JSON.stringify(baseline)+'\n',{flag:'wx'}));}catch(e){error=e;}}
 const result={passed:!error,checks:rec.checks,notRun:business.filter(([id])=>!rec.checks.some(c=>c.id===id)).map(([id,expected])=>({id,expected,actual:null,status:'not_run'})),firstError:rec.firstError,baseline:!error?baseline:null,productImported:false,fixtureWritten:false};
 try{rec.run('H1-OP-RESULT-WRITE','native_result','write',()=>io.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'}));}
 catch(e){finishError=classify(e,'write');result.passed=false;}
 return {passed:result.passed,firstError:rec.firstError,finishError,resultWritten:!finishError};
}
function collectNative(output,evidence,exitCode){
 const receipt={exitCode,firstNativeError:null,resultPresent:false,baselinePresent:false,stagesPresent:false,collectionErrors:[]};let rows=[];
 for(const name of ['stages.jsonl','result.json','baseline.json','native-terminal.json']){
  const source=path.join(output,name);
  if(!fs.existsSync(source)){if(name==='result.json')receipt.collectionErrors.push({role:'native_result',code:'receipt_missing'});continue;}
  try{
   const b=fs.readFileSync(source);fs.copyFileSync(source,path.join(evidence,'native-'+name),fs.constants.COPYFILE_EXCL);
   if(name==='stages.jsonl'){rows=b.toString('utf8').trim().split('\n').filter(Boolean).map(l=>JSON.parse(l));receipt.stagesPresent=true;receipt.firstNativeError=rows.find(v=>v.event==='terminal'&&v.category==='error')??null;}
   if(name==='result.json'){receipt.resultPresent=true;const v=JSON.parse(b);receipt.nativePassed=v.passed;receipt.firstNativeError??=v.firstError;}
   if(name==='baseline.json')receipt.baselinePresent=true;
  }catch(error){receipt.collectionErrors.push({role:name==='stages.jsonl'?'native_stages':'native_result',...classify(error,'parse')});}
 }
 receipt.stageEnters=rows.filter(v=>v.event==='enter').length;receipt.stageTerminals=rows.filter(v=>v.event==='terminal').length;
 receipt.uniqueIds=new Set(rows.filter(v=>v.event==='enter').map(v=>v.id)).size===receipt.stageEnters;
 return receipt;
}
module.exports={classify,createRecorder,prepareContext,verifyContext,encryptedFields,runH1,finish,collectNative,fail,business};
