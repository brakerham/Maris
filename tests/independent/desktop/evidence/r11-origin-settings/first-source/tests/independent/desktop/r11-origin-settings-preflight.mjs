import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {recorder,ToolError,CompareError,safe,parseResult,released} from './r11-origin-settings-record.mjs';
const own=path.dirname(fileURLToPath(import.meta.url)),ev=path.join(own,'evidence/r11-origin-settings');
const out=path.join(ev,'preflight-v1');fs.mkdirSync(out);
const rows=[];let failed=false;
function check(id,expected,actual){const passed=Object.is(expected,actual);rows.push({id,expected,actual,passed});failed ||=!passed;}
function throws(fn){try{fn();return null;}catch(e){return e;}}
const rec=recorder(path.join(out,'virtual-journal.jsonl'));
try{
 rec.check('SELF.ONE',true,true);check('SELF.UNIQUE',1,rec.ids.size);
 check('SELF.DUPLICATE',true,throws(()=>rec.check('SELF.ONE',true,true)) instanceof ToolError);
 check('SELF.NO_RAW',true,throws(()=>safe('R11_PRIVATE secret token path')) instanceof ToolError);
 const compare=throws(()=>rec.check('SELF.COMPARE',true,false));rec.error('SELF.COMPARE',compare);
 rec.error('SELF.LATER',new TypeError('R11_PRIVATE'));check('SELF.FIRST_PRESERVED','SELF.COMPARE',rec.firstError.id);
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
const journal=fs.readFileSync(path.join(out,'virtual-journal.jsonl'),'utf8');check('SELF.REDACTED',false,journal.includes('R11_PRIVATE'));
const req=createRequire('C:/MarisIpcR9/R9-20261101-161412/workspace/node_modules/esbuild/package.json');
const esbuild=req('./lib/main.js');let compiled='';
for(const name of ['r11-origin-settings-contract.test.tsx','r11-origin-settings-main-fixture.ts']){
 const result=esbuild.transformSync(fs.readFileSync(path.join(own,name),'utf8'),{loader:name.endsWith('tsx')?'tsx':'ts',jsx:'automatic',format:'esm',target:'node24'});
 check(name.includes('fixture')?'SELF.FIXTURE_SYNTAX':'SELF.CASE_SYNTAX',true,result.code.length>0);
 if(name.includes('contract'))compiled=result.code;
}
// Registration-only collector: imports removed, callbacks retained but never invoked.
// Dynamic imports and fixture construction would fail; no product body is evaluated.
const nodes=[];let bodies=0;
const context=vm.createContext({__r10:null,__r10Dom:{},test:(name,body)=>{nodes.push({id:name.split(' | ')[0],name});},vi:{},makeFixture:()=>{bodies++;throw Error('forbidden_fixture');}});
vm.runInContext(compiled.replace(/^import .*?;\s*$/gm,''),context,{timeout:1000});
const expected=['R10-I06',...Array.from({length:8},(_,i)=>'R11-O'+String(i+1).padStart(2,'0')),'R10-I07',...Array.from({length:31},(_,i)=>'R10-U'+String(i+1).padStart(2,'0'))];
check('SELF.PLAN_COUNT',41,nodes.length);check('SELF.PLAN_UNIQUE',41,new Set(nodes.map(n=>n.id)).size);
check('SELF.PLAN_ORDER',true,JSON.stringify(expected)===JSON.stringify(nodes.map(n=>n.id)));check('SELF.NO_TARGET_BODY',0,bodies);
const old=fs.readFileSync(path.join(own,'r10-settings-contract.test.tsx'),'utf8').replaceAll('\r\n','\n'),current=fs.readFileSync(path.join(own,'r11-origin-settings-contract.test.tsx'),'utf8').replaceAll('\r\n','\n');
const i06=s=>s.slice(s.indexOf("test('R10-I06"),s.indexOf('\n}));',s.indexOf("test('R10-I06"))+6);
const tail=s=>s.slice(s.indexOf("test('R10-I07"));
check('SELF.I06_EXACT_BODY',i06(old),i06(current));check('SELF.I07_U_EXACT_BODY',true,tail(old)===tail(current));
// Replace bulky comparison text with digests in the safe preflight artifact.
for(const row of rows)if(row.id==='SELF.I06_EXACT_BODY'){row.expected=createHash('sha256').update(row.expected).digest('hex');row.actual=createHash('sha256').update(row.actual).digest('hex');}
check('SELF.ABSOLUTE_ROOT',true,path.isAbsolute(own)&&own===path.resolve('D:/CodeX_gap/wife-system/tests/independent/desktop'));
check('SELF.DATE_VALID',true,Number.isFinite(Date.parse(new Date().toISOString())));
fs.writeFileSync(path.join(ev,'independent-plan.json'),JSON.stringify({nodes,excludedHistorical:['R10-I01','R10-I02','R10-I03','R10-I04','R10-I05'],productBodyExecuted:false,oldToNew:{I06:'exact body, same ID',I07_U01_U31:'exact tail, same IDs'},order:expected},null,2)+'\n',{flag:'wx'});
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({at:new Date().toISOString(),passed:!failed,rows,productStarts:0,helperStarts:0,targetImported:false},null,2)+'\n',{flag:'wx'});
process.stdout.write(JSON.stringify({passed:!failed,comparisons:rows.length,nodes:nodes.length,productStarts:0,helperStarts:0})+'\n');if(failed)process.exitCode=1;
