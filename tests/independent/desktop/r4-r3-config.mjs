import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { persistentImportResolver } from './r4-r3-resolver.mjs';
const own = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
export function configuration(phase) {
  if (!['injection', 'cold-trace', 'cold-public'].includes(phase)) throw Error('c12_r3_phase_required');
  return {root: own, cacheDir: path.join(own, 'evidence/r4-r3/cache', phase),
    plugins: [persistentImportResolver(phase)], esbuild: {jsx: 'automatic'},
    resolve: {alias: [
      {find: /^vitest$/, replacement: `${deps}/vitest/dist/index.js`},
      {find: /^react-router$/, replacement: phase === 'cold-trace' ? path.join(own, 'r4-r3-router-facade.mjs') : `${deps}/react-router`},
      {find: /^__c12R3_real_router$/, replacement: `${deps}/react-router`},
      {find: 'react-router', replacement: `${deps}/react-router`},
      {find: 'react-dom', replacement: `${deps}/react-dom`},
      {find: 'react', replacement: `${deps}/react`},
      {find: 'zod', replacement: `${deps}/zod`},
      {find: 'jsdom', replacement: `${deps}/jsdom/lib/api.js`}
    ]}, test: {include: [`r4-r3-${phase}.test.tsx`], setupFiles: [path.join(own, 'r4-r3-setup.mjs')],
      sequence: {setupFiles: 'list'}, environment: 'node', pool: 'forks', maxWorkers: 1, fileParallelism: false,
      isolate: true, bail: 1, testTimeout: 10000, hookTimeout: 10000,
      reporters: [path.join(own, 'r4-r3-reporter.mjs')]}};
}
