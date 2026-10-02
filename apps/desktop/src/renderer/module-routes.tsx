import { Component, createContext, useContext, useEffect, useMemo, useRef, useState, type ComponentProps, type ComponentType, type ReactNode } from "react";
import { createHashRouter, Navigate, RouterProvider, useLoaderData, useRevalidator, type RouteObject } from "react-router";
import { intersectModules, type DesktopModuleContribution, type HostModuleSummary } from "../modules/registry";
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

function ModuleIndex() {
  const state = useContext(ShellStateContext);
  const firstPath = state?.modules[0]?.routes[0]?.path;
  return firstPath ? <Navigate to={firstPath} replace /> : <EmptyModulePage />;
}

export function DesktopApp({ registry, loaders = builtinPageLoaders }: Readonly<{
  registry: readonly DesktopModuleContribution[]; loaders?: ModulePageLoaders;
}>) {
  const [runtime, setRuntime] = useState<RuntimeSnapshot>({ state: "stopped", mode: "managed", authenticated: false, errorCode: null });
  const [hostModules, setHostModules] = useState<readonly HostModuleSummary[] | null>(null);
  const [theme, setTheme] = useState<Theme>("system");
  const [privacyMode, setPrivacyMode] = useState(false);
  const [router, setRouter] = useState<ReturnType<typeof createHashRouter> | null>(null);

  useEffect(() => {
    let active = true;
    void window.maris.runtime.getSnapshot().then((value) => { if (active) setRuntime(value); });
    void window.maris.modules.list().then((value) => { if (active) setHostModules(value); });
    const unsubscribe = window.maris.runtime.subscribe((value) => { if (active) setRuntime(value); });
    return () => { active = false; unsubscribe(); };
  }, []);

  const modules = useMemo(() => intersectModules(registry, hostModules ?? []), [registry, hostModules]);
  useEffect(() => {
    if (hostModules === null) return;
    const next = createHashRouter([{
      path: "/", element: <ConnectedShell />, errorElement: <RouteErrorBoundary />,
      hydrateFallbackElement: <ConnectedShell />,
      children: [
        { index: true, element: <ModuleIndex /> },
        ...createModuleRoutes(modules, loaders),
        { path: "settings", element: <SettingsPage /> }
      ]
    }]);
    setRouter(next);
    return () => { next.dispose(); };
  }, [modules, loaders, hostModules]);

  const state: ShellState = { modules, runtime, theme, privacyMode,
    onTheme: (value) => { setTheme(value); void window.maris.settings.update({ theme: value }); },
    onPrivacy: (value) => { setPrivacyMode(value); void window.maris.settings.update({ privacyMode: value }); } };
  return <ShellStateContext.Provider value={state}>
    {router ? <RouterProvider router={router} /> : <p role="status">正在打开页面</p>}
  </ShellStateContext.Provider>;
}
