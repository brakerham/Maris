import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import ts from 'file:///C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/typescript/lib/typescript.js';
import { configuration } from './r6-env-config-factory.mjs';
import { classify, fixture } from './r6-env-resolver.mjs';
const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../..');
const evidence = path.join(own, 'evidence/r6-env');
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
const sha = value => createHash('sha256').update(value).digest('hex');
const must = (value, code) => { if (!value) throw Error(code); };
must(!fs.existsSync(path.join(evidence, 'cold-source.sha256')), 'r6_env_source_already_frozen');
const sources = fs.readdirSync(own).filter(name => name.startsWith('r6-env-') && fs.statSync(path.join(own, name)).isFile()).sort();
const syntax = [];
for (const name of sources) {
  const source = fs.readFileSync(path.join(own, name), 'utf8');
  if (name.endsWith('.mjs')) {
    const parsed = spawnSync(process.execPath, ['--check', path.join(own, name)], { shell: false, encoding: 'utf8' });
    must(parsed.status === 0, 'r6_env_mjs_syntax'); syntax.push({ name, parsed: true });
  }
  if (name.endsWith('.tsx')) {
    const result = ts.transpileModule(source, { fileName: name, compilerOptions: { jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext }, reportDiagnostics: true });
    must(!(result.diagnostics ?? []).some(item => item.category === ts.DiagnosticCategory.Error), 'r6_env_tsx_syntax');
    const ast = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const imports = ast.statements.filter(ts.isImportDeclaration).map(node => node.moduleSpecifier.text);
    if (name.includes('failing-page')) must(imports.length === 0 && !result.outputText.includes('import ') && source.includes("throw new Error('VIRTUAL_CHUNK_UNAVAILABLE')"), 'r6_env_zero_import_fixture');
    if (name.includes('cold.test')) {
      must(JSON.stringify(imports) === '["vitest"]', 'r6_env_preload_violation');
      must(!source.includes("await import('jsdom')") && source.includes("await import('react')") && source.includes('__r6EnvDom'), 'r6_env_segmented_imports');
      const runtimeImports = [];
      const visit = node => {
        if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) runtimeImports.push(node.arguments[0]?.text);
        ts.forEachChild(node, visit);
      };
      visit(ast);
      must(runtimeImports.filter(name => name === '../../../apps/desktop/src/renderer/main').length === 1, 'r6_env_main_budget');
      must(runtimeImports.every(name => ['react', '../../../apps/desktop/src/renderer/main'].includes(name)), 'r6_env_other_product_preload');
      must(source.includes("shell?.querySelector('.content [role=\"alert\"]')") && source.includes('const final = sample();'), 'r6_env_local_sample');
      must(source.indexOf('expect.soft(final.alertText)') < source.indexOf('let proof:'), 'r6_env_four_assertions_first');
      const definition = source.slice(source.indexOf('const faultSourceValid ='), source.indexOf("record('fault_source'"));
      must(!definition.includes('final.') && !definition.includes('publicTargetResult'), 'r6_env_circular_fault_source');
      must(source.includes("record('cleanup_enter'") && (source.match(/finally \{/g) ?? []).length >= 5, 'r6_env_nested_cleanup');
    }
    must(!/vi\.(mock|doMock|resetModules|importActual)\(/.test(source), 'r6_env_forbidden_mock');
    syntax.push({ name, parsed: true, staticImports: imports });
  }
}
const config = configuration({ staticOnly: true });
const alias = specifier => {
  const item = config.resolve.alias.find(item => typeof item.find === 'string' ? specifier === item.find || specifier.startsWith(item.find + '/') : item.find.test(specifier));
  return item ? specifier.replace(item.find, item.replacement) : specifier;
};
must(alias('react-router') === `${deps}/react-router` && alias('react-router/dom') === `${deps}/react-router/dom`, 'r6_env_real_router');
must(alias('react-router-extra') === 'react-router-extra' && alias('react/jsx-runtime') === `${deps}/react/jsx-runtime` && alias('react-dom/client') === `${deps}/react-dom/client`, 'r6_env_single_react');
must(config.test.environment === 'node' && config.test.pool === 'forks' && config.test.isolate && config.test.maxWorkers === 1 && config.test.testTimeout === 12000, 'r6_env_runner_settings');
const oldResolver = fs.readFileSync(path.join(own, 'r4-r3-resolver.mjs'), 'utf8');
const newResolver = fs.readFileSync(path.join(own, 'r6-env-resolver.mjs'), 'utf8');
const predicate = source => source.slice(source.indexOf('const normalize ='), source.indexOf('export function persistentImportResolver'));
must(predicate(oldResolver) === predicate(newResolver), 'r6_env_resolver_semantic_drift');
const oldFixture = fs.readFileSync(path.join(own, 'r4-r3-failing-page.tsx'), 'utf8');
const newFixture = fs.readFileSync(path.join(own, 'r6-env-failing-page.tsx'), 'utf8');
must(oldFixture.replaceAll('__c12R3', '__r6Env') === newFixture, 'r6_env_fixture_semantic_drift');
for (const name of sources.filter(name => /\.(mjs|tsx)$/.test(name) && !name.includes('verify'))) {
  const source = fs.readFileSync(path.join(own, name), 'utf8');
  must(!/(?:vi\.(?:mock|doMock|importActual|resetModules)|\.invalidate|\.revalidate|\.navigate|importOriginal)\s*\(/.test(source), 'r6_env_cache_or_loader_manipulation');
}
const target = path.resolve(root, 'apps/desktop/src/modules/daily-finance/DailyFinancePage').replaceAll('\\', '/');
const importer = path.resolve(root, 'apps/desktop/src/renderer/module-routes.tsx').replaceAll('\\', '/');
for (const id of [target, target + '.tsx', target.replace(/^D:/, 'd:'), '/@fs/' + target, '/@id/' + target]) must(classify(id)?.absoluteRequest && !classify(id)?.unsupportedQuery, 'r6_env_known_id');
must(classify('../modules/daily-finance/DailyFinancePage', importer)?.relativeRequest, 'r6_env_bound_relative');
must(classify('../modules/daily-finance/DailyFinancePage', importer.replace('module-routes', 'other')) === null, 'r6_env_wrong_importer');
for (const id of [target + '.mjs', target + '/child', 'react-router', target.replace('DailyFinancePage', 'OtherPage')]) must(classify(id, importer) === null, 'r6_env_mapping_too_broad');
must(classify(target + '?unknown', importer)?.unsupportedQuery && classify(target + '#unknown', importer)?.unsupportedQuery, 'r6_env_unknown_query');
must(fixture.endsWith('r6-env-failing-page.tsx'), 'r6_env_fixture_id');
const versions = {};
for (const [name, version] of Object.entries({ vitest: '5.0.2', vite: '7.3.6', react: '19.3.0', 'react-dom': '19.3.0', 'react-router': '8.4.0', jsdom: '30.1.1', typescript: '6.0.3' })) {
  const file = path.join(deps, name, 'package.json'), bytes = fs.readFileSync(file);
  must(JSON.parse(bytes).version === version, 'r6_env_version');
  versions[name] = { version, packageJsonSha256: sha(bytes), physicalRoot: fs.realpathSync(path.dirname(file)) };
}
must(process.version === 'v24.21.0', 'r6_env_node');
const names = ['apps/desktop/src/renderer/main.tsx', 'apps/desktop/src/renderer/module-routes.tsx', 'apps/desktop/src/shell/Shell.tsx',
  'apps/desktop/src/modules/daily-finance/contribution.ts', 'apps/desktop/src/modules/registry.ts', 'apps/desktop/src/shared/contracts.ts'];
const productFiles = names.map(name => ({ name, sha256: sha(fs.readFileSync(path.join(root, name))) }));
const main = fs.readFileSync(path.join(root, names[0]), 'utf8'), routes = fs.readFileSync(path.join(root, names[1]), 'utf8');
must(main.includes('compileRegistry([dailyFinanceContribution])') && main.includes('<StrictMode><DesktopApp registry={compiled} /></StrictMode>'), 'r6_env_main_contract');
must(routes.includes('loaders = builtinPageLoaders') && routes.includes('...createModuleRoutes(modules, loaders)') && routes.includes('await import("../modules/daily-finance/DailyFinancePage")'), 'r6_env_default_loader_contract');
const controller = fs.readFileSync(path.join(own, 'r6-env-run-once.ps1'), 'utf8');
must(controller.includes("'--configLoader','native'") && controller.includes('processDeadlineMs=75000') && controller.includes("$row.stage -eq 'body_enter'") && controller.includes("$row.stage -eq 'cleanup_enter'") && !controller.includes('priorPhase'), 'r6_env_stage_controller');
// Resolve and hash only; never load jsdom or a target during static verification.
const packagePath = path.join(deps, 'jsdom/package.json');
const packageBytes = fs.readFileSync(packagePath), metadata = JSON.parse(packageBytes);
const nativeRequire = createRequire(pathToFileURL(packagePath));
const resolvedApi = nativeRequire.resolve('./lib/api.js');
must(metadata.version === '30.1.1' && metadata.type === 'commonjs' && metadata.main === './lib/api.js', 'r6_env_native_package');
must(fs.realpathSync(resolvedApi) === fs.realpathSync(path.join(deps, 'jsdom/lib/api.js')), 'r6_env_native_api_path');
const nativeJsdom = { version: metadata.version, type: metadata.type, main: metadata.main,
  packageRealPath: fs.realpathSync(packagePath), apiRealPath: fs.realpathSync(resolvedApi),
  packageSha256: sha(packageBytes), apiSha256: sha(fs.readFileSync(resolvedApi)), loadedDuringStaticCheck: false };
const setup = fs.readFileSync(path.join(own, 'r6-env-setup.mjs'), 'utf8');
must(setup.includes('createRequire(packageUrl)') && setup.includes('const api = nativeRequire(resolvedApi)') && setup.indexOf("record('journal_ready')") < setup.indexOf("record('native_jsdom_enter')"), 'r6_env_native_entry');
must(!setup.includes('new JSDOM') && !setup.includes('await import(') && !setup.includes('Object.freeze('), 'r6_env_no_preload_or_api_wrap');
// Cold body and fault predicate remain byte-equivalent after identifier translation.
const translate = source => source.replaceAll('r5-public','r6-env').replaceAll('R5-PUBLIC','R6-ENV').replaceAll('__r5Public','__r6Env').replaceAll('r5_public','r6_env').replaceAll('R5_PUBLIC','R6_ENV');
const previousTest = translate(fs.readFileSync(path.join(own, 'r5-public-cold.test.tsx'), 'utf8'));
const currentTest = fs.readFileSync(path.join(own, 'r6-env-cold.test.tsx'), 'utf8');
must(previousTest.slice(previousTest.indexOf("test('R6-ENV-UI-02-COLD")) === currentTest.slice(currentTest.indexOf("test('R6-ENV-UI-02-COLD")), 'r6_env_body_changed');
const result = { syntax, versions, nativeJsdom, coldBodyUnchanged: true, node: process.version, productFiles, defaultLoaderAndEntryUnmodified: true,
  fixtureZeroImportsAndJsx: true, noCacheOrSuccessSubstitute: true, resolverPredicateIdentical: true,
  realRouterDirect: true, reactSinglePhysicalRoot: true, phaseBudgets: { initialization: 60000, body: 10000, cleanup: 2000, overall: 75000, observation: 5000, vitestOuter: 12000 },
  nativeConfigLoader: true, configTemporaryFiles: 'none', productMainRequests: 0,
  disclosedDisturbances: ['synchronous safe journal writes', 'config and resolver stage hooks', 'virtual bridge and denied network boundaries', 'all console arguments inspected in memory', 'bounded condition polling without Router telemetry'] };
fs.writeFileSync(path.join(evidence, 'static-preflight.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
fs.writeFileSync(path.join(evidence, 'cold-source.sha256'), sources.map(name => `${name}\t${sha(fs.readFileSync(path.join(own, name)))}`).join('\n') + '\n', { flag: 'wx' });
console.log(JSON.stringify({ staticPassed: true, frozenSources: sources.length, mainStarts: 0, next: 'one independent public cold B' }));
