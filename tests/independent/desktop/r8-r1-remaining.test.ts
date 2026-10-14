import {test,expect} from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const req=createRequire('C:/MarisModulesR6/R6-20261013-002100/workspace/node_modules/openapi-typescript/package.json');
const api=req('./dist/index.cjs'),ts=req('../typescript/lib/typescript.js');
const repo='D:/CodeX_gap/wife-system';
const journal=path.join(repo,'tests/independent/desktop/evidence/r8-r1/public/assertions.jsonl');
function check(id:string,actual:any,expected:any){fs.appendFileSync(journal,JSON.stringify({id,operator:'eq',expected,actual,passed:actual===expected})+'\n');expect(actual,id).toBe(expected);}
const source=fs.readFileSync(path.join(repo,'apps/desktop/scripts/check-generated.mjs'),'utf8');
// Execute the original checker control flow with virtual file/process ports only.
// No repository artifact generation, process launch or network request occurs.
function gate(currentSchema:string,currentTypes:string,storedSchema:string,storedTypes:string){
 const script=ts.transpileModule(source.replaceAll('import.meta.url',JSON.stringify('file:///V:/virtual/apps/desktop/scripts/check-generated.mjs')),{compilerOptions:{esModuleInterop:true,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
 const temp=path.resolve('V:/virtual/tmp'),desktop=path.resolve('V:/virtual/apps/desktop');const errors:string[]=[];let calls=0,exit=0,removed=0;
 class Exit extends Error{constructor(public code:number){super();}}
 const ports:any={
  'node:fs':{existsSync:()=>true,mkdtempSync:()=>temp,rmSync:(p:string)=>{if(p!==temp)throw Error('virtual_boundary');removed++;},readFileSync:(p:string)=>{
   if(p===path.join(temp,'host.openapi.json'))return currentSchema;if(p===path.join(temp,'host-api.ts'))return currentTypes;
   if(p===path.join(desktop,'openapi/host.openapi.json'))return storedSchema;if(p===path.join(desktop,'src/generated/host-api.ts'))return storedTypes;throw Error('unplanned_read');}},
  'node:child_process':{spawnSync:()=>{calls++;return{status:0};}},'node:os':{tmpdir:()=>temp},'node:path':path,'node:url':req('node:url')};
 try{vm.runInNewContext(script,{exports:{},require:(name:string)=>{if(!(name in ports))throw Error('unplanned_import');return ports[name];},process:{env:{},platform:'win32',execPath:'virtual-node',exit:(code:number)=>{throw new Exit(code);}},console:{error:(s:string)=>errors.push(s),log:()=>{}}},{timeout:1000});}catch(e){if(e instanceof Exit)exit=e.code;else throw e;}
 return{exit,calls,errors,removed};
}
const schema=(mode:string)=>({openapi:'3.0.3',info:{title:'Virtual',version:'1'},paths:{},components:{schemas:{Sample:{type:'object',properties:{value:{type:mode==='field'?'number':'string'},state:{type:'string',enum:mode==='enum'?['new']:['old']},extra:{type:'string'}},required:mode==='required'?['value','state','extra']:['value','state']}}}});
const generate=async(s:any)=>api.astToString(await api.default(s));
function consumerErrors(types:string){
 const text=types+'\nconst value: components["schemas"]["Sample"] = {value:"virtual",state:"old"};\n';
 const file=ts.createSourceFile('/virtual.ts',text,ts.ScriptTarget.Latest,true);const options={noLib:true,noEmit:true,strict:true};
 const host={getSourceFile:(n:string)=>n==='/virtual.ts'?file:undefined,getDefaultLibFileName:()=>'',writeFile:()=>{throw Error('write_forbidden');},getCurrentDirectory:()=> '/',getDirectories:()=>[],fileExists:(n:string)=>n==='/virtual.ts',readFile:(n:string)=>n==='/virtual.ts'?text:undefined,getCanonicalFileName:(n:string)=>n,useCaseSensitiveFileNames:()=>true,getNewLine:()=> '\n'};
 return ts.createProgram(['/virtual.ts'],options,host).getSemanticDiagnostics().filter((d:any)=>[2322,2741].includes(d.code)).length;
}
test('R8R1-PUB-01 | exact generated virtual baseline accepted',async()=>{
 const s=schema('baseline'),t=await generate(s),r=gate(JSON.stringify(s),t,JSON.stringify(s),t);
 check('PUB01.EXIT',r.exit,0);check('PUB01.EXPORT_AND_GENERATE',r.calls,2);check('PUB01.LOCATIONS',r.errors.length,0);check('PUB01.CONSUMER',consumerErrors(t),0);
});
for(const [id,mode]of [['02','field'],['03','enum'],['04','required']])test(`R8R1-PUB-${id} | virtual DTO ${mode} drift rejects and consumer no longer compiles`,async()=>{
 const old=schema('baseline'),fresh=schema(mode),before=await generate(old),after=await generate(fresh),r=gate(JSON.stringify(fresh),after,JSON.stringify(old),before);
 check(`PUB${id}.EXIT`,r.exit,1);check(`PUB${id}.SCHEMA_LOCATION`,r.errors.length===1&&r.errors[0].replaceAll('\\','/').endsWith('apps/desktop/openapi/host.openapi.json'),true);
 check(`PUB${id}.GENERATED_CHANGED`,before!==after,true);check(`PUB${id}.COMPILE_REJECTED`,consumerErrors(after)>0,true);
});
test('R8R1-PUB-05 | stale generated type pinpoints generated artifact',async()=>{
 const s=JSON.stringify(schema('baseline')),types=await generate(schema('baseline'));const r=gate(s,types,s,types+'\n// virtual stale');
 check('PUB05.EXIT',r.exit,1);check('PUB05.TYPE_LOCATION',r.errors.length===1&&r.errors[0].replaceAll('\\','/').endsWith('apps/desktop/src/generated/host-api.ts'),true);
});
test('R8R1-PUB-06 | real main registry startup and generic Shell wiring',()=>{
 const main=fs.readFileSync(path.join(repo,'apps/desktop/src/renderer/main.tsx'),'utf8');
 check('PUB06.COMPILE_BEFORE_MOUNT',main.indexOf('compileRegistry([dailyFinanceContribution])')<main.indexOf('createRoot(document'),true);
 check('PUB06.COMPILED_REGISTRY_PROP',main.includes('<DesktopApp registry={compiled} />'),true);
 const files=['src/shell/Shell.tsx','src/renderer/module-routes.tsx'];let branchCount=0;
 for(const f of files){const s=ts.createSourceFile(f,fs.readFileSync(path.join(repo,'apps/desktop',f),'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);function visit(n:any){if((ts.isIfStatement(n)||ts.isConditionalExpression(n)||ts.isSwitchStatement(n))&&/moduleId/.test((n.expression??n.condition).getText(s)))branchCount++;ts.forEachChild(n,visit);}visit(s);}
 check('PUB06.MODULE_ID_BRANCHES',branchCount,0);
});
