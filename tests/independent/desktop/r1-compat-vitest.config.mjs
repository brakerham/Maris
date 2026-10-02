import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
export default {
  root: 'C:/MarisOutboxR2/R2-20261001-155509/workspace/apps/desktop',
  cacheDir: path.join(own, 'evidence/r1/compat-cache'),
  test: {
    include: ['tests/unit/supervisor-outbox.test.ts', 'tests/unit/outbox-retention.test.ts'],
    environment: 'node', maxWorkers: 1, fileParallelism: false, bail: 1,
    reporters: ['default', 'json'],
    outputFile: { json: path.join(own, 'evidence/r1/executor-compat/result.json') },
  },
};
