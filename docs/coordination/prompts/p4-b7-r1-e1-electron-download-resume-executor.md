# P4-B7-R1-E1 执行智能体任务卡：官方 Electron 链路恢复后续跑

你是执行智能体，唯一负责 `P4-B7-R1-E1`。本任务延续已停止的 P4-B7-R1，不从头重做桌面 Shell，不返回 Forge 7，也不改变 P4-IF-004。

用户把本文件全文发送给你，即表示授权你在本任务边界内恢复项目本地 Node/pnpm 工具、访问冻结的官方软件源、安装项目依赖、运行执行方测试、启动并停止本任务拥有的 loopback Python/Electron/Maris 进程、修改授权产品文件并生成交付证据。不要再次要求用户确认这些已授权动作。

## 必读输入

开始前依次读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. 最新 `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze-003.md`
8. `docs/phase-4-interface-freeze-004.md`
9. `docs/phase-4-d12-b7-supply-chain-advice.md`
10. `docs/p4-d12-coordinator-review.md`
11. `docs/b7-r1-windows-shell-running.md`
12. `docs/p4-b7-r1-blocked-coordinator-review.md`
13. `apps/desktop/b7-r1-dependency-graph.json`
14. `apps/desktop/b7-r1-source.sha256`
15. `docs/coordination/snapshots/p4-b7-r1-e1-start.sha256`
16. 本任务卡

最新 control 与本任务冲突时，以 control 为准。先在 `docs/coordination/agents/executor.md` 登记接单、当前步骤、开始时间、下一检查点和可观察会话，再执行外部下载或长操作。

## 已确认事实

- P4-B7-R1 已正确停为 `blocked / finished`，不得把它改写成 review。
- R1 source manifest 为 182 entries，交接时 `182/182 matched`。
- 停止时最终 lock SHA-256 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- 候选 audit lock 与最终 lock 不同，因此旧的 full/prod audit 0 不能直接代表最终 lock。
- Electron `44.4.5` 官方 release 和 Windows x64 资产存在；总控在 2026-09-27 20:35 使用 curl HEAD 与本机 Node fetch HEAD 均得到 200。这只是恢复条件，不是本任务实际安装通过证据。
- 官方 Windows x64 归档预期 SHA-256 为 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- Host 接线、Python smoke、Forge package、app.asar E2E、真实 EXE 和 C12 均尚未执行。

## 起点门禁

任何修改、安装或运行前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-e1-start.sha256`；必须全部匹配。
2. 独立逐行复算 `apps/desktop/b7-r1-source.sha256`；必须为 182 matched、0 mismatch、0 missing。
3. 核对 R1 报告、dependency graph、最终 lock、package manifest 和 executor 状态摘要。
4. 重新读取最新 control；确认你仍是 E1 唯一负责人，测试智能体、技术顾问和 P4-C12 均停止。

任一 mismatch/missing 时立即停止，不 restore、不 reset、不覆盖现场。

## 文件边界

允许修改：

- 根 `.node-version`、`.npmrc`、`package.json`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`；
- `apps/desktop/**`，但不得读取或修改 `.claude/**`；
- `tools/openapi/**`；
- P4-IF-004 已允许的最小 Python desktop sidecar/readiness/production/Host route 接线；
- 对应 `tests/host/**` 执行方测试；
- `docs/b7-r1-e1-windows-shell-running.md`；
- `apps/desktop/b7-r1-e1-source.sha256`；
- `docs/coordination/agents/executor.md`。

禁止修改或运行：

- `tests/independent/**`；
- P4 测试矩阵、独立报告、control、overview、其他角色状态；
- migration；
- Finance、Agent、pending、memory、activity import 业务语义；
- 微信、OpenClaw、DeepSeek、Docker/PostgreSQL；
- `.claude/**`；
- Git 状态与远程仓库。

## 阶段 1：最终 lock 的供应链闭环

使用冻结的项目本地 Node `24.21.0` 和 pnpm `12.7.0`。工具只放任务拥有的工作区忽略目录，从官方来源取得并核对已记录摘要，不改系统 PATH、全局 npm、用户 profile 或系统安装。

在当前最终 lock 上重新执行并分别保存统计：

1. full audit，门禁为 critical=0、high=0；
2. production-only audit，门禁为 critical=0、high=0；
3. peer、exotic、Git/file source、lifecycle allowlist 检查；
4. 从不存在项目 `node_modules` 的状态执行 clean frozen install；
5. frozen install 前后重新计算 `pnpm-lock.yaml` SHA-256，必须不变；
6. 再次确认 F04 五个传递版本和旧六类依赖消失。

不得把候选 audit lock 的历史结果计入本轮。最终 lock 漂移、出现 critical/high、未知 lifecycle、Git/exotic/file source 或冻结图不符时，立即停止。

## 阶段 2：Electron 官方资产恢复门禁

只允许 Electron 官方 GitHub Release 路径和包自带的官方下载/校验入口。不设置第三方 `ELECTRON_MIRROR`，不复制旧 package 二进制，不关闭安全软件，不添加排除项，不复用无法证明摘要的缓存。

步骤：

1. 在外部下载前重读最新 control。
2. 通过官方安装入口获取 Electron `44.4.5` Windows x64 资产。
3. 核对下载归档或官方安装器所验证的 SHA-256 必须等于 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
4. 证明 `node_modules/electron/dist/electron.exe` 存在并可报告安全版本信息。
5. 不把临时签名 URL、代理凭据或完整私密日志写入项目。

若首次仍失败，只允许一次有诊断价值的第二检查点。第二检查点必须补充脱敏的 `error.name`、`error.message`、底层 `cause.code`、失败主机以及 DNS、TLS、redirect 或文件写入阶段；不得只是原命令盲重跑。同一问题连续两个检查点没有新进展时，停为 `blocked / finished`。

## 阶段 3：恢复原 R1 静态与测试门禁

Electron binary 验证通过后，运行：

- OpenAPI generated drift；
- TypeScript；
- desktop lint；
- 完整 Vitest 执行方范围。

所有 suite 必须通过。不得把 R1 的 8/9 files、15 tests 历史结果计为本轮通过；不得 skip/xfail、删测试或放宽断言。

## 阶段 4：desktop core readiness 与真实 Host 组合

只有阶段 1～3 全部通过才进入本阶段。严格按 P4-IF-004 完成：

- startup nonce 只通过继承环境传给 sidecar，不出现在 argv、renderer、日志或持久化；
- `GET /api/v1/desktop/readyz` 只判断 database、Alembic head 和 compiled module registry；
- 通用 `/readyz` 继续保留 provider readiness，未配置 provider 时仍 fail closed；
- `/healthz` 只表示进程存活；
- `BackendSupervisor` 以 nonce + child handle + verified port 识别 ownership，支持 single-flight、deadline、恢复预算和 bounded cleanup；
- 首次本地 owner 初始化、后续恢复、refresh single-flight、revoke/repair 和 HostClient 401 一次重试遵守冻结合同；
- Electron main 只创建一套 Supervisor、secret store、owner session、HostClient 和 runtime publisher；
- main 不再返回固定 stopped/空 modules，而返回真实脱敏 runtime 与 Host/compiled registry 交集；
- preload/renderer 不取得 token、nonce、PID、port、路径、HTTP client、Node 或文件系统能力；
- Tray quit、app quit 和 Windows session end 使用统一 bounded shutdown；隐藏窗口不停止 Host。

新增或补强执行方测试，覆盖上述边界、多次窗口/IPC 不重复创建核心对象、停止幂等和秘密扫描。

## 阶段 5：Python 与 managed sidecar smoke

只运行受影响的执行方 Python 范围和必要相邻 Host 回归，不运行独立测试。使用任务拥有的 loopback、single-worker、no-reload sidecar 验证：

1. handshake 与 nonce digest；
2. healthz；
3. desktop core readiness；
4. 通用 readyz 无 provider 时继续 fail closed；
5. owner establish、modules、recover；
6. stop 与 owned PID/port 收口。

记录任务拥有的 PID/session，最终 residual 必须为 0。

## 阶段 6：package、app.asar E2E 与真实 EXE

在冻结 lock 和精确工具链下：

1. Forge 8 package；
2. 核对 Packager 20 hooks、Vite main/preload/renderer、ASAR、fuses 和资源复制；
3. 扫描包内不得存在旧脆弱依赖、工具缓存、secret/token/nonce、个人数据、开发配置或更新 URL；
4. 对最终 app.asar 运行 E2E；
5. 对真实 `Maris.exe` 运行 startup、owner、modules、offline/recover、Tray quit 和 owned child cleanup smoke；
6. 退出后 Electron、Maris、sidecar、端口、窗口、Tray 和测试 profile 均无本任务残留。

任一真实 package/E2E/EXE 门禁失败即停止，不能用 app.asar 测试代替 EXE。

## P0 停止条件

除 P4-IF-004 原条件外，出现以下任一项立即停为 `blocked / finished`：

- E1 或 R1 manifest mismatch/missing；
- 最终 lock 审计不是 0 critical/0 high；
- frozen install 改写 lock；
- Electron 官方归档摘要不符、来源无法确认或连续两个检查点仍无法获取；
- 需要第三方镜像、旧 binary、关闭安全软件或系统级修改；
- Vitest 仍有 suite 失败；
- Host 组合需要改变 migration 或 P4-A/P4-C/P4-D 业务；
- 需要修改/运行独立测试；
- 同一问题连续两个检查点没有有效新输出。

## 交付物与完成规则

交付：

1. 实际代码、依赖、配置与执行方测试；
2. `docs/b7-r1-e1-windows-shell-running.md`；
3. `apps/desktop/b7-r1-e1-source.sha256`；
4. 更新 `docs/coordination/agents/executor.md`。

报告必须分别列出当前 final lock 的审计、安装、Electron 校验、Vitest、Python、sidecar、package、E2E、EXE、隐私扫描、资源收口和逐文件摘要。source manifest 排除自身、角色日志、`node_modules`、工具/cache、package/out、测试 profile、trace、临时日志和 `.claude/**`。

只有全部阶段通过才可提交 `review / finished`。完成后停止，不启动 P4-C12，不执行 Git 写操作，不推送远程，等待总控复算稳定快照。
