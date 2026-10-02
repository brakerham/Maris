import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(own, '../../../../..');
const external = 'C:/MarisLazyR5/R5-20261002-222300';
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const save = (name, value) => fs.writeFileSync(path.join(own, name), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
const check = (manifest, root, authorized = []) => {
  const out = { total: 0, matched: 0, authorizedChanged: [], changed: [], missing: [], invalid: [], manifestSha256: hash(manifest) };
  for (const line of fs.readFileSync(manifest, 'utf8').replace(/^\uFEFF/, '').trim().split(/\r?\n/)) {
    out.total++;
    const cells = line.split('\t');
    if (![2, 3].includes(cells.length) || !/^[a-f0-9]{64}$/.test(cells.at(-1))) { out.invalid.push(out.total); continue; }
    const relative = cells[0].replaceAll('\\', '/');
    const target = path.resolve(root, relative);
    if (!target.startsWith(path.resolve(root) + path.sep)) { out.invalid.push(out.total); continue; }
    if (!fs.existsSync(target)) out.missing.push(relative);
    else if (hash(target) === cells.at(-1)) out.matched++;
    else (authorized.includes(relative) ? out.authorizedChanged : out.changed).push(relative);
  }
  return out;
};
if (process.argv[2] === 'syntax') {
  const require = createRequire(import.meta.url);
  const ts = require(`${external}/workspace/node_modules/typescript/lib/typescript.js`);
  const result = ts.transpileModule(fs.readFileSync(path.join(own, 'bootstrap.test.tsx'), 'utf8'), {
    fileName: 'bootstrap.test.tsx', reportDiagnostics: true,
    compilerOptions: { target: ts.ScriptTarget.ESNext, module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX }
  });
  const codes = (result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).map(d => d.code);
  save('typescript-syntax.json', { kind: 'syntax_only_no_target_execution', version: ts.version, errorCodes: codes });
  console.log(JSON.stringify({ syntaxErrorCount: codes.length }));
  if (codes.length) process.exitCode = 1;
} else {
  const mode = process.argv[2];
  if (!['baseline', 'end-audit'].includes(mode)) throw new Error('d15_r1_audit_mode');
  const old = path.join(repo, 'docs/coordination/diagnostics/p4-d15');
  const baseline = JSON.parse(fs.readFileSync(path.join(old, 'baseline.json'), 'utf8').replace(/^\uFEFF/, ''));
  const inputs = check(path.join(repo, 'docs/coordination/snapshots/p4-d15-r1-start.sha256'), repo,
    ['docs/coordination/agents/technical-adviser.md']);
  const oldDelivery = check(path.join(old, 'delivery.sha256'), repo, ['docs/coordination/agents/technical-adviser.md']);
  const oldFrozen = check(path.join(old, 'probe-source.sha256'), old);
  const externalSource = check(`${external}/evidence/static/workspace-source.sha256`, `${external}/workspace`);
  const externalOut = check(`${external}/evidence/static/out-manifest-v4.tsv`, `${external}/workspace/apps/desktop/out/Maris-win32-x64`);
  const packages = baseline.packages.map(item => ({ name: item.package, version: item.version,
    matched: hash(`${external}/workspace/node_modules/${item.package}/package.json`) === item.packageSha256 }));
  const extraPackages = ['typescript', '@vitest/mocker'].map(name => {
    const file = `${external}/workspace/node_modules/${name}/package.json`;
    return { name, version: JSON.parse(fs.readFileSync(file, 'utf8')).version, sha256: hash(file) };
  });
  const nodeMatched = hash(`${external}/tools/node/node.exe`) === baseline.nodeSha256;
  const frozen = fs.existsSync(path.join(own, 'probe-source.sha256')) ? check(path.join(own, 'probe-source.sha256'), own) : null;
  const git = spawnSync('git', ['diff', '--cached', '--name-only'], { cwd: repo, encoding: 'utf8', windowsHide: true });
  const clean = value => !value.changed.length && !value.missing.length && !value.invalid.length;
  const passed = [inputs, oldDelivery, oldFrozen, externalSource, externalOut, ...(frozen ? [frozen] : [])].every(clean) &&
    packages.every(p => p.matched) && nodeMatched && git.status === 0 && !git.stdout.trim();
  const value = { passed, inputs, oldDelivery, oldFrozen, externalSource, externalOut, packages, extraPackages,
    nodeMatched, frozen, stagedCount: git.stdout.trim() ? git.stdout.trim().split(/\r?\n/).length : 0,
    gitReadExit: git.status, gitReadWarning: Boolean(git.stderr.trim()),
    scope: 'fixed manifests and package metadata; own role changes explicitly authorized; no full dependency graph claim' };
  save(`${mode}.json`, value);
  console.log(JSON.stringify({ passed, inputMatched: inputs.matched, authorizedChanged: inputs.authorizedChanged,
    oldDeliveryMatched: oldDelivery.matched, externalSourceMatched: externalSource.matched,
    externalOutMatched: externalOut.matched, frozenMatched: frozen?.matched, stagedCount: value.stagedCount }));
  if (!passed) process.exitCode = 1;
}
