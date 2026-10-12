import {test,expect} from 'vitest';
import {appendFileSync} from 'node:fs';
import {compileRegistry} from '../../../apps/desktop/src/modules/registry';
const base=()=>({moduleId:'virtual_finance',version:'1.0.0',hostUiMajor:1,expectedApiPrefixes:['/api/v1/virtual'],navigation:{label:'virtual',order:1},routes:[{routeId:'virtual_route',path:'/virtual'}],agentPanel:{profileId:'virtual_finance.assistant@1',title:'virtual'},settings:[{key:'virtual_setting',schemaVersion:1}],companion:{appearanceId:'virtual_appearance',label:'virtual'}});
const observe=(id:string,expected:number,fn:()=>number)=>{const write=(v:object)=>appendFileSync(new URL('./evidence/r7-recovery/public/assertions.jsonl',import.meta.url),JSON.stringify(v)+'\n');write({id,stage:'assert_enter',expected});const actual=fn();write({id,stage:actual===expected?'assert_pass':'assert_fail',expected,actual});expect(actual).toBe(expected)};
const rejected=(v:unknown)=>{try{compileRegistry([v]);return 0}catch{return 1}};
for(const place of ['top','navigation','route','agentPanel','setting','companion'] as const){test(`R7-PUB-STRICT-${place} | unknown field rejected`,()=>{
 observe('R7-PUB-STRICT-'+place,1,()=>{const v:any=base();const target=place==='top'?v:place==='route'?v.routes[0]:place==='setting'?v.settings[0]:v[place];target.virtualUnexpected=true;return rejected(v)})
})}
test('R7-PUB-REQUIRED | missing structural fields rejected',()=>observe('R7-PUB-REQUIRED',6,()=>['expectedApiPrefixes','navigation','routes','agentPanel','settings','companion'].reduce((n,k)=>{const v:any=base();delete v[k];return n+rejected(v)},0)));
test('R7-PUB-SHAPE | empty required arrays and malformed structural scalars rejected',()=>observe('R7-PUB-SHAPE',6,()=>[
 {...base(),routes:[]},{...base(),expectedApiPrefixes:[]},{...base(),navigation:{label:'',order:1}},
 {...base(),navigation:{label:'virtual',order:0.5}},{...base(),settings:[{key:'virtual_setting',schemaVersion:0}]},{...base(),companion:{appearanceId:'virtual_appearance',label:''}}
].reduce((n,v)=>n+rejected(v),0)));
