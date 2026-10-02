import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const deps = 'C:/MarisRegistryR3/R3-20261002-111556/workspace/node_modules';
const phase = process.env.C12_R2_PHASE;
const files = {
  'original-registry': ['r1-shell-boundaries.test.ts'],
  'adjacent-original': ['r1-shell-boundaries.test.ts'],
  'registry-independent': ['r2-registry.test.ts'],
  'remaining-independent': ['r2-remaining.test.ts'],
};
if (!Object.hasOwn(files, phase ?? '')) throw new Error('c12_r2_phase_required');
export default {
  root: own, cacheDir: path.join(own, 'evidence/r2/cache'),
  resolve: { alias: [
    { find: /^vitest$/, replacement: `${deps}/vitest/dist/index.js` },
    { find: /^zod$/, replacement: `${deps}/zod/index.js` },
    { find: /^electron$/, replacement: `${deps}/electron/index.js` },
  ] },
  test: { include: files[phase], environment: 'node', pool: 'forks', maxWorkers: 1,
    fileParallelism: false, bail: 1, testTimeout: 5000, reporters: ['default','json'],
    outputFile: { json: path.join(own, `evidence/r2/${phase}/result.json`) } },
};
