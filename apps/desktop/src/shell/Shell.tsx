import { NavLink, Outlet } from "react-router";
import type { DesktopModuleContribution } from "../modules/registry";
import type { RuntimeSnapshot, Theme } from "../shared/contracts";

export function Shell({ modules, runtime, theme, privacyMode, onTheme, onPrivacy }: Readonly<{
  modules: readonly DesktopModuleContribution[]; runtime: RuntimeSnapshot; theme: Theme; privacyMode: boolean;
  onTheme(value: Theme): void; onPrivacy(value: boolean): void;
}>) {
  return (
    <main className="shell" data-theme={theme} data-privacy={privacyMode ? "on" : "off"}>
      <header><strong>Maris</strong><span role="status">后端：{runtime.state}</span></header>
      <nav aria-label="模块导航">
        {modules.map((module) => <NavLink key={module.moduleId} to={module.routes[0]?.path ?? "/"}>{module.navigation.label}</NavLink>)}
        <NavLink to="/settings">设置</NavLink>
      </nav>
      <div className="content"><Outlet /></div>
      <aside aria-label="统一 Agent 面板">
        <h2>{modules[0]?.agentPanel.title ?? "毛毛"}</h2>
        <p>Agent 面板占位。不会自动调用模型、创建运行或写入财务数据。</p>
        {privacyMode && <p className="privacy-banner">隐私模式已开启</p>}
      </aside>
      <footer className="quick-settings">
        <label>主题 <select aria-label="主题" value={theme} onChange={(event) => onTheme(event.target.value as Theme)}>
          <option value="system">跟随系统</option><option value="light">浅色</option><option value="dark">深色</option><option value="high_contrast">高对比</option>
        </select></label>
        <label><input type="checkbox" checked={privacyMode} onChange={(event) => onPrivacy(event.target.checked)} />隐私模式</label>
      </footer>
    </main>
  );
}

export function EmptyModulePage() { return <section><h1>模块尚未连接</h1><p>连接本地 Host 后，可用模块会出现在导航中。</p></section>; }
export function SettingsPage() { return <section><h1>设置</h1><p>设备设置保存在本机；不会保存密码、令牌、nonce 或消息正文。</p></section>; }
export function RouteErrorBoundary() { return <section role="alert"><h1>页面暂时无法打开</h1><p>请重试。错误详情已安全隐藏。</p><button type="button" onClick={() => location.reload()}>重试</button></section>; }
