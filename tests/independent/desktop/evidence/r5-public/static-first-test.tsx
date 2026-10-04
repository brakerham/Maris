import { expect, test, vi } from 'vitest';
const record = (globalThis as any).__r5PublicRecord;
record('test_module_enter');
record('jsdom_import_enter');
let domModule: typeof import('jsdom');
try { domModule = await import('jsdom'); record('jsdom_import_resolved'); }
catch { record('jsdom_import_rejected'); throw Error('r5_public_jsdom_import_failed'); }
record('react_import_enter');
let reactModule: typeof import('react');
try { reactModule = await import('react'); record('react_import_resolved'); }
catch { record('react_import_rejected'); throw Error('r5_public_react_import_failed'); }
const { JSDOM, VirtualConsole } = domModule;
const { act } = reactModule;

test('R5-PUBLIC-UI-02-COLD | actual cold main and persistent ESM fault, four public assertions', async () => {
  record('body_enter');
  const bodyStarted = performance.now();
  const bodyDeadline = bodyStarted + 10000;
  const calls = { runtime: 0, modules: 0, subscribe: 0, unsubscribe: 0, active: 0,
    recover: 0, settings: 0, outbox: 0, windowAction: 0, external: 0, unknownBridge: 0,
    fetch: 0, xhr: 0, socket: 0, eventSource: 0 };
  const warnings = { count: 0, rawVirtual: false, rawPath: false, rawStack: false, incomplete: false };
  const globalKeys = ['window', 'document', 'location', 'IS_REACT_ACT_ENVIRONMENT', 'fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource'];
  const originals = new Map(globalKeys.map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  const consoleKeys = ['error', 'warn', 'log', 'info', 'debug', 'trace', 'dir', 'dirxml', 'table', 'assert', 'group', 'groupCollapsed', 'timeLog', 'timeEnd', 'count'] as const;
  const originalConsole = new Map(consoleKeys.map(key => [key, console[key]]));
  const consoleSpies: Array<ReturnType<typeof vi.spyOn>> = [];
  const subscriptions = new Set<() => void>();
  let dom: InstanceType<typeof JSDOM> | undefined;
  let entry: typeof import('../../../apps/desktop/src/renderer/main') | undefined;
  let mainStarted = 0, mainResolved = false, actReturned = false, initialEmptyHash = false;
  let initializationFailed = false, bodyOperationFailed = false, observationMs = 0;
  let unhandled: ((event: any) => void) | undefined;
  let rootUnmounted = false, domClosed = false, listenersRemoved = false, globalsRestored = false, consoleRestored = false;
  let cleanupOperationFailed = false;
  let activeAfterUnmount: number | undefined, unsubscribeAfterUnmount: number | undefined, rescueUnsubscribe = 0;

  const inspect = (values: unknown[]) => {
    const seen = new Set<unknown>();
    let rawVirtual = false, rawPath = false, rawStack = false, incomplete = false;
    const scan = (value: any, depth = 0) => {
      if (value === null || value === undefined || seen.has(value)) return;
      if (depth > 8) { incomplete = true; return; }
      if (typeof value === 'object') {
        seen.add(value);
        for (const key of ['message', 'stack', 'cause', 'detail', 'error', 'reason']) {
          try { scan(value[key], depth + 1); } catch { /* Never invoke raw logging. */ }
        }
        if (Array.isArray(value)) for (const item of value) scan(item, depth + 1);
        for (const key of Object.keys(value)) {
          const descriptor = Object.getOwnPropertyDescriptor(value, key);
          if (descriptor && 'value' in descriptor) scan(descriptor.value, depth + 1);
          else incomplete = true;
        }
      } else if (typeof value === 'string') {
        rawVirtual ||= value.includes('VIRTUAL_CHUNK_UNAVAILABLE');
        rawPath ||= /(?:[A-Za-z]:[\\/]|file:\/\/|apps[\\/]desktop[\\/]src|MarisLazyR5)/.test(value);
        rawStack ||= /(?:\n\s+at\s|\bat\s+.*:\d+:\d+)/.test(value);
      }
    };
    values.forEach(value => scan(value));
    warnings.count++; warnings.rawVirtual ||= rawVirtual; warnings.rawPath ||= rawPath; warnings.rawStack ||= rawStack; warnings.incomplete ||= incomplete;
    record('safe_console_observation', { count: warnings.count, rawVirtual, rawPath, rawStack, incomplete });
  };
  const forbidden = (key: keyof typeof calls, ordinal: number) => function deniedBoundary(..._unused: unknown[]) {
    calls[key]++; record('boundary_call_denied', { ordinal, count: calls[key] });
    throw Error('r5_public_forbidden_boundary_call');
  };
  const unknown = new Proxy(forbidden('unknownBridge', 6), { get: (_target, key) => typeof key === 'symbol' ? undefined : unknown });
  const section = (value: object) => new Proxy(value, { get: (target, key) => Reflect.has(target, key) ? Reflect.get(target, key) : unknown });
  const sample = () => {
    const shell = dom?.window.document.querySelector('main.shell');
    const localAlert = shell?.querySelector('.content [role="alert"]');
    const text = (dom?.window.document.documentElement.outerHTML ?? '') + '\n' + (dom?.window.document.body.textContent ?? '');
    return Object.freeze({ alertText: localAlert?.textContent ?? '',
      alertTextSafe: Boolean(localAlert?.textContent?.includes('页面暂时无法打开')),
      shellPresent: Boolean(shell), navigationPresent: Boolean(shell?.querySelector('nav[aria-label="模块导航"]')),
      agentPanelPresent: Boolean(shell?.querySelector('aside[aria-label="统一 Agent 面板"]')),
      dailyHash: dom?.window.location.hash === '#/daily',
      rawVirtualInDom: text.includes('VIRTUAL_CHUNK_UNAVAILABLE'),
      rawPathInDom: /(?:[A-Za-z]:[\\/]|file:\/\/|apps[\\/]desktop[\\/]src|MarisLazyR5)/.test(text),
      rawStackInDom: /(?:\n\s+at\s|\bat\s+.*:\d+:\d+)/.test(text) });
  };
  const withinBody = async <T,>(promise: Promise<T>): Promise<T> => {
    const remaining = bodyDeadline - performance.now();
    if (remaining <= 0) throw Error('r5_public_body_deadline');
    let timer: ReturnType<typeof setTimeout>;
    try { return await Promise.race([promise, new Promise<never>((_resolve, reject) => { timer = setTimeout(() => reject(Error('r5_public_body_deadline')), remaining); })]); }
    finally { clearTimeout(timer!); }
  };
  try {
    try {
      const vc = new VirtualConsole();
      vc.on('jsdomError', (error: unknown) => inspect([error]));
      vc.on('error', (...values: unknown[]) => inspect(values));
      vc.on('warn', (...values: unknown[]) => inspect(values));
      for (const key of consoleKeys) consoleSpies.push(vi.spyOn(console, key).mockImplementation((...values: unknown[]) => inspect(values)));
      for (const key of ['log', 'info', 'debug', 'dir', 'dirxml', 'trace', 'table', 'assert', 'group', 'groupCollapsed']) vc.on(key, (...values: unknown[]) => inspect(values));
      dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: 'http://127.0.0.1/', virtualConsole: vc });
      initialEmptyHash = dom.window.location.hash === '';
      vi.stubGlobal('window', dom.window); vi.stubGlobal('document', dom.window.document);
      vi.stubGlobal('location', dom.window.location); vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
      const blockedFetch = forbidden('fetch', 7);
      const BlockedXhr = forbidden('xhr', 8), BlockedSocket = forbidden('socket', 9), BlockedEventSource = forbidden('eventSource', 10);
      for (const [key, value] of [['fetch', blockedFetch], ['XMLHttpRequest', BlockedXhr], ['WebSocket', BlockedSocket], ['EventSource', BlockedEventSource]] as const) {
        vi.stubGlobal(key, value); Object.defineProperty(dom.window, key, { value, configurable: true, writable: true });
      }
      unhandled = event => inspect([event.reason]);
      dom.window.addEventListener('unhandledrejection', unhandled);
      const bridge = section({
        runtime: section({ getSnapshot: async () => { calls.runtime++; return { state: 'online', mode: 'managed', authenticated: true, errorCode: null }; },
          recover: forbidden('recover', 1), subscribe: () => {
            calls.subscribe++; calls.active++;
            let active = true;
            const off = () => { if (active) { active = false; calls.unsubscribe++; calls.active--; subscriptions.delete(off); } };
            subscriptions.add(off); return off;
          } }),
        modules: section({ list: async () => { calls.modules++; return [{ module_id: 'daily_finance', version: '1.0.0', enabled: true,
          profile_ids: ['daily_finance.assistant@1'], api_prefixes: ['/api/v1/finance'], settings_schema_version: 1 }]; } }),
        settings: section({ update: forbidden('settings', 2) }), outbox: section({ enqueue: forbidden('outbox', 3) }),
        window: section({ perform: forbidden('windowAction', 4) }), external: section({ open: forbidden('external', 5) })
      });
      Object.defineProperty(dom.window, 'maris', { value: bridge });
      record('virtual_dom_bridge_ready', { emptyHash: initialEmptyHash, completeBridgeBoundaries: true, networkGuardsInstalled: true });
      record('act_enter');
      try {
        await withinBody(act(async () => {
          record('main_import_enter'); mainStarted++;
          const mainPromise = import('../../../apps/desktop/src/renderer/main');
          mainPromise.then(value => { entry = value; mainResolved = true; record('main_import_resolved'); }, () => record('main_import_rejected'));
          await mainPromise;
          record('root_created', { rootIsObject: typeof entry?.desktopRoot === 'object' });
        }));
        actReturned = true; record('act_return');
      } catch { record('act_rejected'); bodyOperationFailed = true; }
      const observeStarted = performance.now();
      const observeDeadline = Math.min(observeStarted + 5000, bodyDeadline);
      let state = sample();
      while (actReturned && !(state.alertTextSafe && (globalThis as any).__r5PublicFixtureHits > 0) && performance.now() + 30 < observeDeadline) {
        await withinBody(act(async () => { await new Promise(resolve => setTimeout(resolve, Math.min(15, observeDeadline - performance.now() - 15))); }));
        state = sample();
      }
      observationMs = performance.now() - observeStarted;
      record('observation_finished', { observationMs, alertTextSafe: state.alertTextSafe, dailyHash: state.dailyHash });
    } catch { initializationFailed = true; record('body_operation_rejected'); }

    // Capture all four public requirements synchronously from this one Shell.
    const final = sample();
    record('public_sample', { sampleOrdinal: 1, alertTextSafe: final.alertTextSafe, shellPresent: final.shellPresent,
      navigationPresent: final.navigationPresent, agentPanelPresent: final.agentPanelPresent, dailyHash: final.dailyHash,
      rawVirtualInDom: final.rawVirtualInDom, rawPathInDom: final.rawPathInDom, rawStackInDom: final.rawStackInDom });
    record('assertions_enter');
    expect.soft(final.alertText).toContain('页面暂时无法打开');
    record('public_assertion', { ordinal: 1, passed: final.alertTextSafe, sampleOrdinal: 1 });
    expect.soft(final.shellPresent, 'original Shell requirement').toBe(true);
    record('public_assertion', { ordinal: 2, passed: final.shellPresent, sampleOrdinal: 1 });
    expect.soft(final.navigationPresent, 'original module navigation requirement').toBe(true);
    record('public_assertion', { ordinal: 3, passed: final.navigationPresent, sampleOrdinal: 1 });
    expect.soft(final.agentPanelPresent, 'original unified Agent panel requirement').toBe(true);
    record('public_assertion', { ordinal: 4, passed: final.agentPanelPresent, sampleOrdinal: 1 });
    let proof: any = { exactMappingValid: false, mappingIdentityValid: false, actualWorkerEvaluationValid: false,
      fixedPersistentFixtureValid: false, defaultLoaderContractValid: false, noCacheOrSuccessSubstitute: false, repositoryRootBound: false };
    try { proof = (globalThis as any).__r5PublicSourceProof(); } catch { record('source_proof_unavailable'); }
    const coldEntryContractValid = initialEmptyHash && mainStarted === 1 && mainResolved && actReturned;
    const faultSourceValid = proof.exactMappingValid && proof.mappingIdentityValid && proof.actualWorkerEvaluationValid &&
      proof.fixedPersistentFixtureValid && proof.defaultLoaderContractValid && proof.noCacheOrSuccessSubstitute && proof.repositoryRootBound && coldEntryContractValid;
    record('fault_source', { ...proof, coldEntryContractValid, faultSourceValid });
    const publicTargetResult = final.dailyHash && final.alertTextSafe && final.shellPresent && final.navigationPresent && final.agentPanelPresent;
    record('public_target_result', { publicTargetResult, sampleOrdinal: 1 });
    const boundariesSafe = calls.recover + calls.settings + calls.outbox + calls.windowAction + calls.external + calls.unknownBridge + calls.fetch + calls.xhr + calls.socket + calls.eventSource === 0;
    const domSafe = !final.rawVirtualInDom && !final.rawPathInDom && !final.rawStackInDom;
    const consoleSafe = !warnings.rawVirtual && !warnings.rawPath && !warnings.rawStack && !warnings.incomplete;
    record('safety_assertions', { ...calls, boundariesSafe, domSafe, consoleSafe, warningCount: warnings.count });
    expect.soft(faultSourceValid, 'current fault source, independent of DOM outcome').toBe(true);
    expect.soft(final.dailyHash).toBe(true);
    expect.soft(initializationFailed || bodyOperationFailed).toBe(false);
    expect.soft(observationMs).toBeLessThanOrEqual(5000);
    expect.soft(calls.runtime).toBeGreaterThan(0); expect.soft(calls.modules).toBeGreaterThan(0); expect.soft(calls.subscribe).toBeGreaterThan(0);
    for (const key of ['recover', 'settings', 'outbox', 'windowAction', 'external', 'unknownBridge', 'fetch', 'xhr', 'socket', 'eventSource'] as const) expect.soft(calls[key], key).toBe(0);
    expect.soft(domSafe).toBe(true); expect.soft(consoleSafe).toBe(true);
    record('assertions_finished', { bodyMs: performance.now() - bodyStarted });
    expect.soft(performance.now() - bodyStarted).toBeLessThanOrEqual(10000);
  } finally {
    record('cleanup_enter', { bodyMs: performance.now() - bodyStarted, rootCreated: Boolean(entry), domCreated: Boolean(dom) });
    const cleanupStarted = performance.now();
    try {
      if (entry) {
        record('root_unmount_enter');
        try { await act(async () => entry!.desktopRoot.unmount()); rootUnmounted = true; record('root_unmounted'); }
        catch { cleanupOperationFailed = true; record('root_unmount_rejected'); }
      }
      activeAfterUnmount = calls.active; unsubscribeAfterUnmount = calls.unsubscribe;
      record('root_unmount_subscriptions', { activeAfterUnmount, unsubscribeAfterUnmount, subscriptions: calls.subscribe });
    } finally {
      try {
        for (const off of [...subscriptions]) {
          try { off(); rescueUnsubscribe++; } catch { cleanupOperationFailed = true; record('bridge_unsubscribe_rejected'); }
        }
        if (dom && unhandled) { dom.window.removeEventListener('unhandledrejection', unhandled); listenersRemoved = true; }
      } finally {
        const rootEmpty = dom?.window.document.getElementById('root')?.childElementCount === 0;
        try { if (dom) { dom.window.close(); domClosed = true; record('dom_closed'); } }
        catch { cleanupOperationFailed = true; record('dom_close_rejected'); }
        finally {
          try { vi.unstubAllGlobals(); }
          catch { cleanupOperationFailed = true; record('global_restore_rejected'); }
          finally {
            for (const spy of consoleSpies) { try { spy.mockRestore(); } catch { cleanupOperationFailed = true; } }
          }
        }
        globalsRestored = [...originals].every(([key, before]) => {
          const after = Object.getOwnPropertyDescriptor(globalThis, key);
          return before ? Boolean(after) && ['value', 'get', 'set', 'writable', 'enumerable', 'configurable'].every(field => (after as any)?.[field] === (before as any)[field]) : after === undefined;
        });
        consoleRestored = [...originalConsole].every(([key, value]) => console[key] === value);
        const finalBoundaryCalls = calls.recover + calls.settings + calls.outbox + calls.windowAction + calls.external + calls.unknownBridge + calls.fetch + calls.xhr + calls.socket + calls.eventSource;
        const finalConsoleSafe = !warnings.rawVirtual && !warnings.rawPath && !warnings.rawStack && !warnings.incomplete;
        record('cleanup_finished', { cleanupMs: performance.now() - cleanupStarted, rootCreated: Boolean(entry), rootUnmounted,
          rootEmpty: Boolean(rootEmpty), domCreated: Boolean(dom), domClosed, listenersRemoved, globalsRestored, consoleRestored,
          subscriptions: calls.subscribe, unsubscribe: calls.unsubscribe, activeSubscriptions: calls.active, rescueUnsubscribe,
          finalBoundaryCalls, finalConsoleSafe, cleanupOperationFailed });
        expect.soft(Boolean(entry) && rootUnmounted && rootEmpty).toBe(true);
        expect.soft(domClosed && listenersRemoved && globalsRestored && consoleRestored).toBe(true);
        expect.soft(cleanupOperationFailed).toBe(false);
        expect.soft(calls.active).toBe(0); expect.soft(calls.unsubscribe).toBe(calls.subscribe);
        expect.soft(activeAfterUnmount, 'production unmount must unsubscribe without rescue').toBe(0);
        expect.soft(unsubscribeAfterUnmount).toBe(calls.subscribe); expect.soft(rescueUnsubscribe).toBe(0);
        expect.soft(finalBoundaryCalls).toBe(0); expect.soft(finalConsoleSafe).toBe(true);
        expect.soft(performance.now() - cleanupStarted).toBeLessThanOrEqual(2000);
      }
    }
  }
  record('test_body_finished');
});
record('test_module_ready');
