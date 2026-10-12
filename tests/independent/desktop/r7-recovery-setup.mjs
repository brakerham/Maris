import { openSync, writeSync, fsyncSync, closeSync, readFileSync, realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../..');
const evidence = path.join(own, 'evidence/r7-recovery');
const journal = path.join(evidence, 'recovery/worker.journal.jsonl');
if (process.env.R7_RECOVERY_JOURNAL !== journal) throw Error('r7_recovery_journal_boundary');
const fd = openSync(journal, 'wx');
const started = process.hrtime.bigint();
let seq = 0;
const mapping = JSON.parse(readFileSync(path.join(evidence, 'assertion-map.json'), 'utf8'));
const ids = new Set([...mapping.assertions.map(row => row.id), ...mapping.operationIds]);
const enums = new Set(['unknown', 'dark', 'on', '#/broken', '#/healthy', 'eq', 'lte', 'positive_integer',
  'gate', 'legacy', 'selftest', 'Error', 'TypeError', 'AssertionError', 'other',
  'ERR_REQUIRE_ESM', 'ERR_REQUIRE_ASYNC_MODULE', 'MODULE_NOT_FOUND', 'ERR_MODULE_NOT_FOUND']);
const keys = new Set(['id','group','operation','assertion','operator','kind','expected','actual','errorKind',
  'identityMatched','referencesValid','code','exitCode','passed','differentSaved','booleanSaved','rejected','noRawField',
  'ordinal','loads','healthyLoads','denied','initialBaseline','scenarios','settingsWrites','rawConsoleCalls','jsdomErrors',
  'bodyMs','unmounted','closed','listenersRemoved','restored','restoreFailed','activeAfterUnmount','rescueUnsubscribe',
  'subscribe','unsubscribe','consoleLeak','incomplete','cleanupMs']);
function record(stage, detail = {}) {
  // Validate before opening a write path; schema rejection never serializes input.
  if (!/^[a-z][a-z0-9_]*$/.test(stage)) throw Error('r7_record_schema');
  for (const [key, value] of Object.entries(detail)) {
    if (!keys.has(key)) throw Error('r7_record_schema');
    const scalar = typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value);
    if (key === 'id' ? !ids.has(value) : !(scalar || enums.has(value))) throw Error('r7_record_schema');
  }
  try {
    const event = { seq: ++seq, elapsedMs: Number(process.hrtime.bigint() - started) / 1e6, stage, pid: process.pid, parentPid: process.ppid, ...detail };
    const bytes = Buffer.from(JSON.stringify(event) + '\n');
    for (let offset = 0; offset < bytes.length;) offset += writeSync(fd, bytes, offset, bytes.length - offset);
    fsyncSync(fd);
  } catch { process.stderr.write('r7_recovery_journal_write_failed\n'); process.exit(91); }
}
Object.defineProperty(globalThis, '__r7RecoveryReadJournal', { value: () => readFileSync(journal, 'utf8'), configurable: true });
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
Object.defineProperty(globalThis, '__r7RecoveryRecord', { value: record, configurable: true });
Object.defineProperty(globalThis, '__r7RecoveryFixtureHits', { value: 0, writable: true, configurable: true });
record('worker_start');
record('journal_ready');
process.once('exit', exitCode => { record('worker_exit', { exitCode }); closeSync(fd); });

// Native environment entry only. No DOM, React, Router or product evaluation here.
const packagePath = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/jsdom/package.json';
const packageUrl = pathToFileURL(packagePath);
const nativeRequire = createRequire(packageUrl);
const expectedApi = path.join(path.dirname(packagePath), 'lib/api.js');
const nativeIdentity = JSON.parse(readFileSync(path.join(evidence, 'start-audit.json'), 'utf8')).nativeJsdom;
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
  if (!identityMatched) throw Error('r7_recovery_jsdom_identity_mismatch');
  record('native_jsdom_enter');
  const api = nativeRequire(resolvedApi);
  const referencesValid = typeof api.JSDOM === 'function' && typeof api.VirtualConsole === 'function';
  if (!referencesValid) throw TypeError('r7_recovery_jsdom_api_invalid');
  Object.defineProperty(globalThis, '__r7RecoveryDom', {
    value: { JSDOM: api.JSDOM, VirtualConsole: api.VirtualConsole }, configurable: true
  });
  record('native_jsdom_resolved', { referencesValid });
} catch (error) {
  const kind = ['Error', 'TypeError'].includes(error?.name) ? error.name : 'other';
  const code = ['ERR_REQUIRE_ESM', 'ERR_REQUIRE_ASYNC_MODULE', 'MODULE_NOT_FOUND', 'ERR_MODULE_NOT_FOUND'].includes(error?.code) ? error.code : 'other';
  record('native_jsdom_rejected', { kind, code });
  throw Error('r7_recovery_native_jsdom_failed');
}
