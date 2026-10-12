import { expect, test, vi } from 'vitest';
const record = (globalThis as any).__r7RecoveryRecord;
record('test_module_enter');
const { JSDOM, VirtualConsole } = (globalThis as any).__r7RecoveryDom;
record('react_import_enter');
let React: typeof import('react');
try { React = await import('react'); record('react_import_resolved'); }
catch { record('react_import_rejected'); throw Error('r7_recovery_react_import_failed'); }
const { act, createElement, StrictMode } = React;

test('R7-RECOVERY-01 | explicit recovery, navigation and state through real DesktopApp', async () => {
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

  let gateFailed = false, operation = 0, assertionSeq = 0;
  const scalar = (value: any): any => typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value)
    || ['dark','on','#/broken','#/healthy'].includes(value) ? value : 'unknown';
  const check = (id: string, observe: () => any, expectedValue: any, operator = 'eq', kind = 'gate') => {
    const expected = scalar(expectedValue), group = scenario, op = operation, assertion = ++assertionSeq;
    record('assert_enter', { id, group, operation: op, assertion, operator, kind, expected });
    let actual: any = 'unknown', passed = false;
    try {
      actual = scalar(observe());
      if (actual === 'unknown' || expected === 'unknown') throw Error('r7_unknown_comparison');
      if (operator === 'lte') expect(actual).toBeLessThanOrEqual(expected);
      else if (operator === 'positive_integer') expect(Number.isSafeInteger(actual) && actual > expected).toBe(true);
      else expect(actual).toBe(expected);
      passed = true;
    } catch { passed = false; }
    record(passed ? 'assert_pass' : 'assert_fail', { id, group, operation: op, assertion, operator, kind, expected, actual });
    if (!passed && kind === 'gate') gateFailed = true;
    return passed;
  };
  const guard = () => { if (gateFailed) throw Error('r7_formal_gate_failed'); };
  const op = async <T,>(id: string, fn: () => Promise<T> | T, cleanup = false): Promise<T> => {
    if (!cleanup) guard();
    const index = ++operation;
    record('operation_enter', { id, group: scenario, operation: index });
    try { const value = await fn(); record('operation_resolved', { id, group: scenario, operation: index }); return value; }
    catch (error) { record('operation_rejected', { id, group: scenario, operation: index, errorKind: error instanceof TypeError ? 'TypeError' : 'Error' }); throw error; }
  };
  const matchesUpdate = (value: any, expected: any) => {
    try { expect(value).toEqual(expected); return true; } catch { return false; }
  };
  const recorderSelftest = () => {
    record('recorder_selftest_enter');
    const different = check('SELF.DIFFERENT', () => 7, 9, 'eq', 'selftest');
    const boolean = check('SELF.BOOLEAN', () => true, true, 'eq', 'selftest');
    let rejected = false;
    try { record('selftest_forbidden', { rawError: 'R7_FORBIDDEN_PRIVATE_TEXT' }); } catch { rejected = true; }
    const text = (globalThis as any).__r7RecoveryReadJournal();
    const events = text.trimEnd().split('\n').map((line: string) => JSON.parse(line));
    const differentSaved = events.some((row: any) => row.stage === 'assert_fail' && row.id === 'SELF.DIFFERENT' && row.actual === 7 && row.expected === 9);
    const booleanSaved = events.some((row: any) => row.stage === 'assert_pass' && row.id === 'SELF.BOOLEAN' && row.actual === true && row.expected === true);
    const noRawField = !text.includes('R7_FORBIDDEN_PRIVATE_TEXT') && !events.some((row: any) => row.stage === 'selftest_forbidden');
    const passed = !different && boolean && rejected && differentSaved && booleanSaved && noRawField;
    record('recorder_selftest_result', { passed, differentSaved, booleanSaved, rejected, noRawField });
    if (!passed) throw Error('r7_recorder_selftest_failed');
  };
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
  const denied = function (..._args: unknown[]) { counts.denied++; throw Error('r7_recovery_forbidden_call'); };
  const unknown: any = new Proxy(denied, { get: (_target, key) => typeof key === 'symbol' ? undefined : unknown });
  const section = (object: object) => new Proxy(object, { get: (target, key) => Reflect.has(target, key) ? Reflect.get(target, key) : unknown });
  const q = (selector: string) => dom.window.document.querySelector(selector);
  const content = () => q('main.shell .content')?.textContent ?? '';
  const wait = async (condition: () => boolean) => op('OP.WAIT', async () => {
    const until = Math.min(deadline - 30, performance.now() + 5000);
    while (!condition() && performance.now() < until) await act(async () => { await new Promise(resolve => setTimeout(resolve, 10)); });
    check('WAIT.CONDITION', () => condition(), true, 'eq', 'gate');
  });
  const click = async (element: Element | null) => op('OP.CLICK', async () => {
    check('CLICK.PRESENT', () => element !== null, true, 'eq', 'gate');
    guard(); await act(async () => { (element as HTMLElement).click(); });
  });
  const link = (route: string) => q(`main.shell nav a[href="#${route}"]`);
  const retry = () => q('main.shell .content [role="alert"] button');
  const alert = () => Boolean(q('main.shell .content [role="alert"]')?.textContent.includes('页面暂时无法打开'));
  const pause = async () => op('OP.PAUSE', async () => { await act(async () => { await new Promise(resolve => setTimeout(resolve, 60)); }); });
  const safety = () => {
    check('SAFETY.SHELL_SAME', () => q('main.shell') === shell, true, 'eq', 'gate');
    check('SAFETY.NAV_PRESENT', () => q('main.shell nav[aria-label="模块导航"]') !== null, true, 'eq', 'gate');
    check('SAFETY.AGENT_PRESENT', () => q('main.shell aside[aria-label="统一 Agent 面板"]') !== null, true, 'eq', 'gate');
    check('SAFETY.DOM_LEAK', () => leaked(dom.window.document.documentElement.outerHTML), false, 'eq', 'gate');
    check('SAFETY.CONSOLE_LEAK', () => consoleLeak || incomplete, false, 'eq', 'gate');
    check('SAFETY.JSDOM_ERRORS', () => jsdomErrors, 0, 'eq', 'gate');
    check('SAFETY.DENIED', () => counts.denied, 0, 'eq', 'gate');
  };
  const begin = (ordinal: number) => { scenario = ordinal; record('recovery_scenario_enter', { ordinal }); };
  const passed = () => { safety(); guard(); record('recovery_scenario_passed', { ordinal: scenario, loads: counts.loads, healthyLoads: counts.healthy, denied: counts.denied }); };
  let baseline: any;
  const stable = () => {
    check('STABLE.SNAPSHOTS', () => counts.snapshots, baseline.snapshots, 'eq', 'gate'); check('STABLE.MODULES', () => counts.modules, baseline.modules, 'eq', 'gate');
    check('STABLE.SUBSCRIBE', () => counts.subscribe, baseline.subscribe, 'eq', 'gate'); check('STABLE.UNSUBSCRIBE', () => counts.unsubscribe, baseline.unsubscribe, 'eq', 'gate');
    check('STABLE.ACTIVE', () => callbacks.size, 1, 'eq', 'gate'); check('STABLE.SETTINGS_WRITES', () => counts.writes, 2, 'eq', 'gate');
    check('STABLE.THEME', () => q('main.shell')?.getAttribute('data-theme'), 'dark', 'eq', 'gate');
    check('STABLE.PRIVACY', () => q('main.shell')?.getAttribute('data-privacy'), 'on', 'eq', 'gate');
    check('STABLE.RUNTIME_OFFLINE', () => Boolean(q('main.shell header [role="status"]')?.textContent?.includes('offline')), true, 'eq', 'gate');
  };
  try {
    recorderSelftest();
    await op('OP.DOM_SETUP', async () => {
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
    });
    const { createRoot, compileRegistry, DesktopApp, rendererRootOptions } = await op('OP.IMPORTS', async () => {
    record('recovery_product_import_enter');
    const { createRoot } = await import('react-dom/client');
    const { compileRegistry } = await import('../../../apps/desktop/src/modules/registry');
    const { DesktopApp, rendererRootOptions } = await import('../../../apps/desktop/src/renderer/module-routes');
    record('recovery_product_import_resolved');
    return { createRoot, compileRegistry, DesktopApp, rendererRootOptions };
    });
    const contribution = (name: string, route: string, order: number) => ({
      moduleId: name, version: '1.0.0', hostUiMajor: 1, expectedApiPrefixes: [`/api/v1/${name}`],
      navigation: { label: name, order }, routes: [{ routeId: name, path: route }],
      agentPanel: { profileId: `${name}.assistant@1`, title: name }, settings: [],
      companion: { appearanceId: name, label: name }
    });
    const registry = await op('OP.REGISTRY', async () => compileRegistry([contribution('virtual_recovery', '/broken', 1), contribution('virtual_safe', '/healthy', 2)]));
    const host = registry.map(m => ({ module_id: m.moduleId, version: m.version, enabled: true, profile_ids: [m.agentPanel.profileId], api_prefixes: m.expectedApiPrefixes, settings_schema_version: 1 }));
    const bridge = section({
      runtime: section({ getSnapshot: async () => { counts.snapshots++; return online; }, recover: denied,
        subscribe: (fn: (value: any) => void) => { counts.subscribe++; callbacks.add(fn); const off = () => { if (callbacks.delete(fn)) counts.unsubscribe++; subscriptions.delete(off); }; subscriptions.add(off); return off; } }),
      modules: section({ list: async () => { counts.modules++; return host; } }),
      settings: section({ update: async (value: any) => { counts.writes++; check('SETTINGS.PAYLOAD', () => matchesUpdate(value, counts.writes === 1 ? { theme: 'dark' } : { privacyMode: true }), true, 'eq', 'gate'); return { ok: true }; } }),
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
    await op('OP.MOUNT', async () => {
      root = createRoot(q('#root'), rendererRootOptions);
      await act(async () => { root.render(createElement(StrictMode, null, createElement(DesktopApp, { registry, loaders }))); });
    });
    await wait(alert); shell = q('main.shell');
    const initialBaseline = counts.loads;
    record('initial_baseline', { initialBaseline });
    check('legacy_initial_exact_1', () => initialBaseline, 1, 'eq', 'legacy');
    check('G1.POSITIVE_INITIAL', () => initialBaseline, 0, 'positive_integer');
    check('G1.HASH', () => dom.window.location.hash, '#/broken');
    safety(); guard();
    await pause(); check('G1.FIXED_QUIET', () => counts.loads, initialBaseline); passed();

    begin(2);
    await op('OP.THEME', async () => { await act(async () => { const select = q('select[aria-label="主题"]'); select.value = 'dark'; select.dispatchEvent(new dom.window.Event('change', { bubbles: true })); }); });
    await click(q('input[type="checkbox"]'));
    await op('OP.RUNTIME', async () => { await act(async () => { for (const fn of callbacks) fn({ ...online, state: 'offline' }); }); });
    baseline = { ...counts };
    const preRetry = counts.loads;
    check('G2.PRE_RETRY_BASELINE', () => preRetry, initialBaseline);
    safety(); guard();
    mode = 'ok'; await click(retry()); await wait(() => content().includes('R6 recovered page'));
    const postRetry = counts.loads;
    check('legacy_first_retry_total_2', () => postRetry, 2, 'eq', 'legacy');
    check('G2.RETRY_TOTAL', () => postRetry, initialBaseline + 1);
    check('G2.RETRY_DELTA', () => postRetry - preRetry, 1); stable(); passed();

    begin(3);
    const beforeHealthyLoads = counts.loads, beforeHealthy = counts.healthy;
    await click(link('/healthy')); await wait(() => content().includes('R6 healthy page'));
    check('G3.HEALTHY_DELTA', () => counts.healthy - beforeHealthy, 1);
    check('G3.LEAVE_NO_BROKEN_LOAD', () => counts.loads, beforeHealthyLoads); safety(); guard();
    const beforeSettingsLoads = counts.loads, beforeSettingsHealthy = counts.healthy;
    await click(link('/settings')); await wait(() => q('main.shell .content h1')?.textContent === '设置');
    check('G3.SETTINGS_NO_LOAD', () => counts.loads, beforeSettingsLoads);
    check('G3.SETTINGS_NO_HEALTHY_LOAD', () => counts.healthy, beforeSettingsHealthy); safety(); guard();
    const beforeReturn = counts.loads;
    mode = 'fail'; await click(link('/broken')); await wait(alert);
    check('G3.RETURN_DELTA', () => counts.loads - beforeReturn, 1); safety(); guard();
    const initialFailureLoads = counts.loads; await pause(); check('G3.QUIET_INITIAL', () => counts.loads, initialFailureLoads); safety(); guard();
    await click(retry()); await wait(() => alert() && !retry()?.disabled);
    check('G3.RETRY_TOTAL', () => counts.loads, initialFailureLoads + 1); safety(); guard();
    await pause(); check('G3.QUIET_AFTER_RETRY', () => counts.loads, initialFailureLoads + 1); stable(); passed();

    begin(4);
    mode = 'pending'; const beforePending = counts.loads;
    const button = retry();
    await op('OP.REPEAT_CLICK', async () => { await act(async () => { button.click(); button.click(); button.click(); }); });
    await wait(() => counts.loads === beforePending + 1);
    check('G4.PENDING_DISABLED', () => retry()?.disabled, true); safety(); guard();
    await pause(); check('G4.SINGLE_INFLIGHT', () => counts.loads, beforePending + 1); safety(); guard();
    await click(link('/healthy')); await wait(() => content().includes('R6 healthy page'));
    check('G4.SETTLER_PRESENT', () => typeof settleOld === 'function', true); safety(); guard();
    await op('OP.SETTLE_OLD', async () => { await act(async () => { settleOld!(Stale); }); });
    await pause(); check('G4.HEALTHY_VISIBLE', () => content().includes('R6 healthy page'), true);
    check('G4.STALE_ABSENT', () => content().includes('R6 stale page'), false);
    check('G4.HASH', () => dom.window.location.hash, '#/healthy'); stable(); passed();

    begin(5);
    mode = 'render'; await click(link('/broken')); await wait(alert); stable(); safety(); guard();
    const beforeRenderRetry = counts.loads; mode = 'ok'; await click(retry());
    await wait(() => content().includes('R6 recovered page')); check('G5.RETRY_TOTAL', () => counts.loads, beforeRenderRetry + 1); stable(); passed();
    record('recovery_assertions_finished', { scenarios: 5, settingsWrites: counts.writes, denied: counts.denied, rawConsoleCalls, jsdomErrors, bodyMs: performance.now() - bodyStart });
    check('BODY.BUDGET', () => performance.now() - bodyStart, 10000, 'lte', 'gate');
  } catch (error) {
    record('recovery_scenario_failed', { ordinal: scenario }); throw error;
  } finally {
    scenario = 6;
    record('cleanup_enter', { bodyMs: performance.now() - bodyStart });
    const cleanupStart = performance.now();
    let unmounted = false, closed = false, listenersRemoved = false, restored = false, restoreFailed = false;
    let activeAfterUnmount = -1, rescueUnsubscribe = 0;
    try {
      if (root) { await op('OP.UNMOUNT', async () => { await act(async () => root.unmount()); unmounted = true; }, true); }
    } finally {
      activeAfterUnmount = callbacks.size;
      await op('OP.UNSUBSCRIBE_RESCUE', async () => { for (const off of [...subscriptions]) { try { off(); rescueUnsubscribe++; } catch { restoreFailed = true; } } }, true);
      try { await op('OP.REMOVE_LISTENER', async () => { if (dom && unhandled) { dom.window.removeEventListener('unhandledrejection', unhandled); listenersRemoved = true; } }, true); }
      finally {
        try { await op('OP.CLOSE_DOM', async () => { if (dom) { dom.window.close(); closed = true; } }, true); }
        finally {
          try { await op('OP.RESTORE_GLOBALS', async () => { vi.unstubAllGlobals(); }, true); }
          finally { await op('OP.RESTORE_CONSOLE', async () => { for (const spy of spies) { try { spy.mockRestore(); } catch { restoreFailed = true; } } }, true); }
        }
      }
      restored = globalOriginals.every(([key, before]) => {
        const after = Object.getOwnPropertyDescriptor(globalThis, key);
        return before ? Boolean(after) && ['value','get','set','writable','enumerable','configurable'].every(field => (after as any)?.[field] === (before as any)[field]) : !after;
      }) && consoleOriginals.every(([key, value]) => console[key] === value);
      record('cleanup_finished', { unmounted, closed, listenersRemoved, restored, restoreFailed, activeAfterUnmount, rescueUnsubscribe, subscribe: counts.subscribe, unsubscribe: counts.unsubscribe, denied: counts.denied, consoleLeak, incomplete, jsdomErrors, cleanupMs: performance.now() - cleanupStart });
      check('CLEANUP.RESOURCES', () => unmounted && closed && listenersRemoved && restored && !restoreFailed, true, 'eq', 'gate');
      check('CLEANUP.ACTIVE', () => activeAfterUnmount, 0, 'eq', 'gate'); check('CLEANUP.RESCUE', () => rescueUnsubscribe, 0, 'eq', 'gate'); check('CLEANUP.UNSUBSCRIBE', () => counts.subscribe, counts.unsubscribe, 'eq', 'gate');
      check('CLEANUP.CONSOLE', () => consoleLeak || incomplete, false, 'eq', 'gate'); check('CLEANUP.JSDOM', () => jsdomErrors, 0, 'eq', 'gate'); check('CLEANUP.DENIED', () => counts.denied, 0, 'eq', 'gate');
      check('CLEANUP.BUDGET', () => performance.now() - cleanupStart, 2000, 'lte', 'gate');
    }
  }
  guard();
  record('test_body_finished');
});
record('test_module_ready');
