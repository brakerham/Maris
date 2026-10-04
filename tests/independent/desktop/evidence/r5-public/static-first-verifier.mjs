import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import ts from 'file:///C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/typescript/lib/typescript.js';
import { configuration } from './r5-public-config-factory.mjs';
import { classify, fixture } from './r5-public-resolver.mjs';
const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../..');
const evidence = path.join(own, 'evidence/r5-public');
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
const sha = value => createHash('sha256').update(value).digest('hex');
const must = (value, code) => { if (!value) throw Error(code); };
must(!fs.existsSync(path.join(evidence, 'cold-source.sha256')), 'r5_public_source_already_frozen');
const sources = fs.readdirSync(own).filter(name => name.startsWith('r5-public-') && fs.statSync(path.join(own, name)).isFile()).sort();
const syntax = [];
for (const name of sources) {
  const source = fs.readFileSync(path.join(own, name), 'utf8');
  if (name.endsWith('.mjs')) {
    const parsed = spawnSync(process.execPath, ['--check', path.join(own, name)], { shell: false, encoding: 'utf8' });
    must(parsed.status === 0, 'r5_public_mjs_syntax'); syntax.push({ name, parsed: true });
  }
  if (name.endsWith('.tsx')) {
    const result = ts.transpileModule(source, { fileName: name, compilerOptions: { jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext }, reportDiagnostics: true });
    must(!(result.diagnostics ?? []).some(item => item.category === ts.DiagnosticCategory.Error), 'r5_public_tsx_syntax');
    const ast = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const imports = ast.statements.filter(ts.isImportDeclaration).map(node => node.moduleSpecifier.text);
    if (name.includes('failing-page')) must(imports.length === 0 && !result.outputText.includes('import ') && source.includes("throw new Error('VIRTUAL_CHUNK_UNAVAILABLE')"), 'r5_public_zero_import_fixture');
    if (name.includes('cold.test')) {
      must(JSON.stringify(imports) === '["vitest"]', 'r5_public_preload_violation');
      must(source.includes("await import('jsdom')") && source.includes("await import('react')"), 'r5_public_segmented_imports');
      must((source.match(/import\('\.\.\/\.\.\/\.\.\/apps\/desktop\/src\/renderer\/main'\)/g) ?? []).length === 1, 'r5_public_main_budget');
      must(source.includes("shell?.querySelector('.content [role=\"alert\"]')") && source.includes('const final = sample();'), 'r5_public_local_sample');
      must(source.indexOf('expect.soft(final.alertText)') < source.indexOf('let proof:'), 'r5_public_four_assertions_first');
      const definition = source.slice(source.indexOf('const faultSourceValid ='), source.indexOf("record('fault_source'"));
      must(!definition.includes('final.') && !definition.includes('publicTargetResult'), 'r5_public_circular_fault_source');
      must(source.includes("record('cleanup_enter'") && (source.match(/finally \{/g) ?? []).length >= 5, 'r5_public_nested_cleanup');
    }
    must(!/vi\.(mock|doMock|resetModules|importActual)\(/.test(source), 'r5_public_forbidden_mock');
    syntax.push({ name, parsed: true, staticImports: imports });
  }
}
const config = configuration({ staticOnly: true });
const alias = specifier => {
  const item = config.resolve.alias.find(item => typeof item.find === 'string' ? specifier === item.find || specifier.startsWith(item.find + '/') : item.find.test(specifier));
  return item ? specifier.replace(item.find, item.replacement) : specifier;
};
must(alias('react-router') === `${deps}/react-router` && alias('react-router/dom') === `${deps}/react-router/dom`, 'r5_public_real_router');
must(alias('react-router-extra') === 'react-router-extra' && alias('react/jsx-runtime') === `${deps}/react/jsx-runtime` && alias('react-dom/client') === `${deps}/react-dom/client`, 'r5_public_single_react');
must(config.test.environment === 'node' && config.test.pool === 'forks' && config.test.isolate && config.test.maxWorkers === 1 && config.test.testTimeout === 12000, 'r5_public_runner_settings');
const oldResolver = fs.readFileSync(path.join(own, 'r4-r3-resolver.mjs'), 'utf8');
const newResolver = fs.readFileSync(path.join(own, 'r5-public-resolver.mjs'), 'utf8');
const predicate = source => source.slice(source.indexOf('const normalize ='), source.indexOf('export function persistentImportResolver'));
must(predicate(oldResolver) === predicate(newResolver), 'r5_public_resolver_semantic_drift');
const oldFixture = fs.readFileSync(path.join(own, 'r4-r3-failing-page.tsx'), 'utf8');
const newFixture = fs.readFileSync(path.join(own, 'r5-public-failing-page.tsx'), 'utf8');
must(oldFixture.replaceAll('__c12R3', '__r5Public') === newFixture, 'r5_public_fixture_semantic_drift');
for (const name of sources.filter(name => /\.(mjs|tsx)$/.test(name) && !name.includes('verify'))) {
  const source = fs.readFileSync(path.join(own, name), 'utf8');
  must(!/(?:vi\.(?:mock|doMock|importActual|resetModules)|\.invalidate|\.revalidate|\.navigate|importOriginal)\s*\(/.test(source), 'r5_public_cache_or_loader_manipulation');
}
const target = path.resolve(root, 'apps/desktop/src/modules/daily-finance/DailyFinancePage').replaceAll('\\', '/');
const importer = path.resolve(root, 'apps/desktop/src/renderer/module-routes.tsx').replaceAll('\\', '/');
for (const id of [target, target + '.tsx', target.replace(/^D:/, 'd:'), '/@fs/' + target, '/@id/' + target]) must(classify(id)?.absoluteRequest && !classify(id)?.unsupportedQuery, 'r5_public_known_id');
must(classify('../modules/daily-finance/DailyFinancePage', importer)?.relativeRequest, 'r5_public_bound_relative');
must(classify('../modules/daily-finance/DailyFinancePage', importer.replace('module-routes', 'other')) === null, 'r5_public_wrong_importer');
for (const id of [target + '.mjs', target + '/child', 'react-router', target.replace('DailyFinancePage', 'OtherPage')]) must(classify(id, importer) === null, 'r5_public_mapping_too_broad');
must(classify(target + '?unknown', importer)?.unsupportedQuery && classify(target + '#unknown', importer)?.unsupportedQuery, 'r5_public_unknown_query');
must(fixture.endsWith('r5-public-failing-page.tsx'), 'r5_public_fixture_id');
const versions = {};
for (const [name, version] of Object.entries({ vitest: '5.0.2', vite: '7.3.6', react: '19.3.0', 'react-dom': '19.3.0', 'react-router': '8.4.0', jsdom: '30.1.1', typescript: '6.0.3' })) {
  const file = path.join(deps, name, 'package.json'), bytes = fs.readFileSync(file);
  must(JSON.parse(bytes).version === version, 'r5_public_version');
  versions[name] = { version, packageJsonSha256: sha(bytes), physicalRoot: fs.realpathSync(path.dirname(file)) };
}
must(process.version === 'v24.21.0', 'r5_public_node');
const names = ['apps/desktop/src/renderer/main.tsx', 'apps/desktop/src/renderer/module-routes.tsx', 'apps/desktop/src/shell/Shell.tsx',
  'apps/desktop/src/modules/daily-finance/contribution.ts', 'apps/desktop/src/modules/registry.ts', 'apps/desktop/src/shared/contracts.ts'];
const productFiles = names.map(name => ({ name, sha256: sha(fs.readFileSync(path.join(root, name))) }));
const main = fs.readFileSync(path.join(root, names[0]), 'utf8'), routes = fs.readFileSync(path.join(root, names[1]), 'utf8');
must(main.includes('compileRegistry([dailyFinanceContribution])') && main.includes('<StrictMode><DesktopApp registry={compiled} /></StrictMode>'), 'r5_public_main_contract');
must(routes.includes('loaders = builtinPageLoaders') && routes.includes('...createModuleRoutes(modules, loaders)') && routes.includes('await import("../modules/daily-finance/DailyFinancePage")'), 'r5_public_default_loader_contract');
const controller = fs.readFileSync(path.join(own, 'r5-public-run-once.ps1'), 'utf8');
must(controller.includes("'--configLoader','native'") && controller.includes('processDeadlineMs=30000') && controller.includes("$row.stage -eq 'body_enter'") && controller.includes("$row.stage -eq 'cleanup_enter'") && !controller.includes('priorPhase'), 'r5_public_stage_controller');
const result = { syntax, versions, node: process.version, productFiles, defaultLoaderAndEntryUnmodified: true,
  fixtureZeroImportsAndJsx: true, noCacheOrSuccessSubstitute: true, resolverPredicateIdentical: true,
  realRouterDirect: true, reactSinglePhysicalRoot: true, phaseBudgets: { initialization: 15000, body: 10000, cleanup: 2000, overall: 30000, observation: 5000, vitestOuter: 12000 },
  nativeConfigLoader: true, configTemporaryFiles: 'none', productMainRequests: 0,
  disclosedDisturbances: ['synchronous safe journal writes', 'config and resolver stage hooks', 'virtual bridge and denied network boundaries', 'all console arguments inspected in memory', 'bounded condition polling without Router telemetry'] };
fs.writeFileSync(path.join(evidence, 'static-preflight.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
fs.writeFileSync(path.join(evidence, 'cold-source.sha256'), sources.map(name => `${name}\t${sha(fs.readFileSync(path.join(own, name)))}`).join('\n') + '\n', { flag: 'wx' });
console.log(JSON.stringify({ staticPassed: true, frozenSources: sources.length, mainStarts: 0, next: 'one independent public cold B' }));
