# P4-IF-003：Windows Shell、毛毛与模块 UI 接口冻结

- 冻结编号：`P4-IF-003`
- 冻结时间：2026-09-27，Asia/Shanghai
- 所属切片：P4-B Windows Shell、模块 UI、桌面生命周期与毛毛
- 输入：[P4-B 头脑风暴](phase-4-b-windows-shell-brainstorm.md)、[P4-D11 技术方案](phase-4-d11-windows-shell-technical-advice.md)、[D11 总控审阅](p4-d11-coordinator-review.md)、[P4 测试矩阵](testing/phase-4-modular-agent-host-test-matrix.md)
- 状态：`frozen`

本文是 P4-B7 实现和 P4-C12 独立验收的唯一桌面合同。与较早讨论稿、D11 中已勘误的版本表述或实现者偏好冲突时，以本文为准。架构或范围变化必须退回头脑风暴总控和技术顾问，执行智能体不得自行替换核心方案。

## 1. 产品范围

P4-B 交付一个可以在 Windows 上运行的 Maris 桌面壳，证明以下能力：

1. 安全的 Electron main/preload/renderer 三层边界；
2. 模块贡献注册、后端模块交集和 lazy route；
3. 自动本地 owner 会话和 main-only Host HTTP；
4. 可管理或连接 Python Host 的 `BackendSupervisor`；
5. 加密设备设置和离线 outbox；
6. 主窗口、Tray、单实例、主题和统一 Agent 面板空壳；
7. 只有一个毛毛窗口，模块形态与运行子状态分离；
8. 可复现开发、测试和 unsigned Windows package。

P4-B 不实现：

- 公众注册、第二用户、多租户服务器、云账户、找回密码或常规登录页；
- 真实财务驾驶舱、完整账本管理、聊天写账和确认闭环；
- 真实财富管理、行情、持仓、股票推荐或投资建议；
- Android 应用；手机继续通过微信通道；
- 正式安装器、代码签名、自动更新和发行账号；
- 图表库和真实图表；P4-B 只定义 `ChartAdapter` 接口；
- PyInstaller/Nuitka 等 Python sidecar 正式捆绑。

P4-C 负责日常财务驾驶舱、账本可视化和同一 Agent Host 下的桌面对话；P4-D 负责财富管理、投资学习和行情等独立模块。P4-B 页面只能使用清楚标注的虚拟占位或能力状态，不得伪造真实余额、建议、持仓或行情。

## 2. 精确工具链基线

| 组件 | 冻结值 | 规则 |
| --- | --- | --- |
| 开发 Node.js | `24.21.0` | 写入 `.node-version`；与 Electron 44.4.5 内置 Node 同代 |
| Electron | `44.4.5` | 精确 pin；安全 patch 升级另立快照 |
| React / React DOM | `19.3.0` | 精确 pin |
| TypeScript | `6.0.3` | 有意选择的兼容基线，不宣称是最新版本 |
| pnpm | `12.7.0` | 根 `packageManager` 精确固定 |
| Electron Forge | `7.11.2` | 所有 Forge 核心和 plugin 包保持同一精确版本 |
| Forge Vite plugin | `7.11.2` | 接受官方标记的 experimental 状态，精确 pin |
| Vite | `7.3.6` | 精确 pin，不在 P4-B 直接采用 Vite 8 |
| React Router | `8.4.0` | 使用 `createHashRouter` 与 lazy route |

TypeScript 7.0 已经发布，但 7.0 尚不提供稳定 compiler API；依赖编译器 API 的工具仍可能需要 6.0。本切片先使用 6.0.3，等 TypeScript 7.1 或实际依赖矩阵明确兼容后另立升级任务。不得在 B7 中同时安装 TS 7 和 TS 6 形成双编译器路径。

根 `.npmrc` 必须至少包含：

```ini
node-linker=hoisted
```

这是 Electron Forge 使用 pnpm 时的官方要求。生命周期安装脚本采用显式 allowlist，只允许经审查的 Electron/构建依赖；未知依赖不得自动执行安装脚本。核心依赖不得用 `^` 或 `~`。完整依赖图由 `pnpm-lock.yaml` 固定；B7 报告记录最终直接依赖精确版本和 lockfile 摘要。

采用 Forge Vite plugin 的条件是：开发启动、typecheck、unit/component、Electron E2E 和 `forge package` 在同一固定依赖图下通过。plugin minor/major、Electron major、React minor/major、TypeScript major 和 Vite major 升级必须独立验收，不和业务功能混在同一快照。

## 3. 仓库与目录边界

推荐根结构：

```text
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
.node-version
.npmrc
apps/desktop/
  package.json
  forge.config.ts
  vite.*.config.ts
  tsconfig*.json
  electron/main/
  electron/preload/
  src/shared/
  src/shell/
  src/modules/daily-finance/
  src/companion/
  src/theme/
  tests/
tools/openapi/
```

Python 代码继续位于 `src/wife_system/**`。桌面代码不得 import Python 内部模块；Python 也不得 import Electron 构建产物。二者只通过冻结的 HTTP/OpenAPI 合同交互。

## 4. Electron 安全边界

### 4.1 main

main 是桌面组合根，独占：

- Host HTTP、access/refresh token、本地 owner 凭据；
- safeStorage、设备设置、加密 outbox；
- Python 子进程和 `BackendSupervisor`；
- BrowserWindow、Tray、外链、single-instance、登录启动项；
- 毛毛 `CompanionController`；
- IPC handler 注册、sender/origin/window 与参数校验。

### 4.2 preload

preload 只通过 `contextBridge` 公开冻结的判别联合 API。它不得暴露：

- 原始 `ipcRenderer`、任意 channel、`send` 或 `invoke`；
- Node `require`、`process`、`fs`、`child_process`、文件路径；
- token、凭据、nonce、Host URL、PID 或内部异常；
- 通用文件读写、shell 命令或任意 URL 打开能力。

### 4.3 renderer

所有 renderer 都必须启用 `sandbox` 和 `contextIsolation`，关闭 `nodeIntegration`。生产 CSP 默认：

```text
default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'
```

若本地打包资源要求更窄或等价调整，必须由测试证明没有扩大网络和脚本能力。renderer 不直接访问 Host、数据库、网络、文件系统或进程。生产数据流固定为：

```text
renderer -> typed preload -> validated main IPC -> Host HTTP -> FastAPI
```

未知导航、新窗口、`javascript:`、未登记外链、subframe sender 和错误 origin 一律拒绝。获准外链由 main 的固定 ID allowlist 打开到系统浏览器，不能把任意 renderer 字符串传给 shell。

## 5. 模块 UI 合同

桌面定义并运行时严格验证 `DesktopModuleContribution`，至少包含：

```ts
interface DesktopModuleContribution {
  readonly moduleId: ModuleId;
  readonly version: `${number}.${number}.${number}`;
  readonly hostUiMajor: 1;
  readonly expectedApiPrefixes: readonly `/api/v1/${string}`[];
  readonly navigation: NavigationContribution;
  readonly routes: readonly LazyRouteContribution[];
  readonly agentPanel: AgentPanelContribution;
  readonly settings: readonly ModuleSettingContribution[];
  readonly companion: CompanionContribution;
}
```

编译注册必须 fail closed，并检查：

- module ID、Profile ID、SemVer 使用与 Python 合同相同的 ASCII 语法，不自动 trim、lowercase 或 Unicode 归一化；
- `hostUiMajor === 1`；
- module、Profile、route、setting 和 appearance 全局唯一；
- contribution module major 与 Host `/modules` 返回的 module major 相同；
- Profile 和 API prefix 都属于后端摘要；
- settings schema version 首版要求精确相等；
- 任一冲突时不部分加载。

导航只显示 compiled registry 与 `/api/v1/modules` 的兼容交集。未知、后端禁用、桌面缺失或版本不兼容模块不导航、不预加载、不调用 Profile。Shell、main 和 preload 都不得出现针对 `daily_finance`、`wealth_management` 等具体 module ID 的业务分支；业务差异来自 contribution。

P4-B 只登记 `daily_finance` 的安全占位 contribution。可用第二个纯测试 contribution 证明扩展性，不实现真实 wealth 模块。

## 6. OpenAPI 和类型来源

FastAPI DTO 的唯一类型来源是仓库内 production app 的 OpenAPI：

1. 使用受控 Python 命令调用正式 `create_app().openapi()`；
2. 规范化并输出 checked-in JSON；
3. 使用精确 pin 的 `openapi-typescript` 生成 TypeScript `paths`；
4. 使用 `openapi-fetch` 建立 main-only client；
5. `check:generated` 在临时目录重生成并比较；
6. Pydantic required/enum/field 漂移必须使生成检查或 `tsc` 失败。

运行时禁止下载 Schema。不得手写一套平行的 Host DTO 掩盖漂移。IPC、设备设置、窗口、outbox 和 UI contribution 不属于 FastAPI DTO，必须手写严格合同并做运行时校验。

## 7. 本地 owner 会话

桌面没有登录页。main 按以下顺序建立单主人会话：

1. 读取并解密本机 owner 凭据与 refresh token；
2. 若有 refresh token，执行 single-flight refresh；
3. refresh 失效但本地 owner 凭据可用时调用现有 login；
4. 数据库未初始化时，main 生成随机高熵 `local_owner` 凭据，先成功写入 safeStorage 临时 blob，再调用 initialize；
5. 初始化成功后原子提升本地凭据状态；失败时不得留下无法恢复的半初始化本地状态；
6. access token 只驻留 main 内存，refresh token 与 owner 凭据只以 safeStorage 加密形式持久化；
7. 并发 401 只触发一次 refresh，其余请求等待同一 Promise；
8. 用户主动 revoke/logout 后不得静默重新登录，UI 进入明确的 repair 状态。

renderer 只能看到 `authenticated / offline / needs_repair` 等安全状态，不得看到 token、密码或密文。未来应用锁只保护本机解密动作，不改变后端 user/session 模型。

## 8. desktop nonce 与 readiness 窄扩展

P4-B7 可以对 Python Host 做一项窄扩展：受管桌面启动时，Electron main 生成随机 startup nonce，经子进程启动通道传给该实例；Supervisor 的 ready 请求携带 `X-Maris-Startup-Nonce`。只有 nonce 匹配且现有 Host readiness 通过时，Supervisor 才接受该进程。

冻结规则：

- `/healthz` 继续只表示进程存活，不要求 nonce；
- 通用非桌面部署的 `/readyz` 行为保持兼容；
- 只有显式启用 managed desktop profile 时才要求 startup nonce；
- nonce 不写入响应、日志、renderer、设备设置或 crash 文本；
- 错 nonce、缺 nonce、超时和错误实例都返回稳定安全错误；
- nonce 不能替代 Bearer token、loopback 绑定或现有授权；
- Python 改动不得触及 FinanceService、Agent 工具、pending、活动导入或业务幂等语义。

## 9. BackendSupervisor

模式固定为：

- `managed`：桌面启动并拥有 Python 子进程；
- `external_dev`：连接开发者手工启动的 Host，桌面永不取得停止权。

状态固定为：

```text
starting / online / offline / recovering / failed / stopping / stopped
```

参数冻结：

- 只绑定 `127.0.0.1`，端口由系统分配或有限重试选择；
- ready 总上限 30 秒；
- online 后每 5 秒检查一次；
- 5 分钟窗口最多 3 次自动恢复；
- 退避 1、2、4 秒；
- 正常停止预算 5 秒，超时后只处理本实例拥有的子进程树；
- 单实例应用；第二次启动只激活现有主窗口；
- 只有实际 `ChildProcess` 句柄、ownership record、instance ID 和 nonce 全部匹配，才允许停止进程；
- PID 相同、端口相同或服务可访问都不足以证明 ownership；
- 状态变化通过固定 preload 订阅发送安全 snapshot，不透出路径、命令行、PID 或 nonce。

连续失败进入 `failed`，等待用户明确重试。不得无限循环或在失败时偷偷启动 Docker、OpenClaw、DeepSeek 或其他服务。

## 10. 加密 outbox 与幂等

outbox 由 main 独占并用 safeStorage 保护。默认值：

- 最多 20 条；超过上限拒绝新增并提示用户处理，不能静默丢弃；
- terminal 条目在 24 小时后清理；
- 未提交草稿保留 30 天后提示用户确认删除；
- 设置文件只保存 outbox 版本或状态，不保存消息正文。

第一次准备发送时生成并固定 `client_event_id` 和 payload digest。离线、重复点击、响应丢失、应用重启与后端恢复均复用同一 ID；第一次提交后修改正文必须派生新 ID。renderer 不能生成重试 ID或直接决定 terminal 状态。

P4-B 只证明消息保留、ID 稳定和恢复调用基础，不证明 P4-C 的真实自然语言写账闭环。

## 11. 设备设置

设备设置使用版本化严格 JSON Schema、同目录临时文件、flush 后原子替换和损坏文件安全回退。首版至少包含：

- `schemaVersion`；
- `backendMode`；
- `closePolicy`：`hide_to_tray / ask_every_time / quit`；
- `closeHintShown`；
- `theme`：`system / light / dark / high_contrast`；
- `reducedMotion`；
- `privacyMode`；
- `companionVisible`、`companionAlwaysOnTop`、主形态/降级状态；
- 主窗口与毛毛窗口的 DIP bounds、display ID；
- `launchAtLogin`，默认 `false`；
- 外部全屏自动隐藏功能的支持/启用状态；
- outbox 格式版本，不含正文或 secret。

设置文件不得保存 token、owner 密码、API key、nonce、消息正文、账目、模型上下文、原始异常或个人财务数据。写入失败保持上一份有效配置，不把半写文件当成功。

## 12. 主窗口、Tray、主题和布局

- 应用名为 `Maris`。
- 主窗口最小 960×680 DIP；初始三栏断点为 1120/1360 DIP。
- 三栏含模块导航、模块内容、统一 Agent 面板；较窄尺寸按冻结断点折叠，不创建第二套页面状态。
- 首次关闭默认隐藏到 Tray 并只提示一次；之后按 `closePolicy` 执行。
- `ask_every_time` 的取消操作保持应用和状态不变。
- `quit` 走统一退出流程并只清理自有后端。
- 开机启动默认关闭；只有用户明确切换后才创建 Maris 自身启动项，关闭时只移除自己的启动项。
- 主题支持 system/light/dark/high-contrast 与 reduced motion；CSS Modules + semantic CSS custom properties 为唯一主题机制。
- 收入/支出颜色和市场涨/跌颜色使用不同语义 token，不能因红绿习惯复用同一含义。
- 所有文本默认作为 text node 渲染；禁用 raw HTML。

## 13. 单一毛毛合同

全局只有一个 `CompanionController` 和一个毛毛 BrowserWindow。候选初始尺寸为 176×176 DIP。

- 模块 contribution 决定主形态，例如日常管钱和财富管理形态；
- 可信 Host/Supervisor/run 状态决定子状态：`idle / listening / thinking / tool / needs_confirmation / error / offline`；
- 模块切换不创建第二个窗口、第二个 Agent、第二个会话或模型调用；
- 子状态变化不改变模块权限或工具；
- 毛毛可在设置中显示/隐藏、置顶或跟随主窗口策略；主窗口隐藏后是否显示取决于设置；
- 隐私模式不显示金额、消息正文或持仓；
- 键盘与无障碍入口必须能完成显示/隐藏、回到主窗口和关闭提示；
- 透明窗口发生黑底、闪烁、点击错位、无障碍不可达或重复 GPU 崩溃时，降级为普通迷你窗口，合同和单实例不变。

外部应用全屏自动隐藏仅在可审计 adapter 可用且人工证据通过时计为支持；否则显示为不支持并保留手动隐藏。不得为了通过测试引入未经审计的 Win32 二进制。

## 14. 状态归属

| 状态 | 唯一来源 |
| --- | --- |
| 模块、Profile、会话、记忆、模块设置 | FastAPI Host |
| Host 查询缓存 | TanStack Query v5，仅缓存，不成为权威 |
| Supervisor 状态 | Electron main |
| access/refresh token、owner 凭据、nonce | Electron main 内存或 safeStorage |
| 设备设置、窗口、Tray、毛毛、outbox | Electron main |
| 当前路由、面板折叠、输入草稿编辑副本 | renderer |

P4-B 使用 React state/reducer/context 管理普通 UI 状态，不引入 Redux 或 Zustand。任何新全局状态库需要真实跨窗口写入需求和单独评审。

## 15. 测试与证据

执行方自测必须覆盖：

- TypeScript compile、lint、依赖审计与 generated diff；
- Vitest 单元、React Testing Library 组件和 IPC 合同；
- Playwright Electron 的关键自动化路径；
- dev 启动和 unsigned `forge package` smoke；
- P4-A 受影响的 Python定向回归；
- 资源收口：无自有后端、窗口、端口和测试临时目录遗留。

独立验收由 P4-C12 负责，并逐项落地 24 个现有矩阵 ID：

- `P4B-SEC-01～08`；
- `P4B-SUP-01～06`；
- `P4B-UI-01～04`；
- `P4B-CMP-01～06`。

Windows 人工证据至少覆盖 Tray、开机启动、系统注销/退出、多显示器、100%/125%/150% DPI、拔屏、外部全屏支持状态、透明/GPU 降级、高对比和 reduced motion。不能自动化的案例必须明确记录设备、步骤、预期、实际和证据位置，不能直接标为 passed。

执行方只能提交 `review / finished`；测试方只能提交独立 `review / finished`；只有头脑风暴总控可以标记 P4-B `complete`。

## 16. 七个实施里程碑

1. **工具链与安全空壳**：固定 workspace、三层 Electron 配置、开发启动和 package smoke。
2. **OpenAPI 与模块交集**：离线生成、main client、compiled registry、daily placeholder。
3. **IPC、设备设置与本地 owner**：typed preload、运行时校验、safeStorage、single-flight refresh、原子设置。
4. **Supervisor 与 outbox**：managed/external_dev、nonce readiness、有界恢复、加密 outbox、同 ID 重试。
5. **Shell 和主题**：三栏、模块导航、统一 Agent 面板占位、主题、错误边界和断点。
6. **Tray 与毛毛**：单实例、关闭策略、一个毛毛窗口、降级和 Windows 生命周期 adapter。
7. **固定交付**：完整自测、unsigned package、运行说明、有序文件摘要和资源收口。

每个里程碑必须在执行智能体状态文件登记开始、检查点、结果和下一步。遇到同一阻塞连续两个检查点无进展时，停止受影响范围，记录最小错误和已完成工作，交回总控；不得无限重试。

## 17. 变更控制

以下情况必须停止并退回总控：

- 需要改变 P4-A Finance、Agent、pending、memory 或 activity import 业务语义；
- 需要新增公众注册、多用户、云服务或登录页面；
- 需要更换 Electron/Tauri、pnpm/npm、Forge/electron-builder、TypeScript 6/7 双路径；
- 需要 renderer 直接访问 Host、网络、Node 或通用 IPC；
- 需要安装未经审计的原生 helper、关闭安全软件或添加排除项；
- 依赖安全 P0、secret 泄露、错误进程被停止、幂等 ID 漂移或 package 无法收口；
- 独立矩阵或固定快照需要由执行方修改。

实现者可以在不改变本文语义的前提下调整内部类名、目录细节和测试拆分，但必须在运行说明记录。窗口尺寸可在同一视觉基线内依据目标 Windows 证据小幅调整；断点、设置 Schema 或用户可见行为变化需要总控批准。
