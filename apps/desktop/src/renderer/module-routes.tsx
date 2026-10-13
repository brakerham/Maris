import { Component, createContext, useContext, useEffect, useRef, useState, type ComponentProps, type ComponentType, type ReactNode } from "react";
import { createHashRouter, Navigate, RouterProvider, useLoaderData, useRevalidator, type RouteObject } from "react-router";
import { intersectModules, type DesktopModuleContribution } from "../modules/registry";
import { EmptyModulePage, RouteErrorBoundary, SettingsPage, Shell } from "../shell/Shell";
import type { RuntimeSnapshot, Theme } from "../shared/contracts";

export type ModulePageLoader = () => Promise<ComponentType>;
export type ModulePageLoaders = Readonly<Record<string, ModulePageLoader>>;

const builtinPageLoaders: ModulePageLoaders = Object.freeze({
  daily_finance_home: async () => (await import("../modules/daily-finance/DailyFinancePage")).default
});

// React's default caught-error logger includes the original error and stack.
// The visible local/root fallback remains responsible for presenting failures.
export const rendererRootOptions = { onCaughtError: () => { console.error("desktop_render_unavailable"); } };

type PageData = Readonly<{ Page: ComponentType; attempt: number }>;

function useModuleRetry() {
  const revalidator = useRevalidator();
  const inFlight = useRef(false);
  const [pending, setPending] = useState(false);
  const retry = async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    setPending(true);
    try { await revalidator.revalidate(); }
    finally { inFlight.current = false; setPending(false); }
  };
  return { onRetry: () => { void retry(); }, isRetrying: pending || revalidator.state === "loading" };
}

function ModuleLoadError() {
  return <RouteErrorBoundary {...useModuleRetry()} />;
}

class ModuleRenderBoundary extends Component<Readonly<{
  children: ReactNode; onRetry: () => void; isRetrying: boolean;
}>, { failed: boolean }> {
  override state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  override render() {
    return this.state.failed
      ? <RouteErrorBoundary onRetry={this.props.onRetry} isRetrying={this.props.isRetrying} />
      : this.props.children;
  }
}

function ModulePage() {
  const { Page, attempt } = useLoaderData() as PageData;
  const retry = useModuleRetry();
  return <ModuleRenderBoundary key={attempt} {...retry}><Page /></ModuleRenderBoundary>;
}

export function createModuleRoutes(
  modules: readonly DesktopModuleContribution[], loaders: ModulePageLoaders = builtinPageLoaders
): RouteObject[] {
  return modules.flatMap((module) => module.routes.map((route): RouteObject => {
    let attempt = 0;
    return {
      id: `module_route:${route.routeId}`, path: route.path,
      loader: async () => {
        const currentAttempt = ++attempt;
        try {
          if (!Object.hasOwn(loaders, route.routeId)) throw new Error("desktop_module_unavailable");
          const Page = await loaders[route.routeId]!();
          return { Page, attempt: currentAttempt } satisfies PageData;
        } catch {
          // A failed import may contain a chunk URL, path or secret. Router only
          // receives a stable safe error; no raw exception enters DOM/logs.
          throw new Error("desktop_module_unavailable");
        }
      },
      element: <ModulePage />, errorElement: <ModuleLoadError />
    };
  }));
}

type ShellState = ComponentProps<typeof Shell>;
const ShellStateContext = createContext<ShellState | null>(null);

function ConnectedShell() {
  const state = useContext(ShellStateContext);
  if (!state) throw new Error("desktop_shell_unavailable");
  return <Shell {...state} />;
}

function ModuleIndex({ modules }: Readonly<{ modules: readonly DesktopModuleContribution[] }>) {
  // The index belongs to this router's route set, not a newer Shell context.
  const firstPath = modules[0]?.routes[0]?.path;
  return firstPath ? <Navigate to={firstPath} replace /> : <EmptyModulePage />;
}

export function DesktopApp({ registry, loaders = builtinPageLoaders }: Readonly<{
  registry: readonly DesktopModuleContribution[]; loaders?: ModulePageLoaders;
}>) {
  const [runtime, setRuntime] = useState<RuntimeSnapshot>({ state: "stopped", mode: "managed", authenticated: false, errorCode: null });
  const [modules, setModules] = useState<readonly DesktopModuleContribution[] | null>(null);
  const [theme, setTheme] = useState<Theme>("system");
  const [privacyMode, setPrivacyMode] = useState(false);
  const [router, setRouter] = useState<{ instance: ReturnType<typeof createHashRouter>; revision: number } | null>(null);

  useEffect(() => {
    let active = true;
    let notifications = 0;
    let requested = 0;
    let reading = false;
    const readModules = async () => {
      if (!active || reading) return;
      reading = true;
      const generation = requested;
      try {
        const summaries = await window.maris.modules.list();
        if (active && generation === requested) {
          const next = intersectModules(registry, summaries);
          // Contribution identity/order is the actual route contract. Fresh or
          // irrelevant Host summaries must not reset a route or retry its page.
          setModules((current) => current?.length === next.length && current.every((item, index) => item === next[index]) ? current : next);
        }
      } catch {
        // No raw bridge error enters the DOM/logs; retain a working intersection.
        if (active && generation === requested) setModules((current) => current ?? []);
      } finally {
        reading = false;
        // Only an intervening ready notification can request another read.
        if (active && generation !== requested) void readModules();
      }
    };
    const requestModules = () => { requested++; void readModules(); };
    const unsubscribe = window.maris.runtime.subscribe((value) => {
      if (!active) return;
      notifications++;
      setRuntime(value);
      // Composition can publish equal fields before and after assigning modules.
      // Offline observation alone must not clear a usable route or query again.
      if (value.state === "online" && value.authenticated) requestModules();
    });
    void (async () => {
      try {
        const value = await window.maris.runtime.getSnapshot();
        if (active && notifications === 0) setRuntime(value);
      } catch { /* A later subscription notification remains authoritative. */ }
    })();
    if (requested === 0) requestModules();
    return () => { active = false; unsubscribe(); };
  }, [registry]);

  useEffect(() => {
    if (modules === null) return;
    const next = createHashRouter([{
      path: "/", element: <ConnectedShell />, errorElement: <RouteErrorBoundary />,
      hydrateFallbackElement: <ConnectedShell />,
      children: [
        { index: true, element: <ModuleIndex modules={modules} /> },
        ...createModuleRoutes(modules, loaders),
        { path: "settings", element: <SettingsPage /> },
        // A previously selected module may leave the effective intersection.
        { path: "*", element: <EmptyModulePage /> }
      ]
    }]);
    // RouterProvider retains match/loader state; a different route set needs a
    // fresh provider. Equal intersections never reach this effect.
    setRouter((current) => ({ instance: next, revision: (current?.revision ?? 0) + 1 }));
    return () => { next.dispose(); };
  }, [modules, loaders]);

  const state: ShellState = { modules: modules ?? [], runtime, theme, privacyMode,
    onTheme: (value) => { setTheme(value); void window.maris.settings.update({ theme: value }); },
    onPrivacy: (value) => { setPrivacyMode(value); void window.maris.settings.update({ privacyMode: value }); } };
  return <ShellStateContext.Provider value={state}>
    {router ? <RouterProvider key={router.revision} router={router.instance} /> : <p role="status">正在打开页面</p>}
  </ShellStateContext.Provider>;
}
