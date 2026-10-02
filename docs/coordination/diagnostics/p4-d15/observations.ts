import { writeFileSync } from 'node:fs';

export function safeError(value: unknown) {
  const error = value as { name?: unknown; message?: unknown; cause?: { message?: unknown } } | null;
  const name = error?.name;
  const message = typeof error?.message === 'string' ? error.message : '';
  const causeMessage = typeof error?.cause?.message === 'string' ? error.cause.message : '';
  return {
    kind: ['Error', 'TypeError', 'AssertionError', 'AbortError'].includes(String(name)) ? String(name) : 'other',
    safeModuleCode: message === 'desktop_module_unavailable',
    safeRenderCode: message === 'desktop_render_unavailable',
    virtualFault: message === 'VIRTUAL_CHUNK_UNAVAILABLE',
    mockWrapper: message.startsWith('[vitest] There was an error when mocking a module.'),
    virtualCause: causeMessage === 'VIRTUAL_CHUNK_UNAVAILABLE'
  };
}

export function save(probe: string, value: Record<string, unknown>) {
  const receipt = { probe, data: 'virtual_only', workerPid: process.pid,
    workerParentPid: process.ppid, ...value };
  writeFileSync(process.env.P4_D15_RESULT_FILE!, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(receipt));
}

// Captures the original Promise's settlement. Handlers record only safe fields;
// neither the source Promise nor its resolution/rejection is replaced.
export function observe(promise: Promise<unknown>, record: (stage: string, detail?: unknown) => void) {
  const status: { terminal: 'pending' | 'resolve' | 'reject'; error?: ReturnType<typeof safeError> } = { terminal: 'pending' };
  void promise.then(() => { status.terminal = 'resolve'; record('resolve'); }, error => {
    status.terminal = 'reject'; status.error = safeError(error); record('reject', status.error);
  });
  return status;
}

export async function waitBounded(done: () => boolean, started: number) {
  const deadline = started + 5000;
  while (!done()) {
    const remaining = deadline - Date.now();
    if (remaining <= 0) break;
    await new Promise(resolve => setTimeout(resolve, Math.min(20, remaining)));
  }
  return { observedMs: Date.now() - started, deadlineMs: 5000, terminalWithinDeadline: done() };
}
