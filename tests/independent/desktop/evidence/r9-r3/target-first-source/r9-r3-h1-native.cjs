const fs=require('node:fs'),path=require('node:path');
const {app,safeStorage}=require('electron');
const cfg=require('D:/CodeX_gap/wife-system/tests/independent/desktop/r9-r3-config.cjs');
const identity=require('D:/CodeX_gap/wife-system/tests/independent/desktop/r9-r2-identity.cjs');
const storage=require('D:/CodeX_gap/wife-system/tests/independent/desktop/r9-r3-storage.cjs');
const output=path.join(cfg.ext,'output/H1'),helper=path.join(cfg.ext,'helper-profile-H1'),profile=path.join(cfg.ext,'profile-main');
const rec=storage.createRecorder(path.join(output,'stages.jsonl'));
const write=(name,v)=>fs.writeFileSync(path.join(output,name),JSON.stringify(v,null,2)+'\n',{flag:'wx'});
let initialError=null,ended=false;
function terminate(error,baseline=null){
 if(ended)return;ended=true;clearTimeout(timer);
 let terminal;
 try{terminal=storage.finish({rec,output,baseline,error});}
 catch(e){terminal={passed:false,firstError:rec.firstError,finishError:storage.classify(e,'write'),resultWritten:false};}
 // Independent of result.json writing; the controller also has its own collection receipt.
 try{write('native-terminal.json',{...terminal,pid:process.pid,at:new Date().toISOString()});}catch{}
 try{rec.close();}catch{}
 app.exit(terminal.passed?0:1);
}
const timer=setTimeout(()=>terminate(Object.assign(new Error('deadline'),{code:'ETIMEDOUT'})),55000);
try{
 rec.run('H1-CONTEXT-BIND','helper_paths','bind',()=>{
  app.setPath('userData',helper);app.setPath('sessionData',helper);
 });
 app.disableHardwareAcceleration();app.commandLine.appendSwitch('disable-gpu');
}catch(e){initialError=e;}
if(initialError)terminate(initialError);
else app.whenReady().then(async()=>{
 let error=null,baseline=null;
 try{
  const context=storage.verifyContext({source:path.join(profile,'Local State'),helper,userData:app.getPath('userData'),sessionData:app.getPath('sessionData'),boundary:cfg.ext,rec,prefix:'H1-CONTEXT-READY'});
  const descriptor=rec.run('H1-DESCRIPTOR-READ','launch_descriptor','read',()=>JSON.parse(fs.readFileSync(path.join(output,'launch.json'),'utf8')));
  const ready={pid:process.pid,scriptPath:identity.canonical(__filename),scriptSha256:identity.sha(fs.readFileSync(__filename)),marker:cfg.marker,output,callId:'H1',context};
  rec.run('H1-READY-IDENTITY','native_ready','validate',()=>{
   if(!identity.receiptCheck(ready,descriptor,{pid:process.pid,receiptPath:path.join(output,'ready.json'),expectedReceiptPath:path.join(output,'ready.json')}).passed)storage.fail('receipt_missing');
  });
  rec.run('H1-READY-WRITE','native_ready','write',()=>write('ready.json',ready));
  while(!fs.existsSync(path.join(output,'release.json')))await new Promise(r=>setTimeout(r,25));
  rec.run('H1-RELEASE-READ','controller_release','read',()=>{
   const v=JSON.parse(fs.readFileSync(path.join(output,'release.json'),'utf8'));
   if(v.authorized!==true||v.pid!==process.pid||v.callId!=='H1')storage.fail('receipt_missing');
  });
  baseline=storage.runH1({rec,profile,continuityFile:path.join(cfg.ext,'continuity.json'),safeStorage});
 }catch(e){error=e;}
 try{storage.verifyContext({source:path.join(profile,'Local State'),helper,userData:app.getPath('userData'),sessionData:app.getPath('sessionData'),boundary:cfg.ext,rec,prefix:'H1-CONTEXT-AFTER'});}catch(e){error??=e;}
 terminate(error,baseline);
}).catch(error=>terminate(error));
