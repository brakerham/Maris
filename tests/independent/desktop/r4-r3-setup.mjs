import { openSync, writeSync, fsyncSync, closeSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Native-only, before test-module initialization. No product or UI imports.
const own = path.dirname(fileURLToPath(import.meta.url));
const phase = process.env.C12_R4_R3_PHASE;
if (!['injection', 'cold-trace', 'cold-public'].includes(phase)) throw Error('c12_phase_boundary');
const journal = path.join(own, 'evidence', 'r4-r3', phase, 'worker.journal.jsonl');
if (process.env.C12_R4_R3_JOURNAL !== journal) throw Error('c12_journal_boundary');
const fd = openSync(journal, 'wx');
const started = process.hrtime.bigint();
let seq = 0;
const stages = new Set(['worker_start', 'journal_ready', 'hoisted_ready', 'body_enter',
  'virtual_dom_bridge_ready', 'act_enter', 'act_return', 'act_rejected',
  'main_import_enter', 'main_import_resolved', 'main_import_rejected', 'root_created',
  'facade_loaded', 'router_create_enter', 'router_created', 'router_create_rejected',
  'router_superseded', 'router_subscribed', 'router_state', 'loader_enter',
  'loader_resolved', 'loader_rejected', 'loader_aborted', 'fixture_evaluation_enter', 'p_call_enter', 'p_call_terminal',
  'dom_state', 'observation_finished', 'assertions_enter', 'assertions_finished',
  'root_unmount_enter', 'root_unmounted', 'observer_unsubscribed', 'dom_globals_restored',
  'body_rejected', 'body_finished', 'warning', 'worker_exit']);
const safeValues = new Set(['Error', 'TypeError', 'AssertionError', 'AbortError', 'other',
  'idle', 'loading', 'submitting', 'console_error', 'console_warn', 'jsdom',
  'virtual_console_error', 'virtual_console_warn', 'window_unhandled_rejection']);
function record(stage, detail = {}) {
  try {
    if (!stages.has(stage)) throw Error('c12_bad_stage');
    for (const [key, value] of Object.entries(detail)) {
      if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(key) || !(typeof value === 'boolean' ||
        typeof value === 'number' && Number.isFinite(value) || safeValues.has(value))) throw Error('c12_unsafe_detail');
    }
    const bytes = Buffer.from(JSON.stringify({seq: ++seq,
      elapsedMs: Number(process.hrtime.bigint() - started) / 1e6,
      stage, pid: process.pid, parentPid: process.ppid, ...detail}) + '\n');
    for (let offset = 0; offset < bytes.length;) offset += writeSync(fd, bytes, offset, bytes.length - offset);
    fsyncSync(fd);
  } catch {
    process.stderr.write('c12_journal_write_failed\n'); process.exit(91);
  }
}
Object.defineProperty(globalThis, '__c12R3Record', {value: record, configurable: true});
Object.defineProperty(globalThis, '__c12R3Trace', {value: {routers: [], active: null}, configurable: true});
Object.defineProperty(globalThis, '__c12R3FixtureHits', {value: 0, writable: true, configurable: true});
record('worker_start'); record('journal_ready');
process.once('exit', exitCode => { record('worker_exit', {exitCode}); closeSync(fd); });
