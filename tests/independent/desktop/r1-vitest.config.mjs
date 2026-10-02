import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/MarisOutboxR2/R2-20261001-155509/workspace/node_modules';
const phase = process.env.C12_R1_PHASE;
const phases = {
  'original-node': ['public-boundaries.test.ts'],
  'remaining-original': ['public-boundaries.test.ts'],
  'outbox-independent': ['r1-outbox.test.ts'],
  'main-independent': ['r1-main.test.ts'],
  'matrix-independent': ['r1-shell-boundaries.test.ts'],
};
if (!Object.hasOwn(phases, phase ?? '')) throw new Error('c12_r1_phase_required');
export default {
  root,
  cacheDir: path.join(root, 'evidence/r1/cache'),
  resolve: { alias: [
    { find: /^vitest$/, replacement: `${deps}/vitest/dist/index.js` },
    { find: /^zod$/, replacement: `${deps}/zod/index.js` },
    { find: /^electron$/, replacement: `${deps}/electron/index.js` },
  ] },
  test: {
    include: phases[phase], environment: 'node', pool: 'forks', maxWorkers: 1,
    fileParallelism: false, bail: 1, testTimeout: 5000,
    reporters: ['default', 'json'],
    outputFile: { json: path.join(root, `evidence/r1/${phase}/result.json`) },
  },
};
