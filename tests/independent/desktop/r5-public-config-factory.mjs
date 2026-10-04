import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openSync, writeSync, fsyncSync, closeSync } from 'node:fs';
import { persistentImportResolver } from './r5-public-resolver.mjs';
const own = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
export function configuration({ staticOnly = false } = {}) {
  let seq = 0;
  const started = performance.now();
  const record = stage => {
    if (staticOnly) return;
    const fd = openSync(path.join(own, 'evidence/r5-public/cold/config.journal.jsonl'), 'a');
    try {
      const bytes = Buffer.from(JSON.stringify({ seq: ++seq, stage, elapsedMs: performance.now() - started, pid: process.pid, parentPid: process.ppid }) + '\n');
      for (let offset = 0; offset < bytes.length;) offset += writeSync(fd, bytes, offset, bytes.length - offset);
      fsyncSync(fd);
    } finally { closeSync(fd); }
  };
  record('config_evaluation_enter');
  const config = {
    root: own, cacheDir: path.join(own, 'evidence/r5-public/cache/cold'),
    plugins: [persistentImportResolver('cold'), {
      name: 'r5-public-config-stages',
      configResolved() { record('config_resolved'); },
      configureServer() { record('server_configured'); }
    }],
    esbuild: { jsx: 'automatic' },
    resolve: { alias: [
      { find: /^vitest$/, replacement: `${deps}/vitest/dist/index.js` },
      { find: 'react-router', replacement: `${deps}/react-router` },
      { find: 'react-dom', replacement: `${deps}/react-dom` },
      { find: 'react', replacement: `${deps}/react` },
      { find: 'zod', replacement: `${deps}/zod` },
      { find: 'jsdom', replacement: `${deps}/jsdom/lib/api.js` }
    ] },
    test: {
      include: ['r5-public-cold.test.tsx'], setupFiles: [path.join(own, 'r5-public-setup.mjs')],
      sequence: { setupFiles: 'list' }, environment: 'node', pool: 'forks', maxWorkers: 1,
      fileParallelism: false, isolate: true, bail: 1, testTimeout: 12000, hookTimeout: 12000,
      reporters: [path.join(own, 'r5-public-reporter.mjs')]
    }
  };
  record('config_object_ready');
  return config;
}
