import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
export default {
  root: own, cacheDir: path.join(own, '..', 'temp', 'attempt-0'),
  esbuild: { jsx: 'automatic' },
  resolve: { alias: [
    { find: /^vitest$/, replacement: `${deps}/vitest/dist/index.js` },
    { find: 'zod', replacement: `${deps}/zod` },
    { find: 'react-dom', replacement: `${deps}/react-dom` },
    { find: 'react-router', replacement: `${deps}/react-router` },
    { find: 'react', replacement: `${deps}/react` },
    { find: 'jsdom', replacement: `${deps}/jsdom/lib/api.js` }
  ] },
  test: { include: ['bootstrap.test.tsx'], setupFiles: [path.join(own, 'setup.mjs')],
    sequence: { setupFiles: 'list' }, environment: 'node', pool: 'forks', maxWorkers: 1,
    fileParallelism: false, isolate: true, bail: 1, testTimeout: 10000,
    hookTimeout: 10000, reporters: ['default'] }
};
