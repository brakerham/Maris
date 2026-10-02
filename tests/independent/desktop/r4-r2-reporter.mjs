import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
// First JSON is safe at its source: actual runner states/counts, no Error/stack.
export default class SafeReporter {
  onInit() { this.started = Date.now(); }
  onTestRunEnd(modules, unhandledErrors) {
    const nodes = [];
    const visit = task => {
      if (task.type === 'test') nodes.push({name: task.name,
        status: task.result?.state === 'pass' ? 'passed' : task.result?.state === 'fail' ? 'failed' : 'not_run',
        durationMs: task.result?.duration ?? null, errorCount: task.result?.errors?.length ?? 0,
        errors: (task.result?.errors ?? []).map(error => ({
          kind: ['AssertionError', 'Error', 'TypeError'].includes(error.name) ? error.name : 'other',
          timeout: /timed out/i.test(error.message ?? '')}))});
      for (const child of task.tasks ?? []) visit(child);
    };
    for (const module of modules) visit(module.task);
    const result = {startTime: this.started, endTime: Date.now(),
      numTotalTests: nodes.length, numPassedTests: nodes.filter(n => n.status === 'passed').length,
      numFailedTests: nodes.filter(n => n.status === 'failed').length,
      numPendingTests: nodes.filter(n => n.status === 'not_run').length,
      moduleErrorCount: modules.reduce((n, m) => n + (m.task.result?.errors?.length ?? 0), 0),
      unhandledErrorCount: unhandledErrors.length, nodes, data: 'virtual_only',
      rawExceptionTextRecorded: false};
    const own = path.dirname(fileURLToPath(import.meta.url));
    const phase = process.env.C12_R4_R2_PHASE;
    writeFileSync(path.join(own, `evidence/r4-r2/${phase}/result.json`), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    process.stdout.write(JSON.stringify({stage: 'runner_result', total: nodes.length,
      passed: result.numPassedTests, failed: result.numFailedTests,
      unhandledErrors: result.unhandledErrorCount}) + '\n');
  }
}
