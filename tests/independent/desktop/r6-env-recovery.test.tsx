import { expect, test, vi } from 'vitest';
const record = (globalThis as any).__r6RecoveryRecord;
record('test_module_enter');
const { JSDOM, VirtualConsole } = (globalThis as any).__r6RecoveryDom;
record('react_import_enter');
let React: typeof import('react');
try { React = await import('react'); record('react_import_resolved'); }
catch { record('react_import_rejected'); throw Error('r6_recovery_react_import_failed'); }
const { act, createElement, StrictMode } = React;

test('R6-ENV-RECOVERY-01 | explicit recovery, navigation and state through real DesktopApp', async () => {
  record('body_enter');
  const bodyStart = performance.now();
  const deadline = bodyStart + 10000;
  const counts = { snapshots: 0, modules: 0, subscribe: 0, unsubscribe: 0, writes: 0, denied: 0, loads: 0, healthy: 0 };
  const callbacks = new Set<(value: any) => void>();
  const subscriptions = new Set<() => void>();
  const online = { state: 'online', mode: 'managed', authenticated: true, errorCode: null };
  const consoleNames = ['error', 'warn', 'log', 'info', 'debug', 'trace', 'dir', 'dirxml', 'table', 'assert', 'group', 'groupCollapsed', 'timeLog', 'timeEnd', 'count'] as const;
  const consoleOriginals = consoleNames.map(key => [key, console[key]] as const);
  const globalNames = ['window', 'document', 'location', 'IS_REACT_ACT_ENVIRONMENT', 'fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource'];
  const globalOriginals = globalNames.map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)] as const);
  const spies: any[] = [];
  let consoleLeak = false, incomplete = false, jsdomErrors = 0, rawConsoleCalls = 0;
  let dom: any, root: any, scenario = 0, shell: Element | null = null;
  let mode: 'fail' | 'ok' | 'pending' | 'render' = 'fail';
  let settleOld: ((Page: any) => void) | undefined;
  let unhandled: ((event: any) => void) | undefined;
  const privateText = 'R6_VIRTUAL_SECRET C:/virtual_r6/private/chunk.js';
  const leaked = (text: string) => /R6_VIRTUAL_SECRET|virtual_r6|(?:[A-Za-z]:[\\/]|file:\/\/)|\n\s+at\s/.test(text);
  const inspect = (values: any[]) => {
    rawConsoleCalls++;
    const seen = new Set<any>();
    const walk = (value: any, depth: number) => {
      if (value == null || seen.has(value)) return;
      if (depth > 8) { incomplete = true; return; }
      if (typeof value === 'string') { consoleLeak ||= leaked(value); return; }
      if (typeof value === 'object') {
        seen.add(value);
        for (const key of ['message', 'stack', 'cause', 'detail', 'reason', 'error']) {
          try { walk(value[key], depth + 1); } catch { incomplete = true; }
        }
        for (const key of Object.keys(value)) {
          const d = Object.getOwnPropertyDescriptor(value, key);
          if (d && 'value' in d) walk(d.value, depth + 1); else incomplete = true;
        }
      }
    };
    values.forEach(value => walk(value, 0));
  };
  const denied = function (..._args: unknown[]) { counts.denied++; throw Error('r6_recovery_forbidden_call'); };
  const unknown: any = new Proxy(denied, { get: (_target, key) => typeof key === 'symbol' ? undefined : unknown });
  const section = (object: object) => new Proxy(object, { get: (target, key) => Reflect.has(target, key) ? Reflect.get(target, key) : unknown });
  const q = (selector: string) => dom.window.document.querySelector(selector);
  const content = () => q('main.shell .content')?.textContent ?? '';
  const wait = async (condition: () => boolean) => {
    const until = Math.min(deadline - 30, performance.now() + 5000);
    while (!condition() && performance.now() < until) await act(async () => { await new Promise(resolve => setTimeout(resolve, 10)); });
    expect(condition(), 'bounded public condition').toBe(true);
  };
  const click = async (element: Element | null) => {
    expect(element, 'public control exists').not.toBeNull();
    await act(async () => { (element as HTMLElement).click(); });
  };
  const link = (route: string) => q(`main.shell nav a[href="#${route}"]`);
  const retry = () => q('main.shell .content [role="alert"] button');
  const alert = () => Boolean(q('main.shell .content [role="alert"]')?.textContent.includes('页面暂时无法打开'));
  const pause = async () => { await act(async () => { await new Promise(resolve => setTimeout(resolve, 60)); }); };
  const safety = () => {
    expect(q('main.shell')).toBe(shell);
    expect(q('main.shell nav[aria-label="模块导航"]')).not.toBeNull();
    expect(q('main.shell aside[aria-label="统一 Agent 面板"]')).not.toBeNull();
    expect(leaked(dom.window.document.documentElement.outerHTML)).toBe(false);
    expect(consoleLeak || incomplete).toBe(false);
    expect(jsdomErrors).toBe(0);
    expect(counts.denied).toBe(0);
  };
  const begin = (ordinal: number) => { scenario = ordinal; record('recovery_scenario_enter', { ordinal }); };
  const passed = () => { safety(); record('recovery_scenario_passed', { ordinal: scenario, loads: counts.loads, healthyLoads: counts.healthy, denied: counts.denied }); };
  let baseline: any;
  const stable = () => {
    expect(counts.snapshots).toBe(baseline.snapshots); expect(counts.modules).toBe(baseline.modules);
    expect(counts.subscribe).toBe(baseline.subscribe); expect(counts.unsubscribe).toBe(baseline.unsubscribe);
    expect(callbacks.size).toBe(1); expect(counts.writes).toBe(2);
    expect(q('main.shell')?.getAttribute('data-theme')).toBe('dark');
    expect(q('main.shell')?.getAttribute('data-privacy')).toBe('on');
    expect(q('main.shell header [role="status"]')?.textContent).toContain('offline');
  };
  try {
    const vc = new VirtualConsole();
    for (const key of consoleNames) {
      spies.push(vi.spyOn(console, key).mockImplementation((...args: any[]) => inspect(args)));
      vc.on(key, (...args: any[]) => inspect(args));
    }
    vc.on('jsdomError', (error: unknown) => { jsdomErrors++; inspect([error]); });
    dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: 'http://127.0.0.1/', virtualConsole: vc });
    vi.stubGlobal('window', dom.window); vi.stubGlobal('document', dom.window.document);
    vi.stubGlobal('location', dom.window.location); vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
    for (const key of ['fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource']) {
      vi.stubGlobal(key, denied); Object.defineProperty(dom.window, key, { value: denied, configurable: true });
    }
    unhandled = event => inspect([event.reason]); dom.window.addEventListener('unhandledrejection', unhandled);
    record('recovery_product_import_enter');
    const { createRoot } = await import('react-dom/client');
    const { compileRegistry } = await import('../../../apps/desktop/src/modules/registry');
    const { DesktopApp, rendererRootOptions } = await import('../../../apps/desktop/src/renderer/module-routes');
    record('recovery_product_import_resolved');
    const contribution = (name: string, route: string, order: number) => ({
      moduleId: name, version: '1.0.0', hostUiMajor: 1, expectedApiPrefixes: [`/api/v1/${name}`],
      navigation: { label: name, order }, routes: [{ routeId: name, path: route }],
      agentPanel: { profileId: `${name}.assistant@1`, title: name }, settings: [],
      companion: { appearanceId: name, label: name }
    });
    const registry = compileRegistry([contribution('virtual_recovery', '/broken', 1), contribution('virtual_safe', '/healthy', 2)]);
    const host = registry.map(m => ({ module_id: m.moduleId, version: m.version, enabled: true, profile_ids: [m.agentPanel.profileId], api_prefixes: m.expectedApiPrefixes, settings_schema_version: 1 }));
    const bridge = section({
      runtime: section({ getSnapshot: async () => { counts.snapshots++; return online; }, recover: denied,
        subscribe: (fn: (value: any) => void) => { counts.subscribe++; callbacks.add(fn); const off = () => { if (callbacks.delete(fn)) counts.unsubscribe++; subscriptions.delete(off); }; subscriptions.add(off); return off; } }),
      modules: section({ list: async () => { counts.modules++; return host; } }),
      settings: section({ update: async (value: any) => { counts.writes++; expect(value).toEqual(counts.writes === 1 ? { theme: 'dark' } : { privacyMode: true }); return { ok: true }; } }),
      outbox: section({ enqueue: denied }), window: section({ perform: denied }), external: section({ open: denied })
    });
    Object.defineProperty(dom.window, 'maris', { value: bridge });
    const Recovered = () => createElement('h1', null, 'R6 recovered page');
    const Healthy = () => createElement('h1', null, 'R6 healthy page');
    const Stale = () => createElement('h1', null, 'R6 stale page must not appear');
    const BrokenRender = () => { throw Error(privateText); };
    const loaders = {
      virtual_recovery: async () => {
        counts.loads++;
        if (mode === 'fail') throw Error(privateText);
        if (mode === 'pending') return new Promise<any>(resolve => { settleOld = resolve; });
        return mode === 'render' ? BrokenRender : Recovered;
      },
      virtual_safe: async () => { counts.healthy++; return Healthy; }
    };
    begin(1);
    root = createRoot(q('#root'), rendererRootOptions);
    await act(async () => { root.render(createElement(StrictMode, null, createElement(DesktopApp, { registry, loaders }))); });
    await wait(alert); shell = q('main.shell'); expect(counts.loads).toBe(1);
    expect(dom.window.location.hash).toBe('#/broken'); passed();

    begin(2);
    await act(async () => { const select = q('select[aria-label="主题"]'); select.value = 'dark'; select.dispatchEvent(new dom.window.Event('change', { bubbles: true })); });
    await click(q('input[type="checkbox"]'));
    await act(async () => { for (const fn of callbacks) fn({ ...online, state: 'offline' }); });
    baseline = { ...counts }; mode = 'ok'; await click(retry());
    await wait(() => content().includes('R6 recovered page')); expect(counts.loads).toBe(2); stable(); passed();

    begin(3);
    await click(link('/healthy')); await wait(() => content().includes('R6 healthy page'));
    await click(link('/settings')); await wait(() => q('main.shell .content h1')?.textContent === '设置');
    mode = 'fail'; await click(link('/broken')); await wait(alert);
    const initialFailureLoads = counts.loads; await pause(); expect(counts.loads).toBe(initialFailureLoads);
    await click(retry()); await wait(() => alert() && !retry()?.disabled);
    expect(counts.loads).toBe(initialFailureLoads + 1); await pause(); expect(counts.loads).toBe(initialFailureLoads + 1); stable(); passed();

    begin(4);
    mode = 'pending'; const beforePending = counts.loads;
    const button = retry();
    await act(async () => { button.click(); button.click(); button.click(); });
    await wait(() => counts.loads === beforePending + 1);
    expect(retry()?.disabled).toBe(true); await pause(); expect(counts.loads).toBe(beforePending + 1);
    await click(link('/healthy')); await wait(() => content().includes('R6 healthy page'));
    expect(settleOld).toBeTypeOf('function'); await act(async () => { settleOld!(Stale); });
    await pause(); expect(content()).toContain('R6 healthy page'); expect(content()).not.toContain('R6 stale page');
    expect(dom.window.location.hash).toBe('#/healthy'); stable(); passed();

    begin(5);
    mode = 'render'; await click(link('/broken')); await wait(alert); stable();
    const beforeRenderRetry = counts.loads; mode = 'ok'; await click(retry());
    await wait(() => content().includes('R6 recovered page')); expect(counts.loads).toBe(beforeRenderRetry + 1); stable(); passed();
    record('recovery_assertions_finished', { scenarios: 5, settingsWrites: counts.writes, denied: counts.denied, rawConsoleCalls, jsdomErrors, bodyMs: performance.now() - bodyStart });
    expect(performance.now() - bodyStart).toBeLessThanOrEqual(10000);
  } catch (error) {
    record('recovery_scenario_failed', { ordinal: scenario }); throw error;
  } finally {
    record('cleanup_enter', { bodyMs: performance.now() - bodyStart });
    const cleanupStart = performance.now();
    let unmounted = false, closed = false, listenersRemoved = false, restored = false, restoreFailed = false;
    let activeAfterUnmount = -1, rescueUnsubscribe = 0;
    try {
      if (root) { await act(async () => root.unmount()); unmounted = true; }
    } finally {
      activeAfterUnmount = callbacks.size;
      for (const off of [...subscriptions]) { try { off(); rescueUnsubscribe++; } catch { restoreFailed = true; } }
      try { if (dom && unhandled) { dom.window.removeEventListener('unhandledrejection', unhandled); listenersRemoved = true; } }
      finally {
        try { if (dom) { dom.window.close(); closed = true; } }
        finally {
          try { vi.unstubAllGlobals(); }
          finally { for (const spy of spies) { try { spy.mockRestore(); } catch { restoreFailed = true; } } }
        }
      }
      restored = globalOriginals.every(([key, before]) => {
        const after = Object.getOwnPropertyDescriptor(globalThis, key);
        return before ? Boolean(after) && ['value','get','set','writable','enumerable','configurable'].every(field => (after as any)?.[field] === (before as any)[field]) : !after;
      }) && consoleOriginals.every(([key, value]) => console[key] === value);
      record('cleanup_finished', { unmounted, closed, listenersRemoved, restored, restoreFailed, activeAfterUnmount, rescueUnsubscribe, subscribe: counts.subscribe, unsubscribe: counts.unsubscribe, denied: counts.denied, consoleLeak, incomplete, jsdomErrors, cleanupMs: performance.now() - cleanupStart });
      expect.soft(unmounted && closed && listenersRemoved && restored && !restoreFailed).toBe(true);
      expect.soft(activeAfterUnmount).toBe(0); expect.soft(rescueUnsubscribe).toBe(0); expect.soft(counts.subscribe).toBe(counts.unsubscribe);
      expect.soft(consoleLeak || incomplete).toBe(false); expect.soft(jsdomErrors).toBe(0); expect.soft(counts.denied).toBe(0);
      expect.soft(performance.now() - cleanupStart).toBeLessThanOrEqual(2000);
    }
  }
  record('test_body_finished');
});
record('test_module_ready');
