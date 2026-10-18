const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {app,safeStorage}=require('electron');
const cfg=require('D:/CodeX_gap/wife-system/tests/independent/desktop/r9-r2-config.cjs');
const identity=require('D:/CodeX_gap/wife-system/tests/independent/desktop/r9-r2-identity.cjs');
const root=cfg.ext;
const output=path.join(root,'output/H1');
const profile=path.join(root,'profile-main');
app.setPath('userData',path.join(root,'helper-profile-H1'));
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('disable-gpu');
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const write=(name,value)=>fs.writeFileSync(path.join(output,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const checks=[];
function check(id,expected,actual){if(checks.some(c=>c.id===id))throw Error('duplicate_id');const at=new Date().toISOString();fs.appendFileSync(path.join(output,'checks.jsonl'),JSON.stringify({id,event:'enter',at,expected})+'\n');checks.push({id,operator:'eq',expected,actual,passed:expected===actual});write('check-'+checks.length+'.json',checks.at(-1));fs.appendFileSync(path.join(output,'checks.jsonl'),JSON.stringify({...checks.at(-1),event:'terminal',at:new Date().toISOString()})+'\n');if(expected!==actual)throw Error('comparison_failed');}
const timer=setTimeout(()=>{write('deadline.json',{timedOut:true});app.exit(2);},55000);
app.whenReady().then(async()=>{
  const descriptor=JSON.parse(fs.readFileSync(path.join(output,'launch.json'),'utf8'));
  const ready={pid:process.pid,scriptPath:identity.canonical(__filename),scriptSha256:sha(fs.readFileSync(__filename)),marker:cfg.marker,output,callId:'H1'};
  if(!identity.receiptCheck(ready,descriptor,{pid:process.pid,receiptPath:path.join(output,'ready.json'),expectedReceiptPath:path.join(output,'ready.json')}).passed)throw Error('ready_identity');
  write('ready.json',ready);
  while(!fs.existsSync(path.join(output,'release.json')))await new Promise(r=>setTimeout(r,25));
  check('H1-NATIVE-AVAILABLE',true,safeStorage.isEncryptionAvailable());
  const ownerBlob=fs.readFileSync(path.join(profile,'owner-session.bin'));
  const owner=JSON.parse(safeStorage.decryptString(ownerBlob));
  check('H1-OWNER-SCHEMA',true,owner.schemaVersion===1&&typeof owner.handle==='string'&&typeof owner.password==='string');
  check('H1-OWNER-READY',true,owner.password.length>0&&typeof owner.refreshToken==='string'&&owner.refreshToken.length>0&&!owner.repairRequired);
  check('H1-OWNER-NO-PLAIN',true,!ownerBlob.includes(Buffer.from(owner.password))&&!ownerBlob.includes(Buffer.from(owner.refreshToken)));
  const continuity=JSON.parse(fs.readFileSync(path.join(root,'continuity.json'),'utf8'));
  const boxBlob=fs.readFileSync(path.join(profile,'outbox.bin'));
  const entries=JSON.parse(safeStorage.decryptString(boxBlob));
  check('H1-OUTBOX-COUNT',1,entries.length);
  const item=entries[0];
  check('H1-OUTBOX-CONTINUITY',true,item.draftId===continuity.draftId&&item.clientEventId===continuity.eventId&&item.body===continuity.body&&item.digest===sha(continuity.body));
  check('H1-OUTBOX-NO-PLAIN',true,!boxBlob.includes(Buffer.from(continuity.body)));
  const baseline={ownerIdentityDigest:sha(JSON.stringify([owner.handle,owner.password])),refreshPresent:true,
    draftDigest:sha(item.draftId),eventDigest:sha(item.clientEventId),payloadDigest:item.digest,entries:entries.length};
  write('baseline.json',baseline);
  write('result.json',{passed:true,checks,baseline,productImported:false,fixtureWritten:false});
}).catch(error=>{write('result.json',{passed:false,checks,errorKind:['Error','TypeError','SyntaxError'].includes(error.name)?error.name:'other',code:error.message==='comparison_failed'?'comparison_failed':'operation_error',productImported:false});process.exitCode=1;})
.finally(()=>{clearTimeout(timer);app.exit(process.exitCode??0);});
