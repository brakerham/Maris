import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';
const own=path.dirname(fileURLToPath(import.meta.url));const phase=process.argv[2];if(!['e1','e2','e3'].includes(phase))throw Error('d16_syntax_phase');
const require=createRequire(import.meta.url);const ts=require('C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/typescript/lib/typescript.js');
const file=path.join(own,phase,'initialization.test.ts');const source=fs.readFileSync(file,'utf8');
const result=ts.transpileModule(source,{fileName:file,reportDiagnostics:true,compilerOptions:{target:ts.ScriptTarget.ESNext,module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX}});
const errors=(result.diagnostics||[]).filter(x=>x.category===ts.DiagnosticCategory.Error).map(x=>x.code);
const blockedLiteral=/apps\/|src\/wife|r4-r3-|DailyFinancePage|module-routes|renderer\/main/.test(source);
const record={syntaxOnly:true,targetExecuted:false,typescriptVersion:ts.version,errorCodes:errors,forbiddenProductLiteral:blockedLiteral};
fs.writeFileSync(path.join(own,phase,'syntax.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(record));if(errors.length||blockedLiteral)process.exitCode=1;
