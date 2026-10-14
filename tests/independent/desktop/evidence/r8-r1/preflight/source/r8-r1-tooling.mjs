// Scalar bookkeeping only. Shared by setup selftests and the formal scenarios.
export class DuplicateAssertionError extends Error {}
export class GateError extends Error {}
export function claim(used, assertionId, nodeId, record, stage, selftest = false) {
  if (used.has(assertionId)) {
    record('tool_error', {kind:selftest?'selftest':'gate',nodeId,attemptedAssertionId:assertionId,
      errorCode:'duplicate_assertion_id',stage,...(selftest?{caseId:'SELF.DUPLICATE',expectedFailure:true}:{})});
    throw new DuplicateAssertionError('duplicate_assertion_id');
  }
  used.add(assertionId);
}
export function classify(error) {
  return error instanceof DuplicateAssertionError?'tool':error instanceof GateError?'comparison':'unknown';
}
export function nodePassed(bodyPassed, error, cleanupPassed) {
  return bodyPassed && error === null && cleanupPassed;
}
