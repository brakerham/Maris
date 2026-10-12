import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import ts from 'file:///C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/typescript/lib/typescript.js';
const own = path.dirname(fileURLToPath(import.meta.url));
const evidence = path.join(own, 'evidence/r7-recovery');
const must = (value, reason) => { if (!value) throw Error(reason); };
const sha = value => createHash('sha256').update(value).digest('hex');
must(!fs.existsSync(path.join(evidence, 'recovery-source.sha256')), 'r7_sources_already_frozen');
const test = fs.readFileSync(path.join(own, 'r7-recovery.test.tsx'), 'utf8');
const mapping = JSON.parse(fs.readFileSync(path.join(evidence, 'assertion-map.json'), 'utf8'));
const ids = mapping.assertions.map(row => row.id);
must(new Set(ids).size === ids.length, 'r7_duplicate_assertion_ids');
const used = [...test.matchAll(/check\('([^']+)'/g)].map(match => match[1]);
must(ids.every(id => used.includes(id)) && used.every(id => ids.includes(id)), 'r7_mapping_incomplete');
must(mapping.assertions.filter(row => row.kind === 'legacy').map(row => row.id).sort().join(',') === 'legacy_first_retry_total_2,legacy_initial_exact_1', 'r7_legacy_scope');
const source = ts.createSourceFile('r7.test.tsx', test, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const runtimeImports = [];
const visit = node => { if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) runtimeImports.push(node.arguments[0]?.text); ts.forEachChild(node, visit); };
visit(source);
must(runtimeImports.length === 4 && !runtimeImports.some(name => name.includes('/main') || name === 'jsdom'), 'r7_preload_or_main');
must(test.includes('createElement(StrictMode') && test.includes("const initialBaseline = counts.loads;") && (test.match(/const initialBaseline =/g) ?? []).length === 1, 'r7_baseline_or_strictmode');
must(!/vi\.(mock|doMock|resetModules)|\.revalidate\(|\.navigate\(|\.invalidate\(/.test(test), 'r7_router_manipulation');
must(test.indexOf('recorderSelftest();') < test.indexOf("await op('OP.DOM_SETUP'") && test.indexOf('recorderSelftest();') < test.indexOf("await op('OP.IMPORTS'"), 'r7_selftest_order');
const controller = fs.readFileSync(path.join(own, 'r7-recovery-run.ps1'), 'utf8');
must(controller.includes("'--configLoader','native'") && controller.includes('processDeadlineMs=75000') && controller.includes('mainBudget=0'), 'r7_controller_budget');
const setup = fs.readFileSync(path.join(own, 'r7-recovery-setup.mjs'), 'utf8');
must(setup.includes('createRequire(packageUrl)') && setup.includes('nativeRequire(resolvedApi)') && setup.includes("if (!keys.has(key))") && !setup.includes('new JSDOM'), 'r7_setup_contract');
const sources = fs.readdirSync(own).filter(name => name.startsWith('r7-recovery') && fs.statSync(path.join(own,name)).isFile()).sort();
const syntax = [];
for (const name of sources) {
  if (name.endsWith('.mjs')) { const result = spawnSync(process.execPath, ['--check', path.join(own,name)], {shell:false,encoding:'utf8'}); must(result.status === 0,'r7_mjs_syntax'); syntax.push(name); }
  if (name.endsWith('.tsx')) { const result = ts.transpileModule(fs.readFileSync(path.join(own,name),'utf8'), {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext},reportDiagnostics:true}); must(!result.diagnostics.some(d=>d.category===ts.DiagnosticCategory.Error),'r7_tsx_syntax'); syntax.push(name); }
}
const start = JSON.parse(fs.readFileSync(path.join(evidence,'start-audit.json'),'utf8'));
for(const item of Object.values(start.versions)) must(sha(fs.readFileSync(path.join(item.physicalRoot,'package.json')))===item.packageJsonSha256,'r7_dependency_drift');
must(sha(fs.readFileSync(start.nativeJsdom.apiRealPath))===start.nativeJsdom.apiSha256 && process.version==='v24.21.0','r7_native_identity');
const record = {syntax, assertionDefinitions:ids.length, operationIds:mapping.operationIds.length, runtimeImports, nativeJsdom:start.nativeJsdom, node:process.version, versions:start.versions, targetRuns:0, mainImports:0,
  budgets:{initialization:60000,body:10000,cleanup:2000,overall:75000,observation:5000,vitestOuter:12000}};
fs.writeFileSync(path.join(evidence,'static-preflight.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
const files = [...sources, 'evidence/r7-recovery/assertion-map.json'].sort();
fs.writeFileSync(path.join(evidence,'recovery-source.sha256'), files.map(name=>`${name}\t${sha(fs.readFileSync(path.join(own,name)))}`).join('\n')+'\n',{flag:'wx'});
console.log(JSON.stringify({staticPassed:true,sourceAndContractFiles:files.length,assertionDefinitions:ids.length,operations:mapping.operationIds.length,targetRuns:0}));
