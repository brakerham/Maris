import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { createHashRouter, Navigate, RouterProvider } from "react-router";
import { dailyFinanceContribution } from "../modules/daily-finance/contribution";
import { compileRegistry, intersectModules, type HostModuleSummary } from "../modules/registry";
import { EmptyModulePage, RouteErrorBoundary, SettingsPage, Shell } from "../shell/Shell";
import type { RuntimeSnapshot, Theme } from "../shared/contracts";
import "./styles.css";

const compiled = compileRegistry([dailyFinanceContribution]);
const offline: RuntimeSnapshot = { state: "stopped", mode: "managed", authenticated: false, errorCode: null };

function DesktopApp() {
  const [runtime, setRuntime] = useState(offline);
  const [hostModules, setHostModules] = useState<readonly HostModuleSummary[]>([]);
  const [theme, setTheme] = useState<Theme>("system");
  const [privacyMode, setPrivacyMode] = useState(false);
  useEffect(() => {
    void window.maris.runtime.getSnapshot().then(setRuntime);
    void window.maris.modules.list().then(setHostModules);
    return window.maris.runtime.subscribe(setRuntime);
  }, []);
  const modules = useMemo(() => intersectModules(compiled, hostModules), [hostModules]);
  const router = useMemo(() => createHashRouter([{
    path: "/", element: <Shell modules={modules} runtime={runtime} theme={theme} privacyMode={privacyMode} onTheme={(value) => { setTheme(value); void window.maris.settings.update({ theme: value }); }} onPrivacy={(value) => { setPrivacyMode(value); void window.maris.settings.update({ privacyMode: value }); }} />,
    errorElement: <RouteErrorBoundary />,
    children: [
      { index: true, element: modules.length ? <Navigate to={modules[0]!.routes[0]!.path} replace /> : <EmptyModulePage /> },
      ...modules.flatMap((module) => module.routes.map((route) => ({ path: route.path, lazy: async () => ({ Component: (await import("../modules/daily-finance/DailyFinancePage")).default }) }))),
      { path: "settings", element: <SettingsPage /> }
    ]
  }]), [modules, privacyMode, runtime, theme]);
  return <RouterProvider router={router} />;
}

createRoot(document.getElementById("root")!).render(<StrictMode><DesktopApp /></StrictMode>);
