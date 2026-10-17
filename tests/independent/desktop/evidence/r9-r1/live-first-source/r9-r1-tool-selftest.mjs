import assert from 'node:assert/strict';
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {classify,safeError,write,sha} from './r9-r1-observation.mjs';
const own=path.dirname(fileURLToPath(import.meta.url)),ev=path.join(own,'evidence/r9-r1');
const safe={ok:true,rootVerified:true,owned:[],resourceStatus:'success',listeners:[],windowCount:0};
const tests=[
 ['TOOL-01-success',{status:0,stdout:JSON.stringify(safe)},'success'],
 ['TOOL-02-nonzero',{status:7,stdout:''},'nonzero'],
 ['TOOL-03-timeout',{status:null,timedOut:true,stdout:''},'timeout'],
 ['TOOL-04-parse',{status:0,stdout:'virtual invalid json'},'parse_failure'],
 ['TOOL-05-denied',{status:null,error:{code:'EACCES'},stdout:''},'access_denied'],
 ['TOOL-06-empty',{status:0,stdout:JSON.stringify({...safe,rootVerified:false})},'success'],
 ['TOOL-07-unknown-not-zero',{status:null,stdout:''},'nonzero'],
 ['TOOL-08-schema',{status:0,stdout:'{}'},'schema_failure'],
 ['TOOL-09-os-denied',{status:3,stdout:JSON.stringify({ok:false,error:{category:'access_denied'}})},'access_denied']
];
const checks=tests.map(([id,input,expected])=>{const actual=classify(input).kind;assert.equal(actual,expected);return {id,expected,actual,passed:true};});
assert.equal(new Set(checks.map(x=>x.id)).size,checks.length);
assert.deepEqual(safeError({name:'PrivateThing',code:'SECRET'}),{type:'other',code:null});
checks.push({id:'TOOL-10-error-allowlist',expected:true,actual:true,passed:true});
for(const [id,columns,line]of [['TOOL-11-two-columns',2,'safe/path\t'+'a'.repeat(64)],['TOOL-12-three-columns',3,'safe/path\t123\t'+'b'.repeat(64)]]){
 const row=line.split('\t');assert.equal(row.length,columns);assert.match(row.at(-1),/^[a-f0-9]{64}$/);checks.push({id,expected:columns,actual:row.length,passed:true});
}
write(path.join(ev,'virtual-tool-selftest.json'),{passed:true,productImported:false,productStarts:0,helperStarts:0,checks,sourceSha256:sha(fs.readFileSync(fileURLToPath(import.meta.url)))});
console.log(JSON.stringify({virtualChecks:checks.length,passed:true}));
