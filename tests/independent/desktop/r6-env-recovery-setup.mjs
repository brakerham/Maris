import { openSync, writeSync, fsyncSync, closeSync, readFileSync, realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../..');
const evidence = path.join(own, 'evidence/r6-env');
const journal = path.join(evidence, 'recovery/worker.journal.jsonl');
if (process.env.R6_ENV_JOURNAL !== journal) throw Error('r6_env_journal_boundary');
const fd = openSync(journal, 'wx');
const started = process.hrtime.bigint();
let seq = 0;
const evaluations = [];
const safeValues = new Set(['Error', 'TypeError', 'AssertionError', 'ERR_REQUIRE_ESM', 'ERR_REQUIRE_ASYNC_MODULE', 'MODULE_NOT_FOUND', 'ERR_MODULE_NOT_FOUND', 'other']);
function record(stage, detail = {}) {
  try {
    if (!/^[a-z][a-z0-9_]*$/.test(stage)) throw Error('r6_env_bad_stage');
    for (const [key, value] of Object.entries(detail)) {
      if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(key) || !(typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value) || safeValues.has(value))) throw Error('r6_env_unsafe_detail');
    }
    const event = { seq: ++seq, elapsedMs: Number(process.hrtime.bigint() - started) / 1e6, stage, pid: process.pid, parentPid: process.ppid, ...detail };
    const bytes = Buffer.from(JSON.stringify(event) + '\n');
    for (let offset = 0; offset < bytes.length;) offset += writeSync(fd, bytes, offset, bytes.length - offset);
    fsyncSync(fd);
    if (stage === 'fixture_evaluation_enter') evaluations.push(event);
  } catch { process.stderr.write('r6_env_journal_write_failed\n'); process.exit(91); }
}
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
Object.defineProperty(globalThis, '__r6RecoveryRecord', { value: record, configurable: true });
Object.defineProperty(globalThis, '__r6RecoveryFixtureHits', { value: 0, writable: true, configurable: true });
record('worker_start');
record('journal_ready');
process.once('exit', exitCode => { record('worker_exit', { exitCode }); closeSync(fd); });

// Native environment entry only. No DOM, React, Router or product evaluation here.
const packagePath = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/jsdom/package.json';
const packageUrl = pathToFileURL(packagePath);
const nativeRequire = createRequire(packageUrl);
const expectedApi = path.join(path.dirname(packagePath), 'lib/api.js');
const nativeIdentity = JSON.parse(readFileSync(path.join(evidence, 'static-preflight.json'), 'utf8')).nativeJsdom;
try {
  const packageBytes = readFileSync(packagePath);
  const metadata = JSON.parse(packageBytes);
  const resolvedApi = nativeRequire.resolve('./lib/api.js');
  const physicalApi = realpathSync(resolvedApi);
  const identityMatched = metadata.version === '30.1.1' && metadata.type === 'commonjs' && metadata.main === './lib/api.js'
    && realpathSync(packagePath) === nativeIdentity.packageRealPath
    && physicalApi === realpathSync(expectedApi) && physicalApi === nativeIdentity.apiRealPath
    && sha(packageBytes) === nativeIdentity.packageSha256 && sha(readFileSync(physicalApi)) === nativeIdentity.apiSha256;
  record('native_jsdom_identity', { identityMatched });
  if (!identityMatched) throw Error('r6_env_jsdom_identity_mismatch');
  record('native_jsdom_enter');
  const api = nativeRequire(resolvedApi);
  const referencesValid = typeof api.JSDOM === 'function' && typeof api.VirtualConsole === 'function';
  if (!referencesValid) throw TypeError('r6_env_jsdom_api_invalid');
  Object.defineProperty(globalThis, '__r6RecoveryDom', {
    value: { JSDOM: api.JSDOM, VirtualConsole: api.VirtualConsole }, configurable: true
  });
  record('native_jsdom_resolved', { referencesValid });
} catch (error) {
  const kind = ['Error', 'TypeError'].includes(error?.name) ? error.name : 'other';
  const code = ['ERR_REQUIRE_ESM', 'ERR_REQUIRE_ASYNC_MODULE', 'MODULE_NOT_FOUND', 'ERR_MODULE_NOT_FOUND'].includes(error?.code) ? error.code : 'other';
  record('native_jsdom_rejected', { kind, code });
  throw Error('r6_env_native_jsdom_failed');
}
