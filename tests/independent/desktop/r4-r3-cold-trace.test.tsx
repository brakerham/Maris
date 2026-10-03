import { expect, test, vi } from 'vitest';
import { JSDOM, VirtualConsole } from 'jsdom';
import { act } from 'react';

// No Router, module-routes, contribution, or page preload. main builds its
// actual contribution/registry. This virtual Host summary was statically bound.
test('R4-R3-UI-02-COLD-TRACE | cold actual main, persistent real ESM import fault and four assertions', async () => {
  const record = (globalThis as any).__c12R3Record;
  record('body_enter');
  const traceEnabled = true;
  const trace = (globalThis as any).__c12R3Trace;
  const calls = {runtime: 0, modules: 0, subscribe: 0, unsubscribe: 0, activeSubscriptions: 0, settingsWrites: 0};
  const originals = new Map(['window', 'document', 'location', 'IS_REACT_ACT_ENVIRONMENT'].map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  const safeWarning = (source: string, value: unknown) => {
    const text = String(value);
    record('warning', {source, safeModuleCode: text.includes('desktop_module_unavailable'),
      safeRenderCode: text.includes('desktop_render_unavailable'), virtualFailure: text.includes('VIRTUAL_CHUNK_UNAVAILABLE')});
  };
  const vc = new VirtualConsole();
  vc.on('jsdomError', (e: any) => safeWarning('jsdom', e.type));
  vc.on('error', e => safeWarning('virtual_console_error', e));
  vc.on('warn', e => safeWarning('virtual_console_warn', e));
  const errorSpy = vi.spyOn(console, 'error').mockImplementation((...values) => safeWarning('console_error', values[0]));
  const warnSpy = vi.spyOn(console, 'warn').mockImplementation((...values) => safeWarning('console_warn', values[0]));
  const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {url: 'http://127.0.0.1/', virtualConsole: vc});
  vi.stubGlobal('window', dom.window); vi.stubGlobal('document', dom.window.document);
  vi.stubGlobal('location', dom.window.location); vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  const unhandled = (event: any) => safeWarning('window_unhandled_rejection', event.reason);
  dom.window.addEventListener('unhandledrejection', unhandled);
  Object.defineProperty(dom.window, 'maris', {value: {
    runtime: {getSnapshot: async () => { calls.runtime++; return {state: 'online', mode: 'managed', authenticated: true, errorCode: null}; },
      subscribe: () => { calls.subscribe++; calls.activeSubscriptions++; return () => { calls.unsubscribe++; calls.activeSubscriptions--; }; }},
    modules: {list: async () => { calls.modules++; return [{module_id: 'daily_finance', version: '1.0.0', enabled: true,
      profile_ids: ['daily_finance.assistant@1'], api_prefixes: ['/api/v1/finance'], settings_schema_version: 1}]; }},
    settings: {update: async () => {calls.settingsWrites++; return {ok: true}; }}
  }});
  record('virtual_dom_bridge_ready', {emptyHash: dom.window.location.hash === '', traceEnabled});
  let entry: typeof import('../../../apps/desktop/src/renderer/main') | undefined;
  let lastDom = '';
  const sample = () => {
    const alert = dom.window.document.querySelector('[role="alert"]');
    const active = traceEnabled ? trace.active : null;
    const state = {fixtureHits: (globalThis as any).__c12R3FixtureHits, alertShown: Boolean(alert), alertTextSafe: Boolean(alert?.textContent?.includes('页面暂时无法打开')),
      shellPresent: Boolean(dom.window.document.querySelector('main.shell')),
      navigationPresent: Boolean(dom.window.document.querySelector('nav[aria-label="模块导航"]')),
      agentPanelPresent: Boolean(dom.window.document.querySelector('aside[aria-label="统一 Agent 面板"]')),
      dailyHash: dom.window.location.hash === '#/daily', traceEnabled,
      routerSeq: active?.seq ?? 0, activeTargetError: Boolean(active?.last?.active && active?.last?.targetError && active?.last?.targetMatch)};
    const signature = JSON.stringify(state);
    if (signature !== lastDom) { record('dom_state', state); lastDom = signature; }
    return state;
  };
  try {
    record('act_enter');
    try {
      await act(async () => {
        record('main_import_enter');
        const originalImport = import('../../../apps/desktop/src/renderer/main');
        originalImport.then(() => record('main_import_resolved'), () => record('main_import_rejected'));
        entry = await originalImport;
        record('root_created', {rootIsObject: typeof entry.desktopRoot === 'object'});
      });
      record('act_return');
    } catch { record('act_rejected'); throw Error('c12_main_or_act_rejected'); }
    const observeStart = performance.now(); const deadline = observeStart + 5000;
    let state = sample();
    while (!(state.fixtureHits > 0 && state.alertTextSafe) && performance.now() < deadline) {
      const remaining = deadline - performance.now();
      if (remaining <= 0) break;
      await act(async () => { await new Promise(resolve => setTimeout(resolve, Math.min(20, remaining))); });
      state = sample();
    }
    record('observation_finished', {...state, observationMs: performance.now() - observeStart});
    record('assertions_enter');
    expect((globalThis as any).__c12R3FixtureHits, 'real ESM fixture must actually evaluate').toBeGreaterThan(0);
    const doc = dom.window.document;
    // Soft only ensures all four original independent requirements are checked;
    // any one failure still fails this single case.
    expect.soft(doc.querySelector('[role="alert"]')?.textContent).toContain('页面暂时无法打开');
    expect.soft(doc.querySelector('main.shell'), 'Shell must remain').not.toBeNull();
    expect.soft(doc.querySelector('nav[aria-label="模块导航"]')).not.toBeNull();
    expect.soft(doc.querySelector('aside[aria-label="统一 Agent 面板"]')).not.toBeNull();
    if (traceEnabled) {
      const active = trace.active;
      expect.soft(Boolean(active?.last?.targetMatch && active?.last?.targetError && active?.last?.safeModuleCode && active?.last?.active)).toBe(true);
      expect.soft(active?.last?.initialized).toBe(true);
      expect.soft(active?.last?.navigation).toBe('idle');
      expect.soft(Boolean(active?.attempts.some((attempt: any) => attempt.terminal === 'rejected' && attempt.safeModuleCode && !attempt.signal?.aborted))).toBe(true);
    }
    record('assertions_finished');
  } catch (error: any) {
    record('body_rejected', {kind: ['Error', 'AssertionError', 'TypeError'].includes(error?.name) ? error.name : 'other'}); throw error;
  } finally {
    if (entry) {
      record('root_unmount_enter');
      await act(async () => {entry!.desktopRoot.unmount();});
      record('root_unmounted');
    }
    for (const item of trace.routers) {
      if (item.unsubscribe) {item.unsubscribe(); item.unsubscribe = null; record('observer_unsubscribed', {routerSeq: item.seq});}
      for (const remove of item.abortCleanup) remove(); item.abortCleanup.length = 0;
    }
    const rootEmpty = dom.window.document.getElementById('root')?.childElementCount === 0;
    dom.window.removeEventListener('unhandledrejection', unhandled); dom.window.close();
    vi.unstubAllGlobals(); errorSpy.mockRestore(); warnSpy.mockRestore();
    const globalsRestored = [...originals].every(([key, old]) => {
      const current = Object.getOwnPropertyDescriptor(globalThis, key);
      return old ? current?.value === old.value && current?.get === old.get && current?.set === old.set : current === undefined;
    });
    record('dom_globals_restored', {rootEmpty, globalsRestored, domClosed: true, rootUnmounted: Boolean(entry),
      runtimeCalls: calls.runtime, moduleCalls: calls.modules, subscriptions: calls.subscribe,
      unsubscribe: calls.unsubscribe, activeBridgeSubscriptions: calls.activeSubscriptions, settingsWrites: calls.settingsWrites});
    expect.soft(rootEmpty).toBe(true); expect.soft(globalsRestored).toBe(true); expect.soft(calls.activeSubscriptions).toBe(0);
    record('body_finished');
  }
});
