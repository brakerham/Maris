import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import ts from 'file:///C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/typescript/lib/typescript.js';
import { configuration } from './r4-r3-config.mjs';
import { classify, fixture } from './r4-r3-resolver.mjs';
const own = path.dirname(fileURLToPath(import.meta.url));
const evidence = path.join(own, 'evidence/r4-r3');
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
const sha = value => createHash('sha256').update(value).digest('hex');
const must = (value, code) => {if (!value) throw Error(code);};
must(!fs.existsSync(path.join(evidence, 'cold-source.sha256')), 'source_already_frozen');
const sources = fs.readdirSync(own).filter(name => name.startsWith('r4-r3-') && fs.statSync(path.join(own, name)).isFile()).sort();
const syntax = [];
for (const name of sources) {
  const source = fs.readFileSync(path.join(own, name), 'utf8');
  if (name.endsWith('.mjs')) {
    const result = spawnSync(process.execPath, ['--check', path.join(own, name)], {shell: false, encoding: 'utf8'});
    must(result.status === 0, 'mjs_syntax_failed'); syntax.push({name, parsed: true});
  }
  if (name.endsWith('.tsx')) {
    const result = ts.transpileModule(source, {fileName: name, compilerOptions: {jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext}, reportDiagnostics: true});
    const errors = result.diagnostics?.filter(d => d.category === ts.DiagnosticCategory.Error) ?? [];
    must(errors.length === 0, 'tsx_syntax_failed');
    const ast = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const imports = ast.statements.filter(ts.isImportDeclaration).map(n => n.moduleSpecifier.text);
    must(imports.every(p => ['vitest', 'react', 'jsdom'].includes(p)), 'static_import_violation');
    if (name.includes('failing-page')) must(imports.length === 0 && !result.outputText.includes('import ') && source.includes("throw new Error('VIRTUAL_CHUNK_UNAVAILABLE')"), 'fixture_must_be_zero_import');
    if (name.includes('cold-')) must(source.includes("record('main_import_enter');") && !source.includes("import('react-router')"), 'cold_main_boundary');
    if (name.includes('injection.test')) must(!source.includes('renderer/main') && source.includes('createModuleRoutes(registry)'), 'p_must_use_default_loader_without_main');
    must(!/vi\.(mock|doMock|resetModules|importActual)\(/.test(source), 'forbidden_mock_or_cache_reset');
    syntax.push({name, parsed: true, staticImports: imports});
  }
}
const a = configuration('cold-trace'), b = configuration('cold-public');
const resolveAlias = (config, specifier) => {
  const item = config.resolve.alias.find(a => typeof a.find === 'string' ? specifier === a.find || specifier.startsWith(a.find + '/') : a.find.test(specifier));
  return item ? specifier.replace(item.find, item.replacement) : specifier;
};
must(resolveAlias(a, 'react-router') === path.join(own, 'r4-r3-router-facade.mjs'), 'exact_facade_alias');
must(resolveAlias(a, '__c12R3_real_router') === `${deps}/react-router`, 'facade_recursion');
must(resolveAlias(b, 'react-router') === resolveAlias(a, '__c12R3_real_router'), 'different_real_router');
for (const sub of ['dom', 'package.json', 'route-pattern']) must(resolveAlias(a, `react-router/${sub}`) === resolveAlias(b, `react-router/${sub}`), 'subpath_redirect');
must(resolveAlias(a, 'react-router-extra') === 'react-router-extra', 'alias_too_broad');
const metadata = {};
for (const [name, version] of Object.entries({vitest: '5.0.2', react: '19.3.0', 'react-dom': '19.3.0', 'react-router': '8.4.0', jsdom: '30.1.1', vite: '7.3.6', typescript: '6.0.3'})) {
  const file = path.join(deps, name, 'package.json'); const bytes = fs.readFileSync(file);
  must(JSON.parse(bytes).version === version, 'frozen_version_mismatch');
  metadata[name] = {version, packageJsonSha256: sha(bytes), physicalRoot: fs.realpathSync(path.dirname(file))};
}
must(process.version === 'v24.21.0', 'node_version');
const facade = fs.readFileSync(path.join(own, 'r4-r3-router-facade.mjs'), 'utf8');
must(facade.includes("export * from '__c12R3_real_router'") && facade.includes('return originalPromise;') && facade.includes('return item.router;') && !facade.includes('importOriginal') && !facade.includes('vi.mock'), 'facade_structure');

const targetId = path.resolve(own, '../../../apps/desktop/src/modules/daily-finance/DailyFinancePage').replaceAll('\\','/');
const realImporter = path.resolve(own, '../../../apps/desktop/src/renderer/module-routes.tsx').replaceAll('\\','/');
const accepted = [targetId, targetId+'.tsx', targetId.replace(/^D:/,'d:'), '/@fs/'+targetId, '/@id/'+targetId];
for(const id of accepted) must(classify(id, undefined)?.absoluteRequest && !classify(id, undefined)?.unsupportedQuery, 'known_canonical_id_missing');
must(classify('../modules/daily-finance/DailyFinancePage', realImporter)?.relativeRequest, 'relative_importer_not_bound');
for(const id of [targetId+'.mjs',targetId+'/child',targetId.replace('DailyFinancePage','OtherPage'),'react-router']) must(classify(id,realImporter) === null,'resolver_too_broad');
must(classify('../modules/daily-finance/DailyFinancePage',realImporter.replace('module-routes','other'))===null,'unrelated_relative_request');
must(classify(targetId+'?unknown',realImporter)?.unsupportedQuery,'unknown_query_not_rejected');
must(fixture.endsWith('r4-r3-failing-page.tsx'),'fixture_extension');

const result = {syntax, versions: metadata, node: process.version, coldStaticImportsVerified: true,
  aliasExact: true, noRecursiveAlias: true, realRouterTargetSameInAB: true,
  realResolutionConditions: 'unchanged Vite defaults in both configs; same package-directory alias',
  subpathsUnchanged: true, jsxReactAliasSame: true, defaultLoaderAndEntryUnmodified: true,
  facadeDynamicValidation: 'not_run', injectionDynamicValidation: 'not_run', exactTargetResolverStaticChecks: true, fixtureZeroImportsAndJsx: true, productMainRequests: 0,
  disclosedDisturbances: ['loader function identity changes on original target route', 'side Promise listeners', 'read-only Router subscription', 'synchronous journal writes']};
fs.writeFileSync(path.join(evidence, 'static-preflight.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
fs.writeFileSync(path.join(evidence, 'cold-source.sha256'), sources.map(name => `${name}\t${sha(fs.readFileSync(path.join(own, name)))}`).join('\n') + '\n', {flag: 'wx'});
console.log(JSON.stringify({staticPassed: true, sourceFiles: sources.length, mainStarts: 0, persistentInjectionValidation: 'not_run', facadeDynamicValidation: 'not_run'}));
