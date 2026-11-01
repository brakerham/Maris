import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {recorder,ToolError,CompareError,safe,parseResult,released} from './r10-settings-record.mjs';
const own=path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Z]:)/,'$1');
const out=path.join(own,'evidence/r10-settings/preflight-v2');fs.mkdirSync(out);
const rows=[];let failed=false;
function check(id,expected,actual){const passed=Object.is(expected,actual);rows.push({id,expected,actual,passed});failed ||=!passed;}
function throws(fn){try{fn();return null;}catch(e){return e;}}
const rec=recorder(path.join(out,'virtual-journal.jsonl'));
try{
 rec.check('SELF.ONE',true,true);check('SELF.UNIQUE',1,rec.ids.size);
 check('SELF.DUPLICATE',true,throws(()=>rec.check('SELF.ONE',true,true)) instanceof ToolError);
 check('SELF.NO_RAW',true,throws(()=>safe('R10_PRIVATE secret token path')) instanceof ToolError);
 const compare=throws(()=>rec.check('SELF.COMPARE',true,false));rec.error('SELF.COMPARE',compare);
 rec.error('SELF.LATER',new TypeError('R10_PRIVATE'));check('SELF.FIRST_PRESERVED','SELF.COMPARE',rec.firstError.id);
 check('SELF.COMPARE_CLASS',true,compare instanceof CompareError);
 check('SELF.MISSING',true,throws(()=>parseResult(null)) instanceof ToolError);
 check('SELF.BAD_JSON','SyntaxError',throws(()=>parseResult('{')).name);
 check('SELF.BAD_RESULT',true,throws(()=>parseResult('{}')) instanceof ToolError);
 check('SELF.GOOD_RESULT',true,parseResult('{"passed":true}').passed);
 let releases=0;let received=null;const first=new Error('virtual_first');
 try{await released(()=>{throw first;},()=>{releases++;throw new Error('virtual_cleanup');});}catch(e){received=e;}
 check('SELF.FINALLY_RELEASE',1,releases);check('SELF.FIRST_NOT_MASKED',true,received===first);
 let written='';const shortIO={openSync:()=>9,writeSync:(_fd,b,o,len)=>{const n=Math.min(7,len);written+=b.subarray(o,o+n).toString();return n;},fsyncSync(){},closeSync(){}};
 const short=recorder('virtual',shortIO);short.check('SELF.SHORT',1,1);short.close();check('SELF.SHORT_COMPLETE',2,written.trim().split('\n').map(JSON.parse).length);
}finally{rec.close();}
const text=fs.readFileSync(path.join(out,'virtual-journal.jsonl'),'utf8');check('SELF.REDACTED',false,text.includes('R10_PRIVATE'));
const req=createRequire('C:/MarisSettingsR8/R8-20261019-103900/workspace/node_modules/esbuild/package.json');
const esbuild=req('./lib/main.js');
for(const name of ['r10-settings-contract.test.tsx','r10-settings-main-fixture.ts']){
 const result=esbuild.transformSync(fs.readFileSync(path.join(own,name),'utf8'),{loader:name.endsWith('tsx')?'tsx':'ts',jsx:'automatic',format:'esm',target:'node24'});
 check(name.includes('fixture')?'SELF.FIXTURE_SYNTAX':'SELF.CASE_SYNTAX',true,result.code.length>0);
}
const plan=JSON.parse(fs.readFileSync(path.join(own,'evidence/r10-settings/independent-plan.json'),'utf8'));
check('SELF.PLAN_UNIQUE',plan.nodes.length,new Set(plan.nodes.map(n=>n.id)).size);check('SELF.PLAN_COUNT',38,plan.nodes.length);
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({at:new Date().toISOString(),passed:!failed,rows,productStarts:0,helperStarts:0,targetImported:false},null,2)+'\n',{flag:'wx'});
process.stdout.write(JSON.stringify({passed:!failed,comparisons:rows.length,productStarts:0,helperStarts:0})+'\n');if(failed)process.exitCode=1;
