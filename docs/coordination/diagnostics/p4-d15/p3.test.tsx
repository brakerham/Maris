import { expect, test, vi } from 'vitest';
import { JSDOM, VirtualConsole } from 'jsdom';
import { act } from 'react';
import { dailyFinanceContribution } from '../../../../apps/desktop/src/modules/daily-finance/contribution';
import { observe, safeError, save } from './observations';

const observations = vi.hoisted(() => ({
  started: 0, faultHits: 0, faultTimes: [] as number[], routers: [] as any[],
  loaders: [] as any[], timeline: [] as any[], subscriptions: 0, unsubscribe: 0,
  activeSubscriptions: 0, record: undefined as undefined | ((stage: string, detail?: unknown) => void)
}));
vi.mock('../../../../apps/desktop/src/modules/daily-finance/DailyFinancePage', () => {
  observations.faultHits++; observations.faultTimes.push(Date.now());
  observations.record?.('factory_throw', { count: observations.faultHits });
  throw new Error('VIRTUAL_CHUNK_UNAVAILABLE');
});

vi.mock('react-router', async importOriginal => {
  const actual = await importOriginal<typeof import('react-router')>();
  return { ...actual, createHashRouter: (...args: Parameters<typeof actual.createHashRouter>) => {
    const routerOrdinal = observations.routers.length;
    const forwardLoaders = (routes: any[]) => {
      for (const route of routes) {
        if (route.id === 'module_route:daily_finance_home' && typeof route.loader === 'function') {
          const original = route.loader;
          // Dedicated permitted loader observation: same route objects, arguments,
          // this, return value and original Promise; no await/catch substitution.
          route.loader = function (this: unknown, ...loaderArgs: unknown[]) {
            observations.record?.('loader_enter', { routerOrdinal });
            const promise = Reflect.apply(original, this, loaderArgs);
            const sample: any = { routerOrdinal, returnIsThenable: typeof promise?.then === 'function', originalPromiseReturned: true };
            observations.loaders.push(sample);
            sample.result = observe(promise, (stage, detail) => observations.record?.(`loader_${stage}`, { routerOrdinal, detail }));
            return promise;
          };
        }
        if (route.children) forwardLoaders(route.children);
      }
    };
    forwardLoaders(args[0]);
    const router = Reflect.apply(actual.createHashRouter, actual, args);
    const summarize = (state: typeof router.state) => {
      const errors = state.errors ? Object.values(state.errors) : [];
      return {
        initialized: state.initialized, navigation: state.navigation.state,
        currentTargetMatched: state.matches.some(match => match.route.id === 'module_route:daily_finance_home'),
        pendingTarget: state.navigation.location?.pathname === '/daily',
        errorCount: errors.length,
        targetErrorSlot: Boolean(state.errors && Object.hasOwn(state.errors, 'module_route:daily_finance_home')),
        safeCodeMatched: errors.some(error => safeError(error).safeModuleCode)
      };
    };
    const info: any = { router, unsubscribe: undefined, routerOrdinal, observedStates: [] };
    const sampleState = (stage: string, state: typeof router.state) => {
      const sample = summarize(state); info.observedStates.push(sample);
      observations.record?.(stage, { routerOrdinal, ...sample });
    };
    sampleState('router_created', router.state);
    info.unsubscribe = router.subscribe(state => sampleState('router_update', state));
    observations.subscriptions++; observations.activeSubscriptions++;
    observations.routers.push(info);
    return router; // main receives the actual unmodified Router object.
  } };
});

test('D15-P3 | actual main Router publication and DOM order', async () => {
  const started = Date.now(); observations.started = started;
  observations.record = (stage, detail) => observations.timeline.push({ stage, elapsedMs: Date.now() - started, detail });
  const warnings: unknown[] = [];
  const recordWarning = (source: string, value: unknown) => warnings.push({ source, ...safeError(value) });
  const vc = new VirtualConsole();
  vc.on('jsdomError', value => recordWarning('jsdom', value));
  vc.on('error', value => recordWarning('virtual_console_error', value));
  vc.on('warn', value => recordWarning('virtual_console_warn', value));
  const errorSpy = vi.spyOn(console, 'error').mockImplementation((...values) => recordWarning('console_error', values[0]));
  const warnSpy = vi.spyOn(console, 'warn').mockImplementation((...values) => recordWarning('console_warn', values[0]));
  const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: 'http://127.0.0.1/', virtualConsole: vc });
  const savedGlobals = new Map(['window', 'document', 'location', 'IS_REACT_ACT_ENVIRONMENT'].map(name => [name, Object.getOwnPropertyDescriptor(globalThis, name)]));
  vi.stubGlobal('window', dom.window); vi.stubGlobal('document', dom.window.document);
  vi.stubGlobal('location', dom.window.location); vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  const unhandled = (event: any) => recordWarning('window_unhandled_rejection', event.reason);
  dom.window.addEventListener('unhandledrejection', unhandled);
  const calls = { runtime: 0, modules: 0, subscribe: 0, unsubscribe: 0, active: 0, settings: 0 };
  const ui = dailyFinanceContribution;
  const host = { module_id: ui.moduleId, version: ui.version, enabled: true,
    profile_ids: [ui.agentPanel.profileId], api_prefixes: [...ui.expectedApiPrefixes], settings_schema_version: 1 };
  Object.defineProperty(dom.window, 'maris', { value: {
    runtime: { getSnapshot: async () => { calls.runtime++; return { state: 'online', mode: 'managed', authenticated: true, errorCode: null }; },
      subscribe: () => { calls.subscribe++; calls.active++; return () => { calls.unsubscribe++; calls.active--; }; } },
    modules: { list: async () => { calls.modules++; return [host]; } },
    settings: { update: async () => { calls.settings++; return { ok: true }; } }
  } });
  let entry: typeof import('../../../../apps/desktop/src/renderer/main') | undefined;
  let waitStart = 0; let lastDom = ''; let stopReason = 'entry_not_started';
  const readDom = () => {
    const alert = dom.window.document.querySelector('[role="alert"]');
    return { alertShown: Boolean(alert), knownSafePrompt: Boolean(alert?.textContent?.includes('页面暂时无法打开')),
      shellPresent: Boolean(dom.window.document.querySelector('main.shell')),
      navigationPresent: Boolean(dom.window.document.querySelector('nav[aria-label="模块导航"]')),
      agentPanelPresent: Boolean(dom.window.document.querySelector('aside[aria-label="统一 Agent 面板"]')),
      contentHasText: Boolean(dom.window.document.querySelector('.content')?.textContent?.trim()),
      dailyHeadingPresent: [...dom.window.document.querySelectorAll('.content h1')].some(node => node.textContent === '日常财务'),
      openingPrompt: [...dom.window.document.querySelectorAll('[role="status"]')].some(node => node.textContent === '正在打开页面') };
  };
  const sampleDom = () => {
    const state = readDom(); const serialized = JSON.stringify(state);
    if (serialized !== lastDom) { lastDom = serialized; observations.record?.('dom_change', state); }
    return state;
  };
  const mutation = new dom.window.MutationObserver(() => sampleDom());
  mutation.observe(dom.window.document.getElementById('root')!, { childList: true, subtree: true, characterData: true });
  let beforeCleanup: unknown; let cleanup: unknown;
  try {
    observations.record('entry_enter');
    await act(async () => { entry = await import('../../../../apps/desktop/src/renderer/main'); });
    observations.record('entry_import_resolve'); waitStart = Date.now();
    const deadline = waitStart + 5000;
    while (Date.now() < deadline) {
      const state = sampleDom();
      if (observations.faultHits > 0 && state.knownSafePrompt) { stopReason = 'safe_alert_observed'; break; }
      const remaining = deadline - Date.now(); if (remaining <= 0) break;
      await act(async () => { await new Promise(resolve => setTimeout(resolve, Math.min(20, remaining))); });
    }
    if (stopReason !== 'safe_alert_observed') stopReason = observations.faultHits ? 'fault_hit_alert_missing' : 'fault_not_hit';
    beforeCleanup = { observedMs: Date.now() - waitStart, deadlineMs: 5000, stopReason, dom: sampleDom(),
      calls: { ...calls }, routerCount: observations.routers.length,
      routers: observations.routers.map(info => ({ routerOrdinal: info.routerOrdinal, lastState: info.observedStates.at(-1) })),
      loaders: observations.loaders.map(info => ({ ...info })) };
  } catch (error) {
    stopReason = 'unexpected_entry_or_observation_error';
    observations.record('unexpected_error', safeError(error));
    throw new Error('d15_unexpected_observation_error');
  } finally {
    if (entry) await act(async () => { entry!.desktopRoot.unmount(); });
    observations.record('root_unmount_complete', { rootEmpty: dom.window.document.getElementById('root')?.childElementCount === 0 });
    // Each saved object is an actual product-created Router. Product effects call
    // dispose at cleanup; observe the resulting own navigation state, then make
    // the documented idempotent disposal explicit for the observer's ownership.
    for (const info of observations.routers) {
      info.unsubscribe(); observations.unsubscribe++; observations.activeSubscriptions--;
      info.router.dispose();
      observations.record('router_observer_unsubscribe_and_dispose', { routerOrdinal: info.routerOrdinal });
    }
    mutation.disconnect(); dom.window.removeEventListener('unhandledrejection', unhandled);
    const rootEmpty = dom.window.document.getElementById('root')?.childElementCount === 0;
    dom.window.close(); vi.unstubAllGlobals(); errorSpy.mockRestore(); warnSpy.mockRestore();
    const globalsRestored = [...savedGlobals].every(([name, descriptor]) => {
      const current = Object.getOwnPropertyDescriptor(globalThis, name);
      return descriptor ? current?.value === descriptor.value && current?.get === descriptor.get : current === undefined;
    });
    cleanup = { rootUnmounted: Boolean(entry), rootEmpty, bridgeSubscriptions: calls.subscribe,
      bridgeUnsubscribe: calls.unsubscribe, activeBridgeSubscriptions: calls.active,
      routerObserverSubscriptions: observations.subscriptions, routerObserverUnsubscribe: observations.unsubscribe,
      activeRouterObserverSubscriptions: observations.activeSubscriptions, explicitDisposeCalls: observations.routers.length,
      domClosed: true, globalsRestored, stopReason };
    observations.record('cleanup_complete', cleanup);
    save('p3', { startedEpochMs: started, faultHits: observations.faultHits,
      faultElapsedMs: observations.faultTimes.map(time => time - started),
      observationMode: 'forward_same_routes_and_router; loader_same_promise_side_observer; no_navigate_or_revalidate',
      beforeCleanup, cleanup, warnings, timeline: observations.timeline });
    expect(calls.active).toBe(0); expect(observations.activeSubscriptions).toBe(0);
    expect(rootEmpty).toBe(true); expect(globalsRestored).toBe(true);
  }
});
