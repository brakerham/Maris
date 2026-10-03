import { expect, test } from 'vitest';

test('R4-R3-INJECTION-PERSISTENT | default route loader two concurrent and one subsequent imports reject', async () => {
  const record = (globalThis as any).__c12R3Record;
  record('body_enter');
  try {
    const {dailyFinanceContribution} = await import('../../../apps/desktop/src/modules/daily-finance/contribution');
    const {compileRegistry} = await import('../../../apps/desktop/src/modules/registry');
    const {createModuleRoutes} = await import('../../../apps/desktop/src/renderer/module-routes');
    const registry = compileRegistry([dailyFinanceContribution]);
    // No custom loaders argument: the original built-in dynamic import is used.
    const routes = createModuleRoutes(registry);
    const route = routes.find(route => route.id === 'module_route:daily_finance_home')!;
    const loader = route.loader as (...args: unknown[]) => Promise<unknown>;
    const call = async (callSeq: number) => {
      record('p_call_enter', {callSeq, defaultLoader: true});
      try {
        await Reflect.apply(loader, route, []);
        record('p_call_terminal', {callSeq, rejected: false, safeModuleCode: false});
        return {rejected: false, safeModuleCode: false};
      } catch (error: any) {
        const safeModuleCode = error?.message === 'desktop_module_unavailable';
        record('p_call_terminal', {callSeq, rejected: true, safeModuleCode,
          virtualRawError: error?.message === 'VIRTUAL_CHUNK_UNAVAILABLE'});
        return {rejected: true, safeModuleCode};
      }
    };
    const first = await Promise.all([call(1), call(2)]);
    const subsequent = await call(3);
    record('assertions_enter');
    for (const terminal of [...first, subsequent]) {
      expect.soft(terminal.rejected).toBe(true); expect.soft(terminal.safeModuleCode).toBe(true);
    }
    expect.soft((globalThis as any).__c12R3FixtureHits).toBeGreaterThan(0);
    record('assertions_finished');
  } catch (error: any) {
    record('body_rejected', {kind: ['Error', 'AssertionError', 'TypeError'].includes(error?.name) ? error.name : 'other'}); throw error;
  } finally {record('body_finished');}
});
