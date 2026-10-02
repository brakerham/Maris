import { test, vi } from 'vitest';
import { JSDOM, VirtualConsole } from 'jsdom';
import { act } from 'react';
import { dailyFinanceContribution } from '../../../../../apps/desktop/src/modules/daily-finance/contribution';

const observation = vi.hoisted(() => {
  const record = (globalThis as any).__d15R1Record;
  if (typeof record !== 'function') throw new Error('d15_r1_setup_missing');
  record('hoisted_ready');
  const safe = (value: any) => ({
    kind: ['Error', 'TypeError', 'AssertionError', 'AbortError'].includes(value?.name) ? value.name : 'other',
    safeModuleCode: value?.message === 'desktop_module_unavailable',
    safeRenderCode: value?.message === 'desktop_render_unavailable',
    virtualFault: value?.message === 'VIRTUAL_CHUNK_UNAVAILABLE',
    mockWrapper: typeof value?.message === 'string' && value.message.startsWith('[vitest] There was an error when mocking a module.'),
    virtualCause: value?.cause?.message === 'VIRTUAL_CHUNK_UNAVAILABLE'
  });
  return { record, safe, faultHits: 0, unsubscribers: [] as (() => void)[] };
});

vi.mock('../../../../../apps/desktop/src/modules/daily-finance/DailyFinancePage', () => {
  observation.record('virtual_factory_throw', { count: ++observation.faultHits });
  throw new Error('VIRTUAL_CHUNK_UNAVAILABLE');
});
vi.mock('react-router', async importOriginal => {
  observation.record('factory_enter');
  observation.record('actual_import_enter');
  let actual: typeof import('react-router');
  try {
    actual = await importOriginal<typeof import('react-router')>();
    observation.record('actual_import_resolved', { createHashRouterIsFunction: typeof actual.createHashRouter === 'function' });
  } catch (error) {
    observation.record('actual_import_rejected', observation.safe(error));
    throw error;
  }
  return { ...actual, createHashRouter: (...args: Parameters<typeof actual.createHashRouter>) => {
    // Same arguments, route/errorElement objects, and actual returned Router.
    const router = Reflect.apply(actual.createHashRouter, actual, args);
    observation.record('router_created');
    observation.unsubscribers.push(router.subscribe(() => {}));
    return router;
  } };
});

test('D15-R1 | persisted real Router bootstrap and separate main/act terminal', async () => {
  const { record, safe } = observation;
  record('body_enter');
  const vc = new VirtualConsole();
  const warning = (source: string, value: unknown) => record('warning', { source, ...safe(value) });
  vc.on('jsdomError', value => warning('jsdom', value));
  vc.on('error', value => warning('virtual_console_error', value));
  vc.on('warn', value => warning('virtual_console_warn', value));
  const errorSpy = vi.spyOn(console, 'error').mockImplementation((...values) => warning('console_error', values[0]));
  const warnSpy = vi.spyOn(console, 'warn').mockImplementation((...values) => warning('console_warn', values[0]));
  const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: 'http://127.0.0.1/', virtualConsole: vc });
  const savedGlobals = new Map(['window', 'document', 'location', 'IS_REACT_ACT_ENVIRONMENT'].map(name => [name, Object.getOwnPropertyDescriptor(globalThis, name)]));
  vi.stubGlobal('window', dom.window); vi.stubGlobal('document', dom.window.document);
  vi.stubGlobal('location', dom.window.location); vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  const unhandled = (event: any) => warning('window_unhandled_rejection', event.reason);
  dom.window.addEventListener('unhandledrejection', unhandled);
  const calls = { subscribe: 0, unsubscribe: 0, active: 0, settings: 0 };
  const ui = dailyFinanceContribution;
  const host = { module_id: ui.moduleId, version: ui.version, enabled: true,
    profile_ids: [ui.agentPanel.profileId], api_prefixes: [...ui.expectedApiPrefixes], settings_schema_version: 1 };
  Object.defineProperty(dom.window, 'maris', { value: {
    runtime: { getSnapshot: async () => ({ state: 'online', mode: 'managed', authenticated: true, errorCode: null }),
      subscribe: () => { calls.subscribe++; calls.active++; return () => { calls.unsubscribe++; calls.active--; }; } },
    modules: { list: async () => [host] },
    settings: { update: async () => { calls.settings++; return { ok: true }; } }
  } });
  record('virtual_dom_bridge_ready');
  let entry: typeof import('../../../../../apps/desktop/src/renderer/main') | undefined;
  try {
    // Explicit observation prerequisite. This imports the same mocked specifier;
    // only its real export resolution is tested before requesting real main.
    record('router_preflight_enter');
    try { await import('react-router'); record('router_preflight_resolved'); }
    catch (error) { record('router_preflight_rejected', safe(error)); throw error; }
    record('act_enter');
    try {
      await act(async () => {
        record('main_import_enter');
        const promise = import('../../../../../apps/desktop/src/renderer/main');
        // Side listener returns no replacement Promise to act's callback.
        void promise.then(value => {
          entry = value;
          record('main_import_resolved');
          record('root_created', { rootIsObject: typeof value.desktopRoot === 'object' });
        }, error => { record('main_import_rejected', safe(error)); });
        entry = await promise;
      });
      record('act_return');
    } catch (error) { record('act_rejected', safe(error)); throw error; }
  } catch (error) { record('body_rejected', safe(error)); throw error; }
  finally {
    if (entry) {
      record('root_unmount_enter');
      try { await act(async () => { entry!.desktopRoot.unmount(); }); record('root_unmounted'); }
      catch (error) { record('root_unmount_rejected', safe(error)); throw error; }
    }
    for (const unsubscribe of observation.unsubscribers) { unsubscribe(); record('observer_unsubscribed'); }
    dom.window.removeEventListener('unhandledrejection', unhandled);
    const rootEmpty = dom.window.document.getElementById('root')?.childElementCount === 0;
    dom.window.close(); vi.unstubAllGlobals(); errorSpy.mockRestore(); warnSpy.mockRestore();
    const globalsRestored = [...savedGlobals].every(([name, descriptor]) => {
      const current = Object.getOwnPropertyDescriptor(globalThis, name);
      return descriptor ? current?.value === descriptor.value && current?.get === descriptor.get : current === undefined;
    });
    record('dom_globals_restored', { rootEmpty, globalsRestored, domClosed: true,
      bridgeSubscriptions: calls.subscribe, bridgeUnsubscribe: calls.unsubscribe,
      activeBridgeSubscriptions: calls.active, settingsWrites: calls.settings });
    record('body_finished');
  }
});
