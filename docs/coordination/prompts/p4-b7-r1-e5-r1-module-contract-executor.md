# P4-B7-R1-E5-R1：修复 daily_finance Profile 合同并复验最终 EXE

## 唯一目标

你是既有执行智能体，唯一负责 `P4-B7-R1-E5-R1`。E5-FINAL 已证明最终 EXE 直接启动、Host、认证、窗口和安全隔离有效；首个产品失败是 `modules.list()` 为空。

总控已把根因冻结为 `P4-E5-MODULE-001`：Python Host 和 D11 合同使用 `daily_finance.assistant@1`，桌面 contribution 及单元 fixture 错用 `daily_finance.default`，导致 strict intersection fail-closed 过滤模块。

本任务只修该合同、补强执行方回归、重新 package 一次，并在新产物上直接复验最终 EXE 一次。全部通过后停在 `review / finished`；任一真实 package 或动态门禁失败，停在 `blocked / finished`。不得启动 P4-C12、测试智能体、技术顾问或其他任务。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e5-final-blocked-coordinator-review.md`
8. `docs/b7-r1-e5-final-exe-running.md`
9. `docs/phase-4-d11-windows-shell-technical-advice.md` 第 1.1、5 和 5.1 节
10. `docs/phase-4-interface-freeze-003.md` 第 5 节
11. `docs/p4-b7-r1-e4-pkg-r2-coordinator-review.md`
12. `docs/coordination/snapshots/p4-b7-r1-e5-r1-start.sha256`

逐行复算固定快照。最新 control 若不再分配本任务，立即停止。开始时确认 Git index staged paths 为 0；`.claude/`、`.pnpm-store/`、旧 E4/E5 evidence、旧 package 和旧 profile 全部只读。

## 已确认事实

- 后端真实 Profile：`daily_finance.assistant@1`。
- 桌面错误 Profile：`daily_finance.default`。
- E5 新数据库 `module_setting` 为 0 行，不存在禁用模块的用户设置。
- 旧 app.asar 含 `daily_finance.default` 2 次，含 `daily_finance.assistant@1` 0 次。
- 首次 runtime 已达到 `online / managed / authenticated`，所以不修改认证或 Supervisor。
- 最终 EXE 直接 `spawn(shell:false)` 路线有效；不返回 Playwright Electron launcher。

## 仓库修改范围

允许修改：

- `apps/desktop/src/modules/daily-finance/contribution.ts`
- `apps/desktop/tests/unit/registry.test.ts`
- `apps/desktop/tests/unit/composition-root.test.ts`
- `apps/desktop/tests/unit/host-client.test.ts`
- 如现有测试组织确实需要，可新增一个仅覆盖真实 Profile 合同的执行方单元测试文件；不得建立平行 registry 或复制 Python 实现
- 更新 `docs/coordination/agents/executor.md`
- 新建 `docs/b7-r1-e5-r1-module-contract-running.md`
- 新建 `apps/desktop/b7-r1-e5-r1-source.sha256`

禁止修改 Python Host、registry 算法、认证、Supervisor、IPC、preload、renderer 页面、依赖、lock、Forge、staging、migration、接口冻结、独立测试、control、overview、其他角色或 Git 状态。

`settings: [{ key: "preferences" ... }]` 不是本次 `daily_finance_missing` 的触发条件；除非执行方用现有冻结合同和实际调用证明它阻断本任务，不得顺手扩大修改。

## 实现要求

1. 把 daily finance contribution 的 `agentPanel.profileId` 改为 `daily_finance.assistant@1`。
2. 把 registry、composition root 和 HostClient 单元 fixture 中的 daily finance Profile 改为真实 ID。
3. registry 测试必须同时证明：
   - 真实 Profile 加载；
   - `daily_finance.default` 不匹配并返回空交集；
   - major version 不兼容仍被拒绝。
4. composition root 测试必须用生产同形摘要证明公开模块列表包含且只包含受支持的 `daily_finance`。
5. HostClient 测试保持严格响应校验、401 refresh/retry 和错误边界，不降低断言。
6. 修改完成后，`rg` 在 `apps/desktop/src` 和 `apps/desktop/tests` 中对 `daily_finance.default` 必须 0 命中。

不得给 `intersectModules()` 增加别名、fallback、宽松匹配或自动改写；旧错误 ID 必须失败关闭。

## 静态与执行方回归

在任何 package 前依次完成：

- 修改文件语法/格式检查；
- OpenAPI generated drift；
- TypeScript `tsc --noEmit`；
- desktop lint；
- registry、composition root、HostClient 定向 Vitest；
- desktop 完整 Vitest；
- 与 desktop sidecar/module 相关的 Python 定向测试；
- Python `compileall` 和 `pip check`；
- `git diff --check`。

任何产品断言失败立即停止，不得进入 package。环境或测试编排错误可以按项目规则记录并在没有运行产品的前提下修正，但不得删除测试、降低断言、增加 skip/xfail 或把收集结果写成通过。

## 新 C 盘构建现场

旧 `C:\MarisE4\E4-20260928-1255` 和其中全部 workspace、out、evidence、profile、工具与清单保持只读。不得覆盖旧 package 证明。

创建全新的任务根：

```text
C:\MarisE5R1\E5-R1-<timestamp>
```

在新根中：

- 复制固定工具和依赖时逐项核对来源摘要；不得下载或安装新依赖；
- 从当前仓库复制本任务固定 source 集，不能复制旧错误 contribution 覆盖修复；
- 使用旧任务已验证的 Node、pnpm、Electron cache 和依赖图；
- `pnpm-lock.yaml`、Electron dist 和依赖摘要必须与冻结输入匹配；
- 新 evidence、workspace、out、profile 和数据库都必须 create-new；
- 不读取或复用旧 owner session、数据库、PID、端口或动态结果。

如果无法在不修改依赖或旧现场的前提下建立新 C 盘 workspace，记录阻塞并停止，不得退回 D 盘 Electron launcher 或联网安装。

## 唯一 package

静态回归全部通过后，允许在新 C 盘 workspace 执行一次现有 `pnpm run package`，预算 1/1。使用 PKG-R2 已验证的进程级 pnpm/Node PATH 配方，不修改用户或系统 PATH。

package 非零、超时、崩溃、污染或残留时立即停止。不得修改后重跑。

package 成功后只读验证：

- 新 `Maris.exe`、`resources/app.asar`、out 清单和 production fuses；
- app.asar 中 `daily_finance.assistant@1` 至少出现一次，`daily_finance.default` 为 0；
- 67 项 Python resources 仍符合 H1 allowlist；
- `.pyc`、`.egg-info`、测试、任务 evidence、用户路径、凭据样式和私钥均为 0 命中；
- staging、backup、lock 和 transition artifacts 已清理；
- source、lock、node_modules 和 Electron dist 没有非授权漂移。

## 最终 EXE 单次动态复验

只有 package 和静态产物检查全部通过才进入本节。最终 EXE 动态预算 1/1，硬超时 120 秒，不预跑 app.asar，不运行 fixture，不重试。

沿用 E5 已证明有效的路线：

- 固定 Node `child_process.spawn()` 直接启动新 package 的 `Maris.exe`；
- `shell:false`，返回 PID 必须精确对应新 EXE；
- 新隔离 profile、虚拟数据库、随机 owner marker、最终 resources 和已验证 Python；
- 动态非零 CDP 只监听 `127.0.0.1`；Playwright 只用 `connectOverCDP()`；
- 不传 `--no-sandbox`，不启用 inspect，不改变 fuses。

依次验证：

1. 根进程、owned set、CDP 和两个窗口；
2. 主窗口与毛毛 preload bridge、Node 隔离和未授权 API 缺失；
3. runtime `online / managed / authenticated / errorCode=null`；
4. `modules.list()` 含且只公开兼容的 `daily_finance`，其 `profile_ids` 含 `daily_finance.assistant@1`；
5. 毛毛 `getState()` 为 daily finance 形态，`openMain()` 成功且不创建重复主窗口；
6. `runtime.recover()` 精确调用一次；恢复后 runtime 和 module 仍通过；
7. DOM、storage、bridge、console、page error、crash event、Windows Application/Code Integrity 和日志隐私；
8. 使用产品现有 bounded shutdown，自然退出码 0；最终产品、sidecar、监听、窗口和 Tray 归零。

若任一门禁失败，保留首个失败和原始证据，安全收口后提交 `blocked / finished`。不得在同一任务修改后进行第二次 package 或第二次最终 EXE 启动。

## 交付与状态

运行说明必须包含：

- `P4-E5-MODULE-001` 的代码位置、根因和修复；
- 旧假 fixture 如何掩盖缺陷以及新反例；
- 每组回归的 passed/failed/skipped/warning；
- package 真实次数、产物摘要、fuse/resource/污染检查；
- 最终 EXE 真实次数、每个动态门禁、recover 次数和资源收口；
- 起点/终点文件边界、逐文件 SHA-256 和新 source manifest；
- 新 C 盘 evidence 清单与复算算法；
- 未运行的独立验收、P4-C12、真实微信、DeepSeek 和个人数据。

全部通过后提交 `review / finished`，停止修改，等待总控复算。不得自行宣布 P4-B complete，不得启动测试智能体或高保真前端开发。
