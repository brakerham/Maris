import path from 'node:path';
import { fileURLToPath } from 'node:url';

const own = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
const probe = process.env.P4_D15_PROBE;
if (!['p1', 'p2', 'p3'].includes(probe)) throw new Error('d15_probe_required');
export default {
  root: own,
  cacheDir: path.join(own, 'temp', probe),
  esbuild: { jsx: 'automatic' },
  resolve: { alias: [
    { find: /^vitest$/, replacement: `${deps}/vitest/dist/index.js` },
    { find: 'zod', replacement: `${deps}/zod` },
    { find: 'react-dom', replacement: `${deps}/react-dom` },
    { find: 'react-router', replacement: `${deps}/react-router` },
    { find: 'react', replacement: `${deps}/react` },
    { find: 'jsdom', replacement: `${deps}/jsdom/lib/api.js` }
  ] },
  test: {
    include: [`${probe}.test.ts${probe === 'p3' ? 'x' : ''}`],
    environment: 'node', pool: 'forks', maxWorkers: 1,
    fileParallelism: false, isolate: true, bail: 1,
    testTimeout: 10000, hookTimeout: 10000,
    reporters: ['default']
  }
};
