import { expect, test, vi } from 'vitest';
import { observe, save, waitBounded } from './observations';

const fault = vi.hoisted(() => ({ hits: 0, times: [] as number[] }));
vi.mock('../../../../apps/desktop/src/modules/daily-finance/DailyFinancePage', () => {
  fault.hits++; fault.times.push(Date.now());
  throw new Error('VIRTUAL_CHUNK_UNAVAILABLE');
});

test('D15-P1 | direct original page import terminal without Router or UI', async () => {
  const started = Date.now();
  const timeline: unknown[] = [{ stage: 'import_enter', elapsedMs: 0 }];
  const promise = import('../../../../apps/desktop/src/modules/daily-finance/DailyFinancePage');
  const result = observe(promise, (stage, detail) => timeline.push({ stage: `import_${stage}`, elapsedMs: Date.now() - started, detail }));
  const bounded = await waitBounded(() => result.terminal !== 'pending', started);
  save('p1', { startedEpochMs: started, faultHits: fault.hits,
    faultElapsedMs: fault.times.map(time => time - started), result, bounded, timeline,
    uiStarted: false, routerStarted: false });
  expect(fault.hits).toBe(1);
});
