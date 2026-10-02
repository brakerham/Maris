import { expect, test, vi } from 'vitest';
import { compileRegistry } from '../../../../apps/desktop/src/modules/registry';
import { dailyFinanceContribution } from '../../../../apps/desktop/src/modules/daily-finance/contribution';
import { createModuleRoutes } from '../../../../apps/desktop/src/renderer/module-routes';
import { observe, save, waitBounded } from './observations';

const fault = vi.hoisted(() => ({ hits: 0, times: [] as number[] }));
vi.mock('../../../../apps/desktop/src/modules/daily-finance/DailyFinancePage', () => {
  fault.hits++; fault.times.push(Date.now());
  throw new Error('VIRTUAL_CHUNK_UNAVAILABLE');
});

test('D15-P2 | actual contribution route and default builtin loader terminal', async () => {
  const registry = compileRegistry([dailyFinanceContribution]);
  const route = createModuleRoutes(registry)[0]!;
  const started = Date.now();
  const timeline: unknown[] = [{ stage: 'loader_enter', elapsedMs: 0 }];
  // Product loader accepts no arguments and uses its real fixed builtin table.
  const promise = (route.loader as () => Promise<unknown>)();
  const result = observe(promise, (stage, detail) => timeline.push({ stage: `loader_${stage}`, elapsedMs: Date.now() - started, detail }));
  const bounded = await waitBounded(() => result.terminal !== 'pending', started);
  save('p2', { startedEpochMs: started, routeTarget: route.id === 'module_route:daily_finance_home',
    defaultBuiltinLoader: true, faultHits: fault.hits, faultElapsedMs: fault.times.map(time => time - started),
    result, bounded, timeline, uiStarted: false, routerStarted: false });
  expect(fault.hits).toBe(1);
});
