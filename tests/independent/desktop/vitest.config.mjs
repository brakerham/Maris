import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ownRoot = path.dirname(fileURLToPath(import.meta.url));
const cleanModules = 'C:/MarisE5Final/E5-PKG-FINAL-20260929-1732/workspace/node_modules';

// Use the accepted, installed toolchain read-only; all runner output belongs to C12.
export default {
  root: ownRoot,
  cacheDir: path.join(ownRoot, '.cache'),
  resolve: { alias: [
    { find: /^vitest$/, replacement: `${cleanModules}/vitest/dist/index.js` },
    { find: /^zod$/, replacement: `${cleanModules}/zod/index.js` },
  ] },
  test: {
    include: ['public-boundaries.test.ts'],
    environment: 'node',
    pool: 'forks',
    maxWorkers: 1,
    fileParallelism: false,
    bail: 1,
    testTimeout: 5000,
    reporters: ['default', 'json'],
    outputFile: { json: path.join(ownRoot, 'evidence/public-boundaries.json') },
  },
};
