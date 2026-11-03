'use strict';
const fs=require('node:fs'),path=require('node:path');const {sha}=require('./r9-r2-identity.cjs');
const storage=require('./r9-r3-storage.cjs');
function runData({scenario,rec,profile,continuityFile,safeStorage,oldBaseline,expected=null,io=fs,now=Date.now()}){
 const op=(name,role,operation,fn)=>rec.run(scenario+'-OP-'+name,role,operation,fn);
 const check=(name,e,a)=>rec.check(scenario+'-'+name,e,a);
 check('NATIVE-AVAILABLE',true,op('AVAILABLE','native','availability',()=>safeStorage.isEncryptionAvailable()));
 const ownerBlob=op('OWNER-READ','owner','read',()=>io.readFileSync(path.join(profile,'owner-session.bin')));
 const owner=op('OWNER-PARSE','owner','parse',()=>JSON.parse(op('OWNER-DECRYPT','owner','decrypt',()=>safeStorage.decryptString(ownerBlob))));
 check('OWNER-SCHEMA',true,owner.schemaVersion===1&&typeof owner.handle==='string'&&typeof owner.password==='string'&&typeof owner.refreshToken==='string');
 check('OWNER-STABLE-IDENTITY',oldBaseline.ownerIdentityDigest,sha(JSON.stringify([owner.handle,owner.password])));
 check('REFRESH-PRESENT',true,owner.refreshToken.length>0&&!owner.repairRequired);
 const continuity=op('CONTINUITY-PARSE','fixture','parse',()=>JSON.parse(op('CONTINUITY-READ','fixture','read',()=>io.readFileSync(continuityFile,'utf8'))));
 const boxBlob=op('OUTBOX-READ','outbox','read',()=>io.readFileSync(path.join(profile,'outbox.bin')));
 const entries=op('OUTBOX-PARSE','outbox','parse',()=>JSON.parse(op('OUTBOX-DECRYPT','outbox','decrypt',()=>safeStorage.decryptString(boxBlob))));
 check('ENTRIES-ARRAY',true,Array.isArray(entries));
 const original=entries.find(x=>x.draftId===continuity.draftId);
 check('ORIGINAL-CONTINUITY',true,!!original&&original.clientEventId===continuity.eventId&&original.body===continuity.body&&original.digest===sha(continuity.body));
 check('DRAFT-DIGEST',oldBaseline.draftDigest,sha(continuity.draftId));check('EVENT-DIGEST',oldBaseline.eventDigest,sha(continuity.eventId));check('PAYLOAD-DIGEST',oldBaseline.payloadDigest,sha(continuity.body));
 const summary=rows=>rows.map(x=>({draft:sha(x.draftId),event:sha(x.clientEventId),body:sha(x.body),digest:x.digest,state:x.state,createdAt:x.createdAt,updatedAt:x.updatedAt})).sort((a,b)=>a.event.localeCompare(b.event));
 if(scenario==='H2'){
  check('ORIGINAL-COUNT',oldBaseline.entries,entries.length);
  const states=['draft','queued','queued','sending'];
  const added=states.map((state,i)=>({draftId:'11000000-0000-4000-8000-'+String(i+1).padStart(12,'0'),clientEventId:'22000000-0000-4000-8000-'+String(i+1).padStart(12,'0'),body:'R11_R1_VIRTUAL_RETENTION_'+i,digest:sha('R11_R1_VIRTUAL_RETENTION_'+i),state,createdAt:now-(i===2?1000:31*86400000),updatedAt:now-(i===2?1000:31*86400000)}));
  check('SEED-UNIQUE',true,new Set([...entries,...added].map(x=>x.clientEventId)).size===entries.length+added.length);
  const before=summary(entries),after=summary([...entries,...added]),removed=added.slice(0,2).map(x=>sha(x.clientEventId));
  const sealed=op('SEED-ENCRYPT','virtual_outbox','encrypt',()=>safeStorage.encryptString(JSON.stringify([...entries,...added])));
  op('SEED-WRITE','virtual_outbox','write',()=>{const target=path.join(profile,'outbox.bin');io.writeFileSync(target+'.r11-seed.tmp',sealed,{flag:'wx'});io.renameSync(target+'.r11-seed.tmp',target);});
  check('SEED-READBACK',sha(sealed),sha(io.readFileSync(path.join(profile,'outbox.bin'))));
  check('OWNER-UNCHANGED',sha(ownerBlob),sha(io.readFileSync(path.join(profile,'owner-session.bin'))));
  return {before,after,removed,original:summary([original])[0],ownerIdentityDigest:oldBaseline.ownerIdentityDigest,seeded:4};
 }
 if(!expected)throw Error('expected_missing');
 const wanted=scenario==='H3'?expected.after:expected.after.filter(x=>!expected.removed.includes(x.event));
 check('COUNT',wanted.length,entries.length);
 check('ALL-PLAINTEXT-DIGESTS-IDS-STATES',true,JSON.stringify(summary(entries))===JSON.stringify(wanted));
 check('ORIGINAL-PROTECTED',true,JSON.stringify(summary([original])[0])===JSON.stringify(expected.original));
 return {entries:entries.length,readonly:true,expectedMatched:true};
}
function finish({rec,output,baseline=null,error=null}){
 let writeError=null;const result={passed:!error,checks:rec.checks,firstError:rec.firstError,error:error?storage.classify(error,'body'):null,baseline:error?null:baseline,productImported:false};
 try{if(!error)fs.writeFileSync(path.join(output,'baseline.json'),JSON.stringify(baseline)+'\n',{flag:'wx'});fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});}catch(e){writeError=storage.classify(e,'write');}
 return {passed:!error&&!writeError,firstError:rec.firstError,finishError:writeError,resultWritten:!writeError};
}
module.exports={runData,finish};
