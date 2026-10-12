import { writeFileSync, readFileSync } from 'node:fs';
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
    const phase = 'recovery';
    let events = [], journalReadable = false;
    try {
      const raw = readFileSync(path.join(own, `evidence/r7-recovery/${phase}/worker.journal.jsonl`), 'utf8');
      if (!raw.endsWith('\n')) throw Error('r7_incomplete_journal');
      events = raw.trimEnd().split('\n').map(line => JSON.parse(line));
      journalReadable = true;
    } catch { journalReadable = false; }
    const formalFailures = events.filter(row => row.stage === 'assert_fail' && row.kind === 'gate' && row.group !== 6);
    result.firstFormalFailure = formalFailures[0] ?? null;
    result.cleanupFailures = events.filter(row => row.stage === 'assert_fail' && row.kind === 'gate' && row.group === 6);
    result.operationFailures = events.filter(row => row.stage === 'operation_rejected');
    result.legacyComparisons = events.filter(row => ['assert_pass','assert_fail'].includes(row.stage) && row.kind === 'legacy');
    result.groupsEntered = events.filter(row => row.stage === 'recovery_scenario_enter').map(row => row.ordinal);
    result.groupsPassed = events.filter(row => row.stage === 'recovery_scenario_passed').map(row => row.ordinal);
    result.recorderSelftest = events.find(row => row.stage === 'recorder_selftest_result') ?? null;
    const entered = events.filter(row => row.stage === 'assert_enter');
    const terminals = events.filter(row => ['assert_pass','assert_fail'].includes(row.stage));
    result.assertionRecords = { entered: entered.length, terminal: terminals.length,
      complete: journalReadable && entered.every(row => terminals.filter(end => end.assertion === row.assertion && end.id === row.id).length === 1) && entered.length === terminals.length };
    result.journalReadable = journalReadable;
    writeFileSync(path.join(own, `evidence/r7-recovery/${phase}/result.json`), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
    process.stdout.write(JSON.stringify({stage: 'runner_result', total: nodes.length,
      passed: result.numPassedTests, failed: result.numFailedTests,
      unhandledErrors: result.unhandledErrorCount}) + '\n');
  }
}
