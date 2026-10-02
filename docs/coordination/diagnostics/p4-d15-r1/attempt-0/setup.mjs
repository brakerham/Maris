import { openSync, writeSync, fsyncSync, closeSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Native-only setup; no React, Router, observation helper, or product import.
const own = path.dirname(fileURLToPath(import.meta.url));
const journal = path.resolve(process.env.P4_D15_R1_JOURNAL || '');
if (journal !== path.join(own, 'results', 'worker.journal.jsonl')) throw new Error('d15_r1_journal_boundary');
const stages = new Set(['worker_start', 'journal_ready', 'hoisted_ready', 'factory_enter',
  'actual_import_enter', 'actual_import_resolved', 'actual_import_rejected', 'body_enter',
  'virtual_dom_bridge_ready', 'router_preflight_enter', 'router_preflight_resolved',
  'router_preflight_rejected', 'act_enter', 'main_import_enter', 'main_import_resolved',
  'main_import_rejected', 'act_return', 'act_rejected', 'root_created', 'root_unmount_enter',
  'root_unmounted', 'root_unmount_rejected', 'router_created', 'observer_unsubscribed',
  'dom_globals_restored', 'body_rejected', 'body_finished', 'virtual_factory_throw',
  'warning', 'worker_exit']);
const safeStrings = new Set(['Error', 'TypeError', 'AssertionError', 'AbortError', 'other',
  'console_error', 'console_warn', 'jsdom', 'virtual_console_error', 'virtual_console_warn',
  'window_unhandled_rejection']);
const fd = openSync(journal, 'wx');
const started = process.hrtime.bigint();
let seq = 0;
const record = (stage, detail = {}) => {
  try {
    if (!stages.has(stage)) throw new Error('d15_r1_bad_stage');
    for (const [key, value] of Object.entries(detail)) {
      if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(key) || !(typeof value === 'boolean' ||
        (typeof value === 'number' && Number.isFinite(value)) || safeStrings.has(value))) {
        throw new Error('d15_r1_unsafe_detail');
      }
    }
    const row = { seq: ++seq, elapsedMs: Number(process.hrtime.bigint() - started) / 1e6,
      stage, pid: process.pid, parentPid: process.ppid, ...detail };
    const data = Buffer.from(JSON.stringify(row) + '\n');
    let offset = 0;
    while (offset < data.length) offset += writeSync(fd, data, offset, data.length - offset);
    fsyncSync(fd);
  } catch {
    process.stderr.write('d15_r1_journal_write_failed\n');
    process.exit(91);
    throw new Error('d15_r1_journal_write_failed');
  }
};
record('worker_start');
Object.defineProperty(globalThis, '__d15R1Record', { value: record, configurable: true });
record('journal_ready');
process.once('exit', code => { record('worker_exit', { exitCode: code }); closeSync(fd); });
