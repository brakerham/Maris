# P4-B7 Windows Shell 执行说明与阻塞交付

- 任务：`P4-B7`
- 角色：执行智能体
- 状态：`blocked / finished`
- 依据：`P4-IF-003`
- 最终结论：实现、自测、unsigned package 和 packaged smoke 已形成可审阅现场；供应链门禁发现冻结 Forge 依赖链中的 critical/high 漏洞，且 `extract-zip` 的两项 high 没有已发布修复版本，因此没有提交为 `review`，没有启动 P4-C12。

## 1. 起点与文件边界

固定输入 `docs/coordination/snapshots/p4-b7-start.sha256` 在开始时逐项复算：113 matched、0 mismatch、0 missing，清单摘要为 `1cf5603e86d4f9eccb3240feafda7443f5d9c9c610afc738707909c4e0581d02`。

终点复算为：110 unchanged、3 changed、0 missing、0 invalid。三份起点文件变化都在任务卡允许的窄 Python 接线范围：

| 文件 | 起点 SHA-256 | 终点 SHA-256 |
| --- | --- | --- |
| `src/wife_system/api/app.py` | `8ec05220b3483c6a6ea73ce231064204847635a6a6c1b9f9d70ecc9c8ccfa7e3` | `427b184b1920fc27737a57e5962ffd1db42bf7fa12c7a7c50842d53b5aa64124` |
| `src/wife_system/api/host_routes.py` | `7afcb0ed20618a7e8e66f14b94aa6dbd881505c8835afee4ae5aa291627c94e8` | `62aa8c4a44ae50763dbe6dd1e3ebb2011aa656694b4d297e803146b0a08f5724` |
| `src/wife_system/api/production.py` | `6abcf39bb7ba882f1ab938fb043dfd02242c858a33d1197102536dd20910cb6f` | `397ea70660780b631e8780503661875a9a275e66d679a0d6cdb073c6a6fd0c23` |

66 份实现、配置、生成物和执行方测试的逐文件摘要写入 `apps/desktop/b7-source.sha256`。该有序清单自身 SHA-256 为：

```text
P4-B7-SOURCE-SHA256:de1f80c566faf165d7869bb4641477b3743bea80b72c65f137079e0f3993352a
entries=66
```

`b7-source.sha256` 自身是第 67 份桌面交付文件，不递归包含自己。本文和执行角色日志是交付证据文件，也不进入源码清单。预先存在且未跟踪的 `.claude/**` 未读取或修改；独立测试、矩阵、migration、Finance、Agent、activity import、Host 业务实现、control、overview 和其他角色文件均未修改。未执行任何 Git 写操作。

## 2. 工具链、锁文件和供应链控制

| 组件 | 固定版本 |
| --- | --- |
| Node.js | `24.21.0` |
| Electron | `44.4.5` |
| React / React DOM | `19.3.0` |
| TypeScript | `6.0.3` |
| pnpm | `12.7.0` |
| Electron Forge 核心与插件 | `7.11.2` |
| Vite | `7.3.6` |
| React Router | `8.4.0` |

系统 Node 26.8.1 和 pnpm 11.7.0 不符合冻结值。执行时使用工作区临时 `.b7-tools`：官方 Node ZIP `node-v24.21.0-win-x64.zip` 的 SHA-256 为 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`；项目级 npm 包 `pnpm@12.7.0` 的 `package.json` SHA-256 为 `9bdc25a9aeca0318030cc4532572938e0b3a6d9d70a6ed8ec04f4e0f26c0c9d6`。没有修改系统 PATH 或全局安装。临时工具链和缓存在收口时已删除。

`.npmrc` 保留 `node-linker=hoisted`；pnpm 12 的对应 workspace 设置也固定为 `nodeLinker: hoisted`。所有直接依赖是精确版本。生命周期 allowlist 只有 `electron` 和 `esbuild`，`blockExoticSubdeps: true` 保持开启。

Forge 7.11.2 的 `@electron/rebuild@3.7.2` 固定引用 Electron 官方 node-gyp 提交 `06b29aafb7708acef8b3669835c8a7857ebc92d2`。由于 pnpm 12 会阻止 Git 传递依赖，项目把该精确提交归档为本地 vendor 文件；归档 SHA-256 为 `f357931ae77e0e49f2044de30a75f5bb096fc76948e5baa26c29aa0fac285f31`。没有关闭传递来源拦截。

Electron 官方 GitHub 资产下载两次出现 `fetch failed`，随后从 npm 镜像取得相同 44.4.5 Windows x64 归档，并由 Electron npm 包内置官方 SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` 校验通过。

锁文件 SHA-256：`426249eaff7a8e60b5ad68d0ab9532adf29322559de4423fe500012260780441`。

### 阻塞门禁

`pnpm audit --audit-level high` 退出 1：16 vulnerabilities，分布为 1 critical、11 high、3 moderate、1 low。主要失败包括：

- `tar` 的 critical/high 路径，来自冻结的 Forge / `@electron/rebuild` / Electron node-gyp 构建链；`tar >= 7.5.21` 已有修复版本，但任务停止后没有自行加入 override。
- `extract-zip <= 2.0.1` 的两项 high 路径，来自冻结的 `@electron/packager`；审计明确显示 `Patched versions: None`。

这些是构建/打包依赖路径，不是 renderer 运行时权限，但任务卡把“依赖供应链高危”定义为 P0 停止条件。执行方不能自行替换冻结的 Forge 工具链、忽略 advisory 或把失败改写成 warning，因此任务停在 `blocked / finished`。

## 3. 实际架构与数据流

已形成的桌面边界：

```text
renderer
  -> 固定 window.maris / window.companion API
  -> preload 的固定 channel
  -> main 的 sender + main-frame + origin + strict tuple/object 校验
  -> main-only HostClient / LocalOwnerSession / Supervisor / outbox ports
  -> FastAPI HTTP
```

main 独占 BrowserWindow、Tray、外链、设置文件、safeStorage、outbox 和进程控制。preload 不暴露 `ipcRenderer`、任意 channel、Node、文件、token、nonce、Host URL 或 PID。renderer 使用 sandbox/contextIsolation、关闭 nodeIntegration，生产 CSP 包含 `connect-src 'none'`。主/毛毛 preload 分离，毛毛只获得读取安全状态和打开主窗口两个动作。

Python 窄扩展只增加 managed desktop readiness gate：普通 `/healthz` 和非桌面 `/readyz` 保持兼容；显式 managed profile 的 `/readyz` 要求 `X-Maris-Startup-Nonce`，缺失和错误分别返回稳定 code，响应不回显 nonce。nonce 不替代 Host Bearer 认证。

OpenAPI 由 production route graph 离线导出，规范化 JSON 和 `openapi-typescript` 生成物均 checked in；`check:generated` 在临时目录重生成并逐字比较。运行时不下载 schema。

## 4. 七个里程碑结果

| 里程碑 | 结果 | 主要位置 |
| --- | --- | --- |
| 1 工具链与安全空壳 | 已实现并 package 成功 | 根 workspace；`apps/desktop/forge.config.ts`；main/preload/renderer；security tests |
| 2 OpenAPI 与模块交集 | 已实现 | `tools/openapi/`；`openapi/host.openapi.json`；`src/generated/host-api.ts`；module registry / daily contribution |
| 3 IPC、设备设置与本地 owner | 核心类和测试已实现；main 的 Host 登录编排尚未接入真实 Host | `ipc-contract.ts`、`device-settings.ts`、`secure-store.ts`、`owner-session.ts` |
| 4 Supervisor 与 outbox | 核心类、nonce readiness 和测试已实现；main 当前安全显示 backend 未配置，未接入真实 managed Python 启动 | `backend-supervisor.ts`、`outbox.ts`、`desktop_runtime.py` |
| 5 Shell 与主题 | 已实现占位 Shell | `src/shell/`、renderer、daily placeholder；三栏/断点/主题/privacy/reduced motion |
| 6 Tray 与毛毛 | 已实现自动化基础 | single instance、Tray、close policy、登录项 adapter、唯一 CompanionController、七子状态、DIP clamp |
| 7 固定交付 | package、E2E 和 exe smoke 通过；供应链审计 P0 失败 | 本文、源码摘要、ignored unsigned package |

main 的 `/modules` IPC 当前 fail closed 返回空列表，因此 packaged UI 显示“模块尚未连接”；不会伪造 Host 模块或财务数据。LocalOwnerSession、HostClient 和 BackendSupervisor 已有严格实现与执行方测试，但尚未由 main 组合成真实 managed Host 正常链路。该缺口不能在供应链 P0 出现后继续实现或宣称完成。

## 5. 执行方测试证据

| 组 | 结果 |
| --- | --- |
| pnpm peer dependency check | 通过，0 issues |
| OpenAPI `check:generated` | 通过，schema 与 TypeScript 生成物零漂移 |
| TypeScript `tsc --noEmit` | 通过 |
| 桌面 lint | 通过 |
| Vitest unit/component/IPC | 9 files，16 passed，0 failed，0 skipped |
| Python定向 Host | 15 passed，0 failed，0 skipped；1 个 Starlette/AnyIO deprecation warning |
| Python compileall | 退出 0 |
| 自有 Uvicorn health smoke | `/healthz` 200；精确 owned PID 正常停止 |
| Forge unsigned package | 通过 |
| packaged `app.asar` Playwright E2E | 1 passed，0 failed；815 ms；结束后 owned residual 0 |
| 最终 `Maris.exe` smoke | 退出 0；未超时；测试专用 2 秒自退出 |
| 供应链 audit | **失败**：1 critical、11 high、3 moderate、1 low |

执行中保留的非通过证据：初次 `forge package` 分别暴露旧 pnpm shim、pnpm 12 workspace 配置、旧 node_modules 布局、main/preload 同名输出和沙箱外 Electron cache 问题，均修复后 package 通过。Playwright 直接连接 fuse 后的 `Maris.exe` 两次在 launch 阶段超时；trace 明确定位后改为对最终 package 中 `app.asar` 做 Playwright E2E，并另用最终 `Maris.exe` 做自退出 smoke。一次 E2E 发现 renderer 输出落在 source root 导致两个空白窗口，修正 Vite outDir 后通过。Playwright 有一条 `NO_COLOR` 被 `FORCE_COLOR` 覆盖的非产品 warning。pnpm 报告 8 个 deprecated transitive dependencies。

## 6. P4-B 24 项执行方证据映射

以下只是执行方证据，矩阵状态仍保持 `not_run`，由 P4-C12 独立更新：

| 矩阵 ID | 执行方证据 |
| --- | --- |
| P4B-SEC-01 | security unit + packaged renderer Node/process 探测通过 |
| P4B-SEC-02 | CSP、navigation/window deny、固定外链 ID；静态/unit，完整攻击 E2E 待 C12 |
| P4B-SEC-03 | 主/毛毛 preload 固定 API；无 raw IPC |
| P4B-SEC-04 | IPC sender/origin/main-frame/schema/extra 字段反例 unit 通过 |
| P4B-SEC-05 | safeStorage fail-closed、renderer API 无 secret；真实内存/Crash dump 检查未验证 |
| P4B-SEC-06 | Python nonce API unit 通过；远程地址/完整 Host 绕过 E2E 未验证 |
| P4B-SEC-07 | hostile HTML/RTL text-node component 通过；超长 Windows 视觉未验证 |
| P4B-SEC-08 | 安全 error UI 已实现；故障注入覆盖不完整 |
| P4B-SUP-01 | owned child identity/nonce/handle pure unit；真实树停止未验证 |
| P4B-SUP-02 | nonce/timeout 状态代码和真实 owned health child smoke；端口冲突组合未完整验证 |
| P4B-SUP-03 | 有界恢复/backoff unit；真实 online crash 未验证 |
| P4B-SUP-04 | external_dev 不停止 unit；第二实例 packaged 行为未完整自动化 |
| P4B-SUP-05 | 自有 Uvicorn、E2E 和 exe smoke 均 residual 0；系统注销 manual 未验证 |
| P4B-SUP-06 | outbox stable ID/restart/capacity/encryption unit 通过；真实 Host 恢复提交未接线 |
| P4B-UI-01 | registry/Host 交集 unit 通过 |
| P4B-UI-02 | lazy route/error UI 已实现；失败后成功的完整 E2E 未验证 |
| P4B-UI-03 | generated diff + tsc 通过 |
| P4B-UI-04 | strict contribution/extra/conflict unit 通过 |
| P4B-CMP-01 | packaged E2E 证明窗口总数上限与单一 companion；完整状态流未验证 |
| P4B-CMP-02 | close hint/setting 实现；真实两次关闭/Tray 恢复未验证 |
| P4B-CMP-03 | 三策略控制实现；完整交互 E2E 未验证 |
| P4B-CMP-04 | 默认 false、只改 Maris 登录项；Windows 注册表人工证据未验证 |
| P4B-CMP-05 | bounds clamp/privacy/键盘基础；多屏/DPI/拔屏/全屏人工证据未验证 |
| P4B-CMP-06 | 主题/高对比/reduced motion/普通迷你窗合同；透明/GPU 设备人工证据未验证 |

## 7. 运行方式

在供应链裁定前不建议重新安装依赖。若总控/技术顾问形成新冻结并关闭 advisory，开发命令为：

```powershell
pnpm install --frozen-lockfile
pnpm desktop:typecheck
pnpm desktop:lint
pnpm desktop:test
pnpm check:generated
pnpm desktop:dev
pnpm desktop:package
```

保留的 unsigned package：`apps/desktop/out/Maris-win32-x64/Maris.exe`，大小 246032896 bytes，SHA-256 `15abf2f04e6d59ea9f0f5217f457a4452f0282e12f4fdebb9fb776c31167d878`。最终 `app.asar` 大小 740053 bytes，SHA-256 `6b11806a1d47adb3ea79142adcd0cd797bfc280ce6344d8cc471b088283b4d97`。`apps/desktop/.gitignore` 排除 package、构建缓存和测试 trace，避免总控误提交二进制。

## 8. 资源收口与下一步

- 本任务启动的 Uvicorn、Electron、Maris 和 Playwright 进程均已退出；最终 owned residual 为 0。
- 未启动 Docker、PostgreSQL、OpenClaw、微信或 DeepSeek。
- `.b7-tools`、根 pnpm store、root node_modules、测试 profile、trace 和错误 renderer 构建目录均已删除。
- unsigned package 按任务要求保留，源码和 package 证据均不含真实密钥或个人数据。
- Windows 人工项保持 `unverified`：Tray 真实交互、开机项、系统注销、100/125/150% DPI、多显示器/拔屏、外部全屏、透明/GPU 降级、高对比和 reduced motion 设备证据。

下一步必须回到头脑风暴总控和技术顾问：裁定冻结 Forge 7.11.2 下的 `tar` override 与无 patched release 的 `extract-zip` advisory，形成新的固定输入或安全例外；随后由新的执行任务完成 main 对 LocalOwnerSession/BackendSupervisor/HostClient 的真实组合并重跑完整门禁。当前不得派发 P4-C12，因为 B7 尚未形成可接受的稳定产品快照。
