import { openSync, writeSync, fsyncSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
export function journal(name) {
  const phase = process.env.D16_PHASE;
  if (!['e1', 'e2', 'e3'].includes(phase) || !['server', 'worker'].includes(name)) throw Error('d16_journal_boundary');
  const file = path.join(own, phase, 'results', `${name}.journal.jsonl`);
  const fd = openSync(file, 'wx');
  const start = process.hrtime.bigint(); let seq = 0;
  return (stage, detail = {}) => {
    try {
      if (!/^[a-z_]+$/.test(stage)) throw Error('d16_stage');
      for (const [key, value] of Object.entries(detail)) {
        if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(key) || !(typeof value === 'boolean' ||
          typeof value === 'number' && Number.isFinite(value))) throw Error('d16_detail');
      }
      const bytes = Buffer.from(JSON.stringify({seq: ++seq, stage, elapsedMs: Number(process.hrtime.bigint()-start)/1e6,
        pid: process.pid, parentPid: process.ppid, ...detail})+'\n');
      for(let offset=0; offset<bytes.length;) offset+=writeSync(fd,bytes,offset,bytes.length-offset);
      fsyncSync(fd);
    } catch { process.stderr.write('d16_journal_write_failed\n'); process.exit(91); }
  };
}
