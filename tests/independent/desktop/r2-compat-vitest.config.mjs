import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
export default {
  root: 'C:/MarisRegistryR3/R3-20261002-111556/workspace/apps/desktop',
  cacheDir: path.join(own, 'evidence/r2/compat-cache'),
  test: { include: ['tests/unit/registry.test.ts'], environment: 'node', maxWorkers: 1,
    bail: 1, reporters: ['default','json'],
    outputFile: { json: path.join(own, 'evidence/r2/executor-compat/result.json') } },
};
