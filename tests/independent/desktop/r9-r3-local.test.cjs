const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const cfg=require('./r9-r3-config.cjs'),s=require('./r9-r3-storage.cjs'),{sha}=require('./r9-r2-identity.cjs');
const round=Number(process.argv[2]);assert([1,2,3].includes(round));
const root=path.join(cfg.evidence,'local-round'+round);fs.mkdirSync(root);const results=[];
const log=fs.openSync(path.join(root,'cases.jsonl'),'wx');
function test(id,fn){const start=performance.now();fs.writeSync(log,JSON.stringify({id,event:'enter',at:new Date().toISOString()})+'\n');fs.fsyncSync(log);
 try{fn();results.push({id,passed:true,durationMs:performance.now()-start});}
 catch(e){results.push({id,passed:false,error:s.classify(e,'test'),durationMs:performance.now()-start});throw e;}
 finally{fs.writeSync(log,JSON.stringify({event:'terminal',...results.at(-1)})+'\n');fs.fsyncSync(log);}}
const state={os_crypt:{encrypted_key:'VIRTUAL_KEY_ONLY'},unrelated:1};
function setup(id){const dir=path.join(root,id);fs.mkdirSync(dir);const source=path.join(dir,'source.json');fs.writeFileSync(source,JSON.stringify(state));const helper=path.join(dir,'helper');const rec=s.createRecorder(path.join(dir,'stages.jsonl'));return {dir,source,helper,boundary:root,rec};}
function contextCase(id,mutate,expected){test(id,()=>{const c=setup(id);try{mutate(c);if(expected){assert.throws(()=>s.prepareContext(c));assert.equal(c.rec.firstError.error.code,expected);}else{const p=s.prepareContext(c);assert.equal(p.sameBytes,true);assert.equal(p.sameEncryptedFields,true);}}finally{c.rec.close();}});}
function verifyCase(id,mutate,expected){test(id,()=>{const c=setup(id);try{s.prepareContext(c);const args={...c,userData:c.helper,sessionData:c.helper,prefix:'READY'};mutate(c,args);if(expected){assert.throws(()=>s.verifyContext(args));assert.equal(c.rec.firstError.error.code,expected);}else assert.equal(s.verifyContext(args).sameEncryptedFields,true);}finally{c.rec.close();}});}
const text='VIRTUAL_BODY_NOT_A_REAL_MESSAGE',password='VIRTUAL_PASSWORD_ONLY',token='VIRTUAL_REFRESH_ONLY';
const owner={schemaVersion:1,handle:'virtual_owner',password,refreshToken:token,repairRequired:false};
const continuity={draftId:'virtual_draft',eventId:'virtual_event',body:text};
const entry={...continuity,clientEventId:continuity.eventId,digest:sha(text)};
function runFixture(id,{readFailure=null,decryptFailure=null,invalidJson=null,unknownDecrypt=false,writeFailure=false,badOwner=false,badContinuity=false}={}){
 const c=setup(id);const output=c.dir,events=path.join(output,'stages.jsonl');
 const io={...fs,readFileSync(file,encoding){const name=path.basename(file);
  if(name===readFailure)throw Object.assign(new Error('DO_NOT_LOG raw file private message'),{code:'EACCES'});
  if(name==='owner-session.bin')return Buffer.from('cipher-owner');if(name==='outbox.bin')return Buffer.from('cipher-outbox');
  if(name==='continuity.json')return invalidJson==='continuity'?'invalid':JSON.stringify(continuity);return fs.readFileSync(file,encoding);
 },writeFileSync(file,v,options){if(writeFailure&&path.basename(file)==='result.json')throw Object.assign(new Error('DO_NOT_LOG result path'),{code:'EIO'});return fs.writeFileSync(file,v,options);}};
 const fake={isEncryptionAvailable:()=>true,decryptString(blob){const kind=blob.toString()==='cipher-owner'?'owner':'outbox';
  if(decryptFailure===kind)throw new Error(unknownDecrypt?'DO_NOT_LOG unknown private payload':'Error while decrypting the ciphertext provided to safeStorage.decryptString.');
  if(invalidJson===kind)return '{invalid '+token;
  return kind==='owner'?JSON.stringify({...owner,schemaVersion:badOwner?2:1}):JSON.stringify([{...entry,draftId:badContinuity?'mismatch':entry.draftId}]);}};
 let baseline=null,error=null;try{baseline=s.runH1({rec:c.rec,profile:output,continuityFile:path.join(output,'continuity.json'),safeStorage:fake,io});}catch(e){error=e;}
 const final=s.finish({rec:c.rec,output,baseline,error,io});c.rec.close();
 const lines=fs.readFileSync(events,'utf8'),rows=lines.trim().split('\n').map(l=>JSON.parse(l));
 for(const forbidden of [password,token,text,'DO_NOT_LOG','VIRTUAL_KEY_ONLY'])assert(!lines.includes(forbidden));
 assert.equal(new Set(rows.filter(v=>v.event==='enter').map(v=>v.id)).size,rows.filter(v=>v.event==='enter').length);
 for(const v of rows.filter(v=>v.event==='enter'))assert.equal(rows.filter(x=>x.id===v.id&&x.event==='terminal').length,1);
 return {...c,final,rows,first:c.rec.firstError};
}
try{
 contextCase('CTX-01-COPY',()=>{},null);
 contextCase('CTX-02-MISSING',c=>fs.unlinkSync(c.source),'ENOENT');
 contextCase('CTX-03-INVALID-JSON',c=>fs.writeFileSync(c.source,'{broken'),'json_parse_failed');
 contextCase('CTX-04-MISSING-FIELD',c=>fs.writeFileSync(c.source,'{}'),'context_missing_key');
 contextCase('CTX-05-NONFRESH',c=>fs.mkdirSync(c.helper),'helper_not_fresh');
 contextCase('CTX-06-COPY-TAMPER',c=>{c.io={...fs,writeFileSync(file,v,o){fs.writeFileSync(file,JSON.stringify({os_crypt:{encrypted_key:'OTHER_VIRTUAL_KEY'}}),o);}};},'context_mismatch');
 verifyCase('CTX-07-READY',()=>{},null);
 verifyCase('CTX-08-USERDATA',(c,v)=>{v.userData=c.dir;},'path_binding_mismatch');
 verifyCase('CTX-09-SESSIONDATA',(c,v)=>{v.sessionData=c.dir;},'path_binding_mismatch');
 verifyCase('CTX-10-OTHER-ORIGIN',c=>fs.writeFileSync(path.join(c.helper,'Local State'),JSON.stringify({os_crypt:{encrypted_key:'OTHER_VIRTUAL_KEY'}})),'context_mismatch');
 verifyCase('CTX-11-UNRELATED-UPDATE',c=>fs.writeFileSync(path.join(c.helper,'Local State'),JSON.stringify({...state,unrelated:99})),null);
 verifyCase('CTX-12-READY-MISSING',c=>fs.unlinkSync(path.join(c.helper,'Local State')),'ENOENT');
 test('REC-01-IMMEDIATE',()=>{const c=setup('REC-01');c.rec.run('OP-ONE','virtual','read',()=>{const lines=fs.readFileSync(path.join(c.dir,'stages.jsonl'),'utf8').trim().split('\n');assert.equal(JSON.parse(lines.at(-1)).event,'enter');});assert.equal(JSON.parse(fs.readFileSync(path.join(c.dir,'stages.jsonl'),'utf8').trim().split('\n').at(-1)).category,'success');c.rec.close();});
 test('REC-02-UNIQUE',()=>{const c=setup('REC-02');c.rec.run('SAME','virtual','read',()=>{});assert.throws(()=>c.rec.run('SAME','virtual','read',()=>{}),e=>e.safeCode==='duplicate_id');c.rec.close();});
 test('H1-TOOLS-01-HAPPY',()=>{const c=runFixture('TOOL-HAPPY');assert.equal(c.final.passed,true);const v=JSON.parse(fs.readFileSync(path.join(c.dir,'result.json')));assert.equal(v.checks.length,7);assert(v.checks.every(x=>x.passed));assert.equal(v.notRun.length,0);});
 for(const [id,opts,stage,code] of [
  ['READ-OWNER',{readFailure:'owner-session.bin'},'H1-OP-OWNER-READ','EACCES'],
  ['DECRYPT-OWNER',{decryptFailure:'owner'},'H1-OP-OWNER-DECRYPT','native_decrypt_failed'],
  ['PARSE-OWNER',{invalidJson:'owner'},'H1-OP-OWNER-PARSE','json_parse_failed'],
  ['READ-CONTINUITY',{readFailure:'continuity.json'},'H1-OP-CONTINUITY-READ','EACCES'],
  ['PARSE-CONTINUITY',{invalidJson:'continuity'},'H1-OP-CONTINUITY-PARSE','json_parse_failed'],
  ['READ-OUTBOX',{readFailure:'outbox.bin'},'H1-OP-OUTBOX-READ','EACCES'],
  ['DECRYPT-OUTBOX',{decryptFailure:'outbox'},'H1-OP-OUTBOX-DECRYPT','native_decrypt_failed'],
  ['PARSE-OUTBOX',{invalidJson:'outbox'},'H1-OP-OUTBOX-PARSE','json_parse_failed'],
  ['UNKNOWN-NATIVE',{decryptFailure:'owner',unknownDecrypt:true},'H1-OP-OWNER-DECRYPT','unknown'],
  ['SCHEMA',{badOwner:true},'H1-OWNER-SCHEMA','comparison_failed'],
  ['CONTINUITY',{badContinuity:true},'H1-OUTBOX-CONTINUITY','comparison_failed']
 ])test('FAULT-'+id,()=>{const c=runFixture(id,opts);assert.equal(c.final.passed,false);assert.equal(c.first.id,stage);assert.equal(c.first.error.code,code);const result=JSON.parse(fs.readFileSync(path.join(c.dir,'result.json')));assert(result.notRun.every(v=>v.actual===null&&v.status==='not_run'));if(code==='comparison_failed'){assert.equal(c.first.expected,true);assert.equal(c.first.actual,false);}});
 test('REC-03-NONZERO-COLLECTION',()=>{const c=runFixture('COLLECT',{decryptFailure:'owner'});const ev=path.join(c.dir,'collected');fs.mkdirSync(ev);const v=s.collectNative(c.dir,ev,1);assert.equal(v.exitCode,1);assert.equal(v.firstNativeError.id,'H1-OP-OWNER-DECRYPT');assert.equal(v.nativePassed,false);assert.equal(v.resultPresent,true);});
 test('REC-04-RESULT-WRITE-FAILURE',()=>{const c=runFixture('WRITE',{writeFailure:true});assert.equal(c.final.resultWritten,false);assert.equal(c.first.id,'H1-OP-RESULT-WRITE');assert.equal(c.first.error.code,'EIO');const ev=path.join(c.dir,'collected');fs.mkdirSync(ev);const v=s.collectNative(c.dir,ev,1);assert.equal(v.firstNativeError.id,'H1-OP-RESULT-WRITE');assert.equal(v.resultPresent,false);assert.equal(v.collectionErrors[0].code,'receipt_missing');});
 test('REC-05-FIRST-ERROR-PRESERVED',()=>{const c=runFixture('DOUBLE',{decryptFailure:'owner',writeFailure:true});assert.equal(c.first.id,'H1-OP-OWNER-DECRYPT');assert.equal(c.final.finishError.code,'EIO');const ev=path.join(c.dir,'collected');fs.mkdirSync(ev);const v=s.collectNative(c.dir,ev,1);assert.equal(v.firstNativeError.id,'H1-OP-OWNER-DECRYPT');});
 test('REC-06-ERROR-CODE-ALLOWLIST',()=>{for(const code of ['ENOENT','EACCES','EPERM','EIO'])assert.equal(s.classify(Object.assign(new Error('private'),{code}),'read').code,code);assert.equal(s.classify(Object.assign(new Error('private'),{code:'PRIVATE_VALUE'}),'read').code,'unknown');});
}catch(e){process.exitCode=1;}
finally{fs.closeSync(log);fs.writeFileSync(path.join(root,'result.json'),JSON.stringify({at:new Date().toISOString(),passed:results.every(v=>v.passed),checks:results.length,results,productStarts:0,helperStarts:0,realDecryptCalls:0,oldCollectionsRun:0},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({round,checks:results.length,passed:results.every(v=>v.passed)}));}
