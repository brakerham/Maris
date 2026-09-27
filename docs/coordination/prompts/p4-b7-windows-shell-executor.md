# 给执行智能体的 Prompt：P4-B7 Windows Shell、毛毛与模块 UI 实现

你是项目中既有的**执行智能体**，唯一负责 `P4-B7`：按照冻结的 P4-IF-003，实现 Windows 桌面 Shell、模块 UI 注册、本地 owner 会话、BackendSupervisor、离线 outbox、Tray、主题和单一毛毛窗口。

本任务是 P4-B 的单一集成实现任务。main、preload、renderer、Python desktop transport 和执行方测试必须在同一个任务中保持类型与安全边界一致，不要拆给多个会修改共享文件的实现者。你必须自测，但不能做测试智能体的独立验收；即使全部通过，也只能交付 `review / finished`，不能宣布 P4-B `complete`。

用户把本任务卡发送给你，即授权：在工作区内新增冻结范围的桌面代码，下载并安装**项目级**精确依赖，生成 lockfile，运行开发/测试/unsigned package，并为测试启动和关闭你自己拥有的本地 FastAPI 子进程。该授权不包括系统级全局安装、账号登录、Docker、OpenClaw、微信、DeepSeek、代码签名、发布、修改安全软件或 Git 写操作。

## 1. 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-b-windows-shell-brainstorm.md`
8. `docs/phase-4-d11-windows-shell-technical-advice.md`
9. `docs/p4-d11-coordinator-review.md`
10. `docs/phase-4-interface-freeze-003.md`
11. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
12. `docs/coordination/snapshots/p4-b7-start.sha256`

如果最新 `control.md` 已取消、暂停、转交本任务，或指定其他唯一负责人，立即停止并报告旧任务卡失效。不要修改 control、overview 或其他角色状态。

在 `docs/coordination/agents/executor.md` 记录接单和 `Current execution snapshot`：当前里程碑、开始时间、最近进展、心跳、下一检查点、等待对象、进程/session 引用。每个里程碑开始和完成时更新；超过五分钟的 install/build/package/E2E 开始前登记可观察命令和下一检查点；至少每十分钟或实质输出后更新心跳。

## 2. 固定输入快照

使用：

```text
docs/coordination/snapshots/p4-b7-start.sha256
entries=113
manifest_sha256=1cf5603e86d4f9eccb3240feafda7443f5d9c9c610afc738707909c4e0581d02
```

开始前逐行复算，要求 `matched=113`、`missing=0`、`mismatch=0`。缺失或 mismatch 时立即停止，不得用 `git restore/reset/checkout/switch` 或覆盖文件“修复”输入。

执行期间，清单中只有本任务明确允许修改的窄 Python 文件和执行方测试可以变化；其余现有实现、migration 和冻结文档必须保持。交付报告列出起点匹配数、终点 unchanged/changed/added/missing，以及所有新增/变更文件的普通 SHA-256。

## 3. 唯一实现合同

完整合同见 `docs/phase-4-interface-freeze-003.md`。以下条款是硬边界：

### 3.1 精确基线

```text
Node.js                 24.21.0
Electron                44.4.5
React / React DOM       19.3.0
TypeScript              6.0.3
pnpm                    12.7.0
Electron Forge packages 7.11.2
Vite                    7.3.6
React Router            8.4.0
```

- 根 `.npmrc` 必须设置 `node-linker=hoisted`。
- 核心依赖用精确版本，不用 `^`/`~`。
- `pnpm-lock.yaml` 固定完整依赖图。
- lifecycle scripts 采用最小 allowlist。
- TypeScript 6.0.3 是有意兼容基线；不得自行切换 TypeScript 7 或建立双编译器路径。
- Forge Vite plugin 的 experimental 状态必须由精确 pin、package smoke 和 E2E 控制。

如果系统没有合适 Node/pnpm，可以使用不改变系统全局配置的、项目可恢复的本地工具链目录；必须记录来源、版本、路径和摘要。不要无提示安装系统级软件或修改用户 PATH。若只能通过管理员级或系统级安装继续，停在 `blocked / finished` 并向总控提出一个具体请求。

### 3.2 安全与架构

- Electron main 独占 Host HTTP、token、owner credential、safeStorage、文件、子进程、窗口、Tray、外链和 outbox。
- preload 只公开固定 typed API；禁止原始 IPC、任意 channel、Node、文件、进程、token、nonce 和 Host URL。
- renderer 开启 sandbox/contextIsolation，关闭 nodeIntegration；生产 CSP 使用 `connect-src 'none'`。
- renderer 不直接访问 Host 或网络。固定路径为 `renderer -> preload -> main -> FastAPI`。
- 所有 IPC 校验 sender、origin、window、判别联合类型、额外字段和长度；未知输入稳定拒绝且零副作用。
- 文本默认用 text node 渲染，不使用 raw HTML；错误只显示安全 code/message/request ID。
- compiled registry 与 `/api/v1/modules` 求交集；Shell 禁止按 module ID 写业务分支。
- OpenAPI 从正式 FastAPI app 离线生成；运行时不下载 Schema，不手写平行 DTO。
- 不新增注册/多用户/云账户/登录页；使用现有本地 owner initialize/login/refresh。
- 只允许 P4-IF-003 的 desktop nonce/readiness 窄 Python 扩展；不得改变 Finance、Agent、pending、memory、activity import 或业务幂等语义。
- 只停止自己启动、句柄/ownership/instance/nonce 全部匹配的 Python 子进程；external_dev 永不取得停止权。
- outbox 固定 `client_event_id`；离线、重试、响应丢失和重启不得生成第二个 ID。
- 全局只有一个毛毛 BrowserWindow；模块形态和运行子状态分离。

### 3.3 P4-B 页面范围

实现贴近已冻结视觉方向的 Shell、模块导航、三栏、Agent 面板占位、设置、主题和 daily-finance 占位页面。占位数据必须明确标为演示/未连接，不得伪造真实余额、预算建议、账本、持仓、行情或模型回答。

P4-C 才实现真实财务驾驶舱、账本管理、聊天/候选确认与写账；P4-D 才实现财富管理和行情。P4-B 不安装图表库，只定义 lazy `ChartAdapter`。

## 4. 七个内部里程碑

必须按顺序执行。每个里程碑形成可运行检查点；不要一次性生成大批文件后才测试。

### 里程碑 1：工具链与安全空壳

- 建立根 pnpm workspace 与 `apps/desktop`。
- 建立 Electron main/preload/renderer 三层、Forge/Vite/TypeScript 配置。
- 固定 BrowserWindow 安全配置、CSP、navigation/window deny 和外链 allowlist。
- 提供空 Shell 的 dev 启动、typecheck、unit smoke 和 `forge package` smoke。
- 静态/运行断言 renderer 无 Node 能力。

失败停止条件：依赖安全 P0、renderer 获得 Node、安装不可复现或 package 无法启动且两个检查点无进展。

### 里程碑 2：OpenAPI 与模块交集

- 从 production app 离线导出 OpenAPI，生成 checked-in TypeScript 类型。
- 建立 main-only Host client 与稳定 `DesktopError`。
- 实现 `DesktopModuleContribution`、严格 runtime parser、compiled registry、全局冲突检查和 Host 交集。
- 实现 `daily_finance` 占位 contribution、lazy route 和局部错误边界。
- 建立 `check:generated` 和 Schema 漂移测试。

需要改变 P4-A业务 DTO 或语义时停止并交回总控。

### 里程碑 3：IPC、设备设置与本地 owner

- 建立 main/preload typed IPC allowlist 和反例测试。
- 实现版本化设备设置、严格 Schema、原子写入、损坏回退。
- 实现 safeStorage adapter、local owner initialize/login/refresh、并发 401 single-flight。
- token/credential 只在 main/安全存储，renderer 只见安全状态。
- logout/revoke 后进入 repair，不静默恢复。

任何 secret 进入 renderer、日志、设置或错误正文时按 P0 停止。

### 里程碑 4：BackendSupervisor 与加密 outbox

- 实现 managed/external_dev、七种固定状态、有界 ready/health/recovery/stop。
- 实现 P4-IF-003 的 startup nonce/readiness 窄 Python扩展及执行方测试。
- 实现 main 加密 outbox、容量/清理规则、稳定 ID、payload digest 和重启恢复。
- 用可控假 child/Host 覆盖端口冲突、坏 nonce、超时、early/online crash、重启预算、错误 ownership、同 ID 重试。
- 最小真实 FastAPI 子进程 smoke 只能启动本任务自己的服务，并在结束时关闭。

不得启动 Docker、PostgreSQL、OpenClaw、微信或 DeepSeek。

### 里程碑 5：Shell、主题与 Agent 面板

- 实现主窗口三栏、模块导航、daily placeholder、统一 Agent panel placeholder、设置入口。
- 支持 960×680 最小窗口、1120/1360 初始断点。
- 支持 system/light/dark/high-contrast、reduced motion、privacy mode。
- 处理恶意/超长/RTL 文本、键盘、焦点、lazy error/retry。
- 页面切换只改变 route/contribution/形态，不调用模型、不创建 run、不写财务数据。

### 里程碑 6：Tray、毛毛与 Windows 生命周期

- single instance；第二次启动只激活主窗口。
- 实现 `hide_to_tray / ask_every_time / quit` 和只提示一次。
- 实现唯一 `CompanionController`、一个毛毛窗口、模块形态、七种子状态和显隐/置顶。
- 实现 DIP bounds、display clamp、透明失败到普通迷你窗降级、登录项 adapter（默认关）。
- 外部全屏没有可靠 adapter 时显示为不支持并保留手动隐藏，不引入未知原生二进制。
- 建立可自动化的 Electron E2E，并为必须人工的 Windows 项生成明确步骤和证据模板。

### 里程碑 7：固定交付

- 完整执行 typecheck、lint、generated、unit、component、IPC、Electron E2E、Python 定向回归和 package smoke。
- 从 unsigned package 运行一次核心 smoke，不把 dev server 成功当打包成功。
- 清理本任务自有子进程、窗口、端口和临时目录；保留 package 和脱敏测试证据。
- 生成 `docs/b7-windows-shell-running.md`，包含架构、数据流、运行命令、依赖版本、逐项自测、Windows 未验证项、资源收口和文件摘要。
- 更新 executor 状态为 `review / finished` 后停止，不继续 P4-C 页面或 P4-D 模块。

## 5. 文件所有权

### 允许新增或修改

```text
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
.node-version
.npmrc
apps/desktop/**
tools/openapi/**
src/wife_system/api/desktop_runtime.py              # 可选新增；只放 desktop transport/nonce
src/wife_system/api/app.py                          # 仅窄 desktop readiness 接线
src/wife_system/api/host_routes.py                  # 仅窄 desktop readiness 接线
src/wife_system/api/host_schemas.py                 # 仅必要的安全 DTO
src/wife_system/api/production.py                   # 仅 production desktop profile 组合
tests/host/test_api.py                              # 执行方定向回归
tests/host/test_production.py                       # 执行方定向回归
tests/host/test_desktop_runtime.py                  # 可选新增执行方测试
docs/b7-windows-shell-running.md
docs/coordination/agents/executor.md
```

如必须修改上述清单外的产品文件，先停止并提交具体路径、原因、最小合同变化和测试影响，由总控裁定。不要用“大范围重构”绕过文件边界。

### 禁止修改

```text
migrations/**
src/wife_system/finance/**
src/wife_system/agent/**
src/wife_system/activity_import/**
src/wife_system/host/**
tests/independent/**
docs/testing/phase-4-modular-agent-host-test-matrix.md
docs/phase-4-interface-freeze*.md
docs/phase-4-d11-windows-shell-technical-advice.md
docs/p4-d11-coordinator-review.md
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/agents/brainstorm.md
docs/coordination/agents/tester.md
docs/coordination/agents/technical-adviser.md
docs/coordination/snapshots/**
```

禁止删除或放宽既有测试，禁止添加 skip/xfail 掩盖失败，禁止修改 `.claude/**`。

## 6. 自测与证据口径

执行方必须编写并运行实现测试。至少提供：

1. 精确依赖、lockfile 和允许脚本检查；
2. TypeScript typecheck 和 lint；
3. OpenAPI 重生成零 diff；
4. module registry、交集、冲突和 lazy error 测试；
5. IPC sender/origin/schema/extra/unknown 输入反例；
6. local owner、refresh single-flight、safeStorage fail-closed 和 secret scan；
7. Supervisor 状态、ownership、nonce、timeout、backoff、stop 和 crash 测试；
8. outbox stable ID、重复点击、响应丢失、重启恢复和容量测试；
9. React Shell、主题、断点、RTL/恶意文本、键盘和 privacy 测试；
10. Electron E2E：single instance、Tray、close policy、一个毛毛、状态切换和退出收口；
11. `forge package` 与 packaged smoke；
12. 受影响 Python Host 定向回归，以及未受影响 P4-A 的合理相邻回归。

执行方测试可以覆盖 P4-B 24 项所需风险，但不得更新独立矩阵状态，也不得把自测称为独立通过。人工未执行项写 `unverified`，不能用代码审查代替真实 Windows 证据。

所有 fixture 使用虚拟数据。响应、日志、trace、outbox、设置和报告不得包含 API key、真实 token、owner 密码、startup nonce、个人财务数据、原始 SQL、内部路径或未脱敏异常。

## 7. 环境与停止规则

- 第一次安装依赖或启动服务前重新读取最新 `control.md`。
- 只允许项目级依赖；不执行账号登录、publisher、signing、系统级安装或全局 PATH 修改。
- 不启动 Docker/PostgreSQL；P4-B 不需要它们。
- 任何长操作使用可观察、可恢复的会话，状态文件记录 session/process 和下一检查点。
- 同一阻塞连续两个检查点无进展时，停止相关工作，保留产物并报告最小错误；不要无限重试。
- P0 条件立即停止：secret 泄露、renderer Node/网络越权、错误进程被停止、幂等 ID 变化、未授权业务写入、依赖供应链高危或无法安全收口。
- 失败时准确写 `blocked / finished`；不得用旧结果、collect-only、skip 或重复成功运行伪装本轮通过。

## 8. Git 边界

不得执行任何 Git 写操作，包括 add、commit、restore、reset、checkout/switch、merge/rebase、push、tag、PR。可以只读使用 status/diff/log 和对象哈希。最终交给头脑风暴总控审阅、生成固定快照并决定本地提交。

## 9. 最终交付

最终回复和 `docs/b7-windows-shell-running.md` 必须包含：

- 七个里程碑逐项实现位置和结果；
- main/preload/renderer/Python 的实际数据流；
- 精确依赖版本、安装方式、lockfile 和供应链控制；
- 所有测试命令按类别统计 passed/failed/skipped/warning；
- dev 与 packaged app 的运行方式；
- 24 项矩阵的执行方证据映射，但状态仍由测试智能体更新；
- Windows 自动/人工证据及 `unverified` 项；
- 资源收口和残留进程/端口检查；
- 起点/终点快照统计、所有变更和新增文件的 SHA-256；
- 风险、限制、下一步只到 P4-C12 独立验收。

完成后把任务停在 `review / finished`，等待总控核对。不要自行启动 P4-C12、技术顾问、外部联调、P4-C 或 P4-D。
