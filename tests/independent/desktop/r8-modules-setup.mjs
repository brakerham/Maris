import { openSync, writeSync, fsyncSync, closeSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const journal = path.join(own, 'evidence/r8-modules/modules/worker.journal.jsonl');
const fd = openSync(journal, 'wx');
const started = performance.now(); let seq = 0;
const keys = new Set(['id','operator','expected','actual','kind','operation','passed','errorKind','durationMs','count','bodyMs','cleanupMs','exitCode','rejected','noRawField','stage']);
const enums = new Set(['unknown','eq','lte','positive','gate','selftest','Error','TypeError','AssertionError','other','dark','on','off','system','#/alpha','#/beta','#/settings','online','offline','body','cleanup']);
function record(event, details = {}) {
  if (!/^[a-z][a-z0-9_]*$/.test(event)) throw Error('r8_record_schema');
  for (const [key,value] of Object.entries(details)) {
    if (!keys.has(key)) throw Error('r8_record_schema');
    if (key === 'id' || key === 'operation') { if (typeof value !== 'string' || !/^(R8|SELF)[A-Z0-9._-]*$/.test(value)) throw Error('r8_record_schema'); }
    else if (!(typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value) || enums.has(value))) throw Error('r8_record_schema');
  }
  const bytes = Buffer.from(JSON.stringify({ seq: ++seq, event, elapsedMs: performance.now()-started, pid: process.pid, parentPid: process.ppid, details })+'\n');
  for (let offset=0; offset<bytes.length;) offset+=writeSync(fd,bytes,offset,bytes.length-offset);
  fsyncSync(fd);
}
globalThis.__r8Record = record;
record('worker_start');
process.once('exit', exitCode => { record('worker_exit',{exitCode}); closeSync(fd); });
record('assert_enter',{id:'SELF.DIFFERENT',kind:'selftest',operator:'eq',expected:9});
record('assert_fail',{id:'SELF.DIFFERENT',kind:'selftest',operator:'eq',expected:9,actual:7});
record('assert_enter',{id:'SELF.BOOLEAN',kind:'selftest',operator:'eq',expected:true});
record('assert_pass',{id:'SELF.BOOLEAN',kind:'selftest',operator:'eq',expected:true,actual:true});
let rejected=false;
try { record('forbidden',{raw:'R8_FORBIDDEN_PRIVATE_TEXT'}); } catch { rejected=true; }
const raw=readFileSync(journal,'utf8');
const passed=rejected && raw.includes('"expected":9,"actual":7') && raw.includes('"expected":true,"actual":true') && !raw.includes('R8_FORBIDDEN_PRIVATE_TEXT');
record('recorder_selftest',{passed,rejected,noRawField:!raw.includes('R8_FORBIDDEN_PRIVATE_TEXT')});
if (!passed) throw Error('r8_recorder_selftest');
record('native_jsdom_enter');
const req=createRequire('C:/MarisModulesR6/R6-20261013-002100/workspace/node_modules/jsdom/package.json');
const api=req('./lib/api.js');
if(typeof api.JSDOM!=='function'||typeof api.VirtualConsole!=='function') throw Error('r8_jsdom_api');
globalThis.__r8Dom=api;
record('native_jsdom_resolved');
