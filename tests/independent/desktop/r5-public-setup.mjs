import { openSync, writeSync, fsyncSync, closeSync, readFileSync, realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../..');
const evidence = path.join(own, 'evidence/r5-public');
const journal = path.join(evidence, 'cold/worker.journal.jsonl');
if (process.env.R5_PUBLIC_JOURNAL !== journal) throw Error('r5_public_journal_boundary');
const fd = openSync(journal, 'wx');
const started = process.hrtime.bigint();
let seq = 0;
const evaluations = [];
const safeValues = new Set(['Error', 'TypeError', 'AssertionError', 'other']);
function record(stage, detail = {}) {
  try {
    if (!/^[a-z][a-z0-9_]*$/.test(stage)) throw Error('r5_public_bad_stage');
    for (const [key, value] of Object.entries(detail)) {
      if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(key) || !(typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value) || safeValues.has(value))) throw Error('r5_public_unsafe_detail');
    }
    const event = { seq: ++seq, elapsedMs: Number(process.hrtime.bigint() - started) / 1e6, stage, pid: process.pid, parentPid: process.ppid, ...detail };
    const bytes = Buffer.from(JSON.stringify(event) + '\n');
    for (let offset = 0; offset < bytes.length;) offset += writeSync(fd, bytes, offset, bytes.length - offset);
    fsyncSync(fd);
    if (stage === 'fixture_evaluation_enter') evaluations.push(event);
  } catch { process.stderr.write('r5_public_journal_write_failed\n'); process.exit(91); }
}
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function sourceProof() {
  const frozen = readFileSync(path.join(evidence, 'cold-source.sha256'), 'utf8').trimEnd().split('\n').map(line => line.split('\t'));
  const preflight = JSON.parse(readFileSync(path.join(evidence, 'static-preflight.json'), 'utf8'));
  const mappingPath = path.join(evidence, 'cold/resolver.journal.jsonl');
  let maps = [];
  try {
    const text = readFileSync(mappingPath, 'utf8');
    maps = text.split('\n').slice(0, -1).filter(Boolean).map(line => JSON.parse(line));
  } catch { /* Missing mapping remains invalid, never use prior P. */ }
  const exactMappingValid = maps.length > 0 && maps.every(event => event.stage === 'target_module_mapping' && event.targetOrdinal === 1 && event.fixtureOrdinal === 1 && !event.unsupportedQuery && (event.absoluteRequest || event.relativeRequest && event.importerBound));
  const mappingIdentityValid = maps.length > 0 && maps.every(event => event.pid === process.ppid && event.parentPid === Number(process.env.R5_PUBLIC_CONTROLLER_PID));
  const actualWorkerEvaluationValid = evaluations.length > 0 && evaluations.every(event => event.pid === process.pid && event.parentPid === process.ppid && event.fixtureOrdinal === 1 && event.count > 0);
  const frozenSourcesMatched = frozen.every(([name, digest]) => sha(readFileSync(path.join(own, name))) === digest);
  const productFilesMatched = preflight.productFiles.every(({ name, sha256 }) => sha(readFileSync(path.join(root, name))) === sha256);
  const repositoryRootBound = realpathSync(root).replaceAll('\\', '/') === 'D:/CodeX_gap/wife-system';
  return { exactMappingValid, mappingIdentityValid, actualWorkerEvaluationValid, frozenSourcesMatched,
    fixedPersistentFixtureValid: frozenSourcesMatched && preflight.fixtureZeroImportsAndJsx,
    defaultLoaderContractValid: productFilesMatched && preflight.defaultLoaderAndEntryUnmodified,
    noCacheOrSuccessSubstitute: frozenSourcesMatched && preflight.noCacheOrSuccessSubstitute,
    repositoryRootBound, mappingCount: maps.length, evaluationEvents: evaluations.length };
}
Object.defineProperty(globalThis, '__r5PublicRecord', { value: record, configurable: true });
Object.defineProperty(globalThis, '__r5PublicFixtureHits', { value: 0, writable: true, configurable: true });
Object.defineProperty(globalThis, '__r5PublicSourceProof', { value: sourceProof, configurable: true });
record('worker_start');
record('journal_ready');
process.once('exit', exitCode => { record('worker_exit', { exitCode }); closeSync(fd); });
