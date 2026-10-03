// Only loaded by the real main -> module-routes bare Router dependency.
// This distinct alias resolves the same real package, never back to this facade.
import { createHashRouter as realCreateHashRouter } from '__c12R3_real_router';
export * from '__c12R3_real_router';
const record = globalThis.__c12R3Record;
const trace = globalThis.__c12R3Trace;
record('facade_loaded', {realFactoryIsFunction: typeof realCreateHashRouter === 'function'});
const targetId = 'module_route:daily_finance_home';
function safeKind(error) {
  return ['Error', 'TypeError', 'AbortError'].includes(error?.name) ? error.name : 'other';
}
function stateReceipt(item) {
  const state = item.router.state;
  const targetError = state.errors?.[targetId];
  const targetMatch = state.matches.some(match => match.route.id === targetId);
  item.last = {routerSeq: item.seq, active: trace.active === item,
    initialized: state.initialized, navigation: state.navigation.state,
    targetMatch, targetError: Boolean(targetError),
    safeModuleCode: targetError?.message === 'desktop_module_unavailable',
    errorCount: Object.keys(state.errors ?? {}).length};
  record('router_state', item.last);
}
export function createHashRouter(...args) {
  const item = {seq: trace.routers.length + 1, router: null, attempts: [],
    unsubscribe: null, abortCleanup: [], last: null};
  if (trace.active) record('router_superseded', {routerSeq: trace.active.seq});
  trace.routers.push(item); trace.active = item;
  record('router_create_enter', {routerSeq: item.seq});
  const visit = routes => {
    for (const route of routes) {
      if (route.id === targetId && typeof route.loader === 'function') {
        const original = route.loader;
        // Same route object, this/args, returned Promise identity. Only function
        // identity and side listeners change; no result or navigation changes.
        route.loader = function (...loaderArgs) {
          const signal = loaderArgs[0]?.request?.signal;
          const attempt = {seq: item.attempts.length + 1, terminal: null, signal, safeModuleCode: false};
          item.attempts.push(attempt);
          const detail = () => ({routerSeq: item.seq, attemptSeq: attempt.seq,
            active: trace.active === item, aborted: signal?.aborted === true});
          record('loader_enter', detail());
          const onAbort = () => record('loader_aborted', detail());
          signal?.addEventListener('abort', onAbort, {once: true});
          item.abortCleanup.push(() => signal?.removeEventListener('abort', onAbort));
          let originalPromise;
          try { originalPromise = Reflect.apply(original, this, loaderArgs); }
          catch (error) {
            attempt.terminal = 'rejected'; attempt.safeModuleCode = error?.message === 'desktop_module_unavailable';
            record('loader_rejected', {...detail(), synchronous: true, safeModuleCode: attempt.safeModuleCode, kind: safeKind(error)});
            throw error;
          }
          originalPromise.then(() => {
            attempt.terminal = 'resolved'; record('loader_resolved', detail());
          }, error => {
            attempt.terminal = 'rejected'; attempt.safeModuleCode = error?.message === 'desktop_module_unavailable';
            record('loader_rejected', {...detail(), synchronous: false, safeModuleCode: attempt.safeModuleCode, kind: safeKind(error)});
          });
          return originalPromise;
        };
      }
      if (route.children) visit(route.children);
    }
  };
  visit(args[0]);
  try { item.router = Reflect.apply(realCreateHashRouter, this, args); }
  catch (error) { record('router_create_rejected', {routerSeq: item.seq, kind: safeKind(error)}); throw error; }
  record('router_created', {routerSeq: item.seq, returnedOriginalRouter: true});
  stateReceipt(item);
  item.unsubscribe = item.router.subscribe(() => stateReceipt(item));
  record('router_subscribed', {routerSeq: item.seq});
  return item.router;
}
