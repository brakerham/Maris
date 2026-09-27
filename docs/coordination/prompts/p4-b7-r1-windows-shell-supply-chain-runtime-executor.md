# P4-B7-R1 执行智能体任务卡：供应链修复与真实 Host 组合续段

你是执行智能体，唯一负责 `P4-B7-R1：供应链修复与真实 Host 组合续段`。

这是 `P4-B7` 的有限续段，不是从头重写桌面应用。必须保留并复用现有 66 文件 Windows Shell 实现、执行方测试、窗口/Tray/毛毛/主题/IPC/OpenAPI/模块注册/owner/Supervisor/HostClient/outbox 代码和既有失败证据。

## 开始前必须按顺序读取

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze-003.md`
8. `docs/b7-windows-shell-running.md`
9. `apps/desktop/b7-source.sha256`
10. `docs/phase-4-d12-b7-supply-chain-advice.md`
11. `docs/p4-d12-coordinator-review.md`
12. `docs/phase-4-interface-freeze-004.md`
13. `docs/coordination/snapshots/p4-b7-r1-start.sha256`
14. 本任务卡

开始前、下载或安装任何依赖前、启动 Uvicorn/Electron/Maris 前和每个长操作检查点前，重新读取最新 `docs/coordination/control.md`。若 control 的任务、唯一负责人、停止指令或版本冻结与本卡冲突，以最新 control 为准，安全停止旧动作并报告。

## 已批准的两项决定

1. 总控批准 Forge `8.0.0-alpha.10` 只作为发布前 B7-R1 验证基线。不得把 alpha 当正式发布版本，也不得自由试其他 Forge 版本。
2. 总控批准新增带 startup nonce 的 managed desktop `GET /api/v1/desktop/readyz`，同时保持通用 `/readyz` 的完整 provider readiness 语义不变。

不得再次把这两项作为待决定问题，也不得要求用户重复确认。任务卡本身就是本轮项目依赖安装、本地构建和自有测试服务的授权；仍须遵守以下精确边界和停止条件。

## 目标

在一个执行任务内完成两个顺序依赖的续段：

1. 把 Forge 7 的脆弱构建链迁移到 P4-IF-004 冻结的 Forge 8 alpha 同 cohort，实际证明 clean install、完整/生产审计、编译、打包和包后行为；
2. 只有供应链门禁全部通过后，完成 Electron main → managed Python Host → local owner session → HostClient → modules → renderer 的真实组合，并保持所有 token/nonce/进程细节在 main/Python 可信边界内。

最终生成新的不可变 source manifest、lock hash、package hash和运行说明，状态只能提交到 `review / finished`，等待 P4-C12 独立验收。

## 唯一负责人和文件边界

你是本任务唯一实现负责人，也是本轮 Node/pnpm install、Uvicorn、Electron、Maris 和 package smoke 的唯一环境负责人。

允许修改：

- `.node-version`
- `.npmrc`
- 根 `package.json`
- `pnpm-workspace.yaml`
- `pnpm-lock.yaml`
- `apps/desktop/package.json`
- `apps/desktop/forge.config.ts`
- `apps/desktop/vite.*.config.ts`
- `apps/desktop/tsconfig.json`
- `apps/desktop/vitest.config.ts`
- `apps/desktop/electron/main/**`
- `apps/desktop/electron/preload/**`，仅在 typed IPC 合同需要时
- `apps/desktop/src/shared/**`，仅在安全 runtime/module DTO 需要时
- `apps/desktop/src/generated/**` 与 `apps/desktop/openapi/**`，只允许由项目生成命令更新
- `apps/desktop/scripts/**`，只允许依赖门禁、生成物检查和安全扫描所需最小变化
- `apps/desktop/tests/unit/**`
- `apps/desktop/tests/e2e/**`
- `apps/desktop/vendor/**`：只允许在 lock 不再引用后删除旧 Electron node-gyp tarball；不得加入新 fork
- `tools/openapi/export_host_schema.py`，仅在新端点生成合同需要时
- `src/wife_system/api/app.py`
- `src/wife_system/api/desktop_runtime.py`
- 可新增 `src/wife_system/api/desktop_sidecar.py`
- `src/wife_system/api/host_routes.py`
- `src/wife_system/api/production.py`
- `src/wife_system/host/runtime.py`，只允许拆出不含 provider 的 core readiness；不得改变其他 Host 语义
- `tests/host/test_desktop_runtime.py`
- `tests/host/test_production.py`
- 可新增或最小修改其他 `tests/host/test_*desktop*` 执行方测试
- `docs/b7-r1-windows-shell-running.md`
- `apps/desktop/b7-r1-source.sha256`
- `docs/coordination/agents/executor.md`

如果真实代码表明必须修改一个未列出的文件，先停止对应范围，在执行日志说明文件、原因和最小变化，不得自行扩大。

禁止修改：

- `tests/independent/**`
- `docs/testing/**`
- `docs/coordination/control.md`
- `docs/coordination/overview.md`
- `docs/coordination/agents/brainstorm.md`
- `docs/coordination/agents/technical-adviser.md`
- `docs/coordination/agents/tester.md`
- P4 接口冻结、D12、总控审阅和本任务卡
- migration
- FinanceService、Agent 工具、pending、memory、activity import 业务语义
- OpenClaw、微信、DeepSeek、真实 provider、真实个人财务数据和账号
- `.claude/**`；不得读取、修改、删除或提交

不得执行任何 Git 写操作，包括 add、commit、restore、reset、checkout/switch、merge/rebase、push、tag 或 PR。允许只读 `git status`、`git diff`、`git log`、`git ls-files` 和对象/文件摘要。

## 固定输入和接管规则

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-start.sha256`。
2. 报告 matched、mismatch、missing 和 invalid 行；任一 mismatch/missing 先停止，不修改产品。
3. 确认 `apps/desktop/b7-source.sha256` 的 66 条全部匹配。
4. 不删除或重写 B7 的失败历史；新结果写入 `docs/b7-r1-windows-shell-running.md`。
5. 记录接单日志和 `Current execution snapshot` 后才允许修改文件。

## 长任务与停止规则

- 任何预计超过五分钟的 install、test、package、E2E 或 smoke，开始前在 executor 状态写操作、开始时间、下一检查点和可观察进程/会话。
- 有执行控制时，至少每十分钟或每个实质输出更新心跳。
- 同一阻塞连续两个检查点没有有效新输出，安全停止，保留现场并报告；不得无限重试。
- 测试断言失败只允许在定位后做一次有根据的修复和定向复跑；不得用重复成功覆盖首次失败。
- 本卡的 P0 条件出现时立即停止受影响范围，不继续后续里程碑。

## 里程碑 1：恢复精确项目本地工具

必须使用 Node `24.21.0` 与 pnpm `12.7.0`。不得用系统实际存在的其他 Node 版本代替结果。

若现有项目本地工具已被 B7 清理，可以：

1. 从 Node.js 官方发布源下载 Windows x64 `24.21.0` 到项目内忽略目录；
2. 根据官方 `SHASUMS256.txt` 验证下载摘要；
3. 从 npm registry 取得 pnpm `12.7.0` 到项目内忽略目录；
4. 使用绝对路径调用该 Node/pnpm，不修改系统 PATH、全局 npm、用户 profile 或系统安装；
5. 在报告中记录来源、版本、摘要、工具目录和最终清理状态，不记录代理凭据、token 或私人路径之外的信息。

下载/安装前重新读取 control。网络或权限失败时按正常授权机制报告，禁止切换非官方镜像、关闭安全软件或添加排除项。

首先记录：

```text
node --version == v24.21.0
pnpm --version == 12.7.0
```

版本不精确则停止。

## 里程碑 2：供应链候选图

一次性实施 P4-IF-004 F01～F09：

1. 将四个 Forge direct dependencies 精确改为 `8.0.0-alpha.10`。
2. 将 `@electron/fuses` 精确改为 `2.0.0`。
3. 保留 Node、pnpm、Electron、React、TypeScript、Vite、Router 的冻结精确版本。
4. 移除旧 Electron node-gyp 本地 tarball override。
5. 增加 `tar: 7.5.21` 精确 override。
6. 保留 hoisted、strict peers、关闭 auto peer、block exotic subdeps 和只允许 electron/esbuild 的 lifecycle allowlist。
7. 只生成 clean candidate lock，先不要开始 Host 接线。

候选 lock 必须精确解析：

```text
@electron/packager 20.3.0
@electron/rebuild 4.2.0
node-gyp 12.4.0
tar 7.5.21
@electron-internal/extract-zip 1.0.5
```

以下必须完全消失：

```text
@electron/packager 18.4.4
extract-zip 2.0.1
@electron/rebuild 3.7.2
@electron/node-gyp 10.2.0-electron.1
tar 6.2.1 and every tar < 7.5.21
tmp 0.0.33
```

如 tmp 重新出现，必须 `>=0.2.7` 并重新 full audit。出现与冻结不同的 resolved version、新 install script、Git/exotic dependency 或未知 native binary，立即停止并报告，不顺手接受。

在开始 Host 接线前必须全部通过：

- lockfile-only resolution；
- peer dependency check；
- exotic dependency/lifecycle script 检查；
- full `pnpm audit --audit-level high`：critical=0、high=0、退出码 0；
- production-only audit：critical=0、high=0、退出码 0；
- 依赖图或 SBOM 与 lock SHA-256；
- `pnpm why/list` 证明消失清单；
- deprecated transitive 列表和解释。

禁止 ignore GHSA、降低等级、使用 `audit fix --force` 或拆锁来隐藏 Forge 7 图。

## 里程碑 3：Clean frozen install 与静态门禁

从没有项目 `node_modules` 的状态执行 frozen lock install。只允许冻结的 lifecycle scripts。记录网络下载、cache 和 install 结果，但不记录凭据。

完成：

- frozen install；
- OpenAPI `check:generated`；
- TypeScript；
- lint；
- 现有全部 Vitest unit/component/IPC；
- Forge 8 config、ESM、Vite plugin 和 fuses 的最小执行方测试。

若 alpha 要求修改 Electron major、重写业务、放宽三层安全、启用 Node integration 或增加 renderer 权限，立即停止。静态门禁全绿后才进入真实 Host 组合。

## 里程碑 4：Desktop core readiness

实现 P4-IF-004 F10/F11：

1. `HostRuntime` 增加不含 provider 的 core readiness seam，复用 registry、database 与 Alembic head 检查，避免复制不一致逻辑。
2. 新增 `GET /api/v1/desktop/readyz`；只在 managed desktop gate 下通过。
3. 必须验证 `X-Maris-Startup-Nonce`，使用常量时间比较；不记录或回显 nonce。
4. 通用 `/readyz` 继续包含 provider 检查；现有 `agent_provider_unconfigured` 行为和测试必须保留。
5. `/healthz` 保持存活探针。
6. 更新离线 OpenAPI 和生成 TypeScript；生成物漂移检查必须通过。

执行方测试至少覆盖：

- general deployment 不能把 desktop endpoint 当通用 ready；
- managed + 正确 nonce + DB/head/registry 正常时 desktop core ready 200，即使 provider 未配置；
- missing/wrong nonce 503 且不泄露；
- database unavailable、migration old、registry empty 分别 fail closed；
- 通用 `/readyz` 在 provider 缺失时仍 503；
- 错误响应、日志和 OpenAPI 不包含 nonce、URL、SQL、路径或 traceback。

## 里程碑 5：Managed sidecar 与 Supervisor

实现 P4-IF-004 F12～F15/F19：

- 新建受控 Python desktop sidecar entry；loopback、单 worker、无 reload；
- 通过专用父子通道返回协议版本、instance ID、实际 port 和 nonce digest，不打印原 nonce；
- main 的 managed Host port 负责 spawn、handshake、health/core-ready 和 owned stop；
- start/recover single-flight；
- 任一 handshake/ready 失败在返回前清理本次 owned child；
- recover 先停止旧 owned child，再按 1/2/4 秒有界恢复；
- online 每 5 秒 health，连续三次失败才 offline，child exit 立即 offline；
- 5 分钟最多 3 次，online 稳定 10 分钟后重置预算；
- stop/quit 幂等，5 秒后只强停确属本次 owned 的进程树；PID 单独不能证明 ownership；
- external_dev 仅 development、显式 loopback URL 和非空本次 nonce；不停止或重启外部进程。

至少新增执行方测试覆盖 ready false cleanup、recover old child cleanup、并发 start/recover、三次 health failure、budget exhaustion、重复 stop/quit 和 external mode never kill。

## 里程碑 6：Owner、HostClient 与 composition root

实现 P4-IF-004 F12/F16～F19：

1. OwnerSecretStore 使用 safeStorage 加密、stage/commit/repair 和同目录原子替换。
2. owner auth client 严格调用 bootstrap status、initialize、login、refresh；只返回验证过的 token pair。
3. LocalOwnerSession 提供 main-only access token seam、single-flight refresh、revoke/repair。
4. HostClient 使用 main-only Bearer；401 最多一次 refresh+retry；modules 使用严格 runtime schema，只返回安全摘要。
5. composition root 只创建一套 Supervisor、Host port、secret store、owner session、HostClient 和 runtime publisher。
6. main 不再返回固定 stopped/空 modules；只把真实安全 snapshot 和 Host/compiled registry 交集提供给 IPC。
7. renderer/preload 不取得 HTTP client、token、nonce、PID、port、文件路径、进程或任意 Node 能力。
8. Tray quit、app quit、Windows session end 走统一 bounded shutdown；隐藏窗口不停止 Host。

新增/扩展执行方测试覆盖：

- 首次本地 owner 初始化与后续恢复；
- access token 只在 main；
- refresh single-flight；
- revoke/repair；
- HostClient 401 一次重试；
- modules schema 拒绝、版本/交集 fail closed；
- runtime state 事件脱敏；
- 多次 IPC/窗口不创建第二套 Supervisor、session 或 HostClient；
- shutdown 顺序、重复 quit、隐藏窗口不停止 Host。

不得提前实现真实财务卡片、账本写入、模型回答、投资行情或 P4-C/P4-D 业务。

## 里程碑 7：Python 与 managed Uvicorn smoke

只运行受影响的执行方 Python 范围：

- desktop runtime/readiness；
- production composition；
- auth/owner；
- modules；
- OpenAPI；
- 必要的相邻 Host 回归。

不得运行或修改 `tests/independent/**`。不启动 Docker/PostgreSQL、DeepSeek、OpenClaw 或微信。

使用任务自己启动的 loopback、single-worker、no-reload managed sidecar 验证：

1. handshake 和 nonce digest；
2. `/healthz`；
3. desktop core readiness；
4. 通用 `/readyz` 在无 provider 时仍 fail closed；
5. owner establish；
6. modules；
7. recover；
8. stop 和 owned PID/port 收口。

只停止本任务拥有的进程。开始前记录 PID/session，结束后证明 residual=0。

## 里程碑 8：Windows package 与包后行为

在冻结 lock、Node 24.21.0、pnpm 12.7.0 下执行 Forge package。验证：

- Packager 20 hooks；
- Vite main/preload/renderer 输出；
- ASAR、preload、fuses、资源复制；
- 包内不存在 Forge 7 脆弱依赖、Node 工具缓存、secret、token、nonce、个人数据、开发配置或任意更新 URL；
- packaged app 使用真实 composition root，不是固定空模块假 runtime。

随后：

1. 对最终 package 的 `app.asar` 运行 E2E；
2. 对真实 `Maris.exe` 做 startup、owner、modules、offline/recover、Tray quit、owned child cleanup smoke；
3. 检查 renderer 无任意网络/Node/文件系统权限；
4. 检查应用退出后 Electron、Maris、Node/Python sidecar、端口、窗口、Tray 和测试 profile 均无本任务残留。

Forge/package/E2E/EXE 任一失败都停止；不得切换 Forge 版本、回退 Forge 7 override 或把 app.asar 测试冒充真实 EXE 测试。

## P0 立即停止条件

出现任一项，任务停为 `blocked / finished`，保留证据并交回总控：

- 起点快照 mismatch/missing；
- 工具版本不精确；
- 候选 resolved 图与 P4-IF-004 F04 不一致；
- full/prod audit 有 critical/high；
- 新 install script、Git/exotic dependency 或未知 native helper；
- Forge 8/Packager 20/Vite/fuses/ESM 行为不兼容；
- 需要改变 Electron major、放宽 renderer/preload 安全或重写业务；
- 需要改变通用 `/readyz`、使用 `/healthz` 冒充 ready 或注入假 provider；
- ready 失败遗留 child、停止非 owned 进程、PID 被当唯一 ownership；
- token、nonce、密码、真实个人数据或私密日志进入 renderer、日志、receipt 或 package；
- 需要修改 migration、Finance/Agent/pending/memory/activity import 业务；
- 需要修改/运行独立测试、矩阵或独立报告；
- 同一问题连续两个检查点没有有效新输出。

禁止用 skip/xfail、删测试、放宽断言、降低 audit、忽略 GHSA、隐藏 warning 或重复成功覆盖首次失败。

## 最终执行方验证

最终报告必须分别列出 passed/failed/skipped/warnings，不得把 collect、历史结果或 package 成功冒充业务通过。至少包括：

1. Node/pnpm exact；
2. lock hash、依赖图/SBOM、消失清单；
3. peer/exotic/lifecycle 检查；
4. full audit；
5. production audit；
6. clean frozen install；
7. OpenAPI generated diff；
8. TypeScript 与 lint；
9. Vitest 执行方测试；
10. Python 定向与相邻回归；
11. managed sidecar/Uvicorn smoke；
12. Forge package；
13. app.asar E2E；
14. `Maris.exe` 真实 smoke；
15. 包内容隐私/秘密扫描；
16. owned 进程、port、window、Tray、profile、临时工具和 cache 收口；
17. `git diff --check`；
18. 修改文件边界与逐文件 SHA-256。

## 交付物

1. 实际代码、依赖、锁文件、配置和执行方测试；
2. `docs/b7-r1-windows-shell-running.md`；
3. `apps/desktop/b7-r1-source.sha256`；
4. 更新 `docs/coordination/agents/executor.md`。

终点 source manifest 至少覆盖起点快照中所有项目文件，以及本轮新增的实现、执行方测试、生成物和配置；排除 `node_modules`、工具缓存、package/out、测试 profile、临时目录、trace、日志和任何秘密。逐行格式为：

```text
relative/path<TAB>lowercase_sha256
```

报告给出 manifest entries、聚合算法和可复算总摘要，同时单独给出 lock、最终 `Maris.exe`、`app.asar` 和运行说明摘要。

## 完成规则

- 只有供应链、真实 Host 组合、全部执行方门禁和资源收口均通过时，状态才可提交 `review / finished`。
- `review` 不是独立验收或项目 complete；不得自动启动测试智能体或 P4-C12。
- 完成后停止修改，等待头脑风暴总控复算快照并生成 P4-C12。
- 不执行 Git 写操作，不推送远程。
