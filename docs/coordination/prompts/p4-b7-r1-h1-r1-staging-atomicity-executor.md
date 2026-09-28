# P4-B7-R1-H1-R1 执行智能体任务卡：staging 原子替换返修

你是执行智能体，唯一负责 `P4-B7-R1-H1-R1`。本任务只修复总控发现的 `P4-H1-ATOMIC-001`，补全 replacement transition 的确定性故障测试，并重新交付 H1 source manifest。不得重做 H1 allowlist、启动 Electron 或扩大到 E3。

用户把本文件全文发送给你，即表示授权你在本任务边界内恢复锁定的 Node/pnpm 开发依赖、修改列明的 staging 脚本/声明/专属测试，并完成有限执行方自测。依赖恢复不得修改版本或 lock；不要再次要求用户确认这些已授权动作。

## 必读输入

开始前依次读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. 最新 `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze-005.md`
8. `docs/coordination/prompts/p4-b7-r1-h1-package-hygiene-executor.md`
9. `docs/b7-r1-h1-package-hygiene-running.md`
10. `docs/p4-b7-r1-h1-coordinator-review.md`
11. `apps/desktop/b7-r1-h1-source.sha256`
12. `docs/coordination/snapshots/p4-b7-r1-h1-r1-start.sha256`
13. 本任务卡

最新 control 与本任务冲突时，以 control 为准。恢复依赖或开始长操作前重新读取 control。先在 `docs/coordination/agents/executor.md` 登记接单、当前步骤、开始时间、下一检查点和可观察 session。

## 固定缺陷

当前 [stage-python-resources.mjs](../../../apps/desktop/scripts/stage-python-resources.mjs) 在新 payload 和 manifest 安装后，先后删除 payload backup 与 manifest backup；任一删除失败仍进入旧 catch。若第一个 backup 已删除、第二个删除失败，catch 会删除新 pair，但无法恢复已经删除的旧 payload，可能留下只有旧 manifest 的不一致正式状态。

现有失败测试在 source discovery 阶段通过 junction 抛错，发生在旧正式目标移动前，不能证明 replacement transition 的失败原子性。

## 起点门禁

任何修改或依赖恢复前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-h1-r1-start.sha256`，必须全部匹配。
2. 独立复算 `apps/desktop/b7-r1-h1-source.sha256`，必须为 198 matched、0 mismatch、0 missing，manifest SHA-256 为 `9e152288b5b1aaa2cb2fa979c877de617c8cdead08680e3d85430fb0b066f32e`。
3. 核对 H1 报告 SHA-256 为 `f11c99898c08565d9c0596b6c79853465cc034a39f3703923c7d05d992cc147d`，lock SHA-256 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
4. 只读确认 Electron、Maris 和项目 sidecar 没有旧任务残留；不要启动或按名称清理用户的其他进程。
5. 重读 control，确认你仍是 H1-R1 唯一负责人；E3、技术顾问、测试智能体和 P4-C12 均停止。

任一 mismatch、missing、职责冲突或未知活动进程占用时立即停止，不 restore、不 reset、不覆盖现场。

## 文件边界

允许修改：

- `apps/desktop/scripts/stage-python-resources.mjs`
- 只有类型合同实际变化时，才修改 `apps/desktop/scripts/stage-python-resources.d.mts`
- `apps/desktop/tests/unit/package-resources.test.ts`
- `docs/b7-r1-h1-package-hygiene-running.md`，以 R1 章节追加，不覆盖 H1 原始证据
- `apps/desktop/b7-r1-h1-source.sha256`
- `docs/coordination/agents/executor.md`

只读核对 `.gitignore`、Forge 配置、package wrapper、package.json、lock 与其他 H1 source。不得修改：

- H1 allowlist、staging 根、manifest 对外格式、Forge 三入口或 package wrapper 顺序
- `pnpm-lock.yaml`、依赖版本、根 workspace/package 设置
- Electron main/preload/renderer、Playwright/E2E、fuses
- Python 产品、migration 内容、Host/Finance/Agent/activity import
- `tests/independent/**`、矩阵、独立报告
- interface freeze、control、overview、其他角色状态
- `.claude/**`、Git 状态、分支或远程仓库

如果修复必须越过边界或改变冻结合同，立即停止并提交原因，不自行扩大任务。

## 修复合同

### 明确 commit point

实现必须清楚区分：

- **pre-commit**：旧正式 pair 仍是回滚目标。任一步失败后，旧 payload 与旧 manifest 必须共同恢复；新临时或部分正式对象必须清理。
- **committed**：新 payload 与新 manifest 已共同安装并通过一致性检查。此后 backup 清理失败不得进入会删除新 pair 的 pre-commit rollback；最终必须保留完整新 pair，并以安全、可恢复的方式处理或报告残留 backup。

不得出现以下最终状态：

- payload 存在而 manifest 不存在；
- manifest 存在而 payload 不存在；
- payload 与 manifest 来自不同版本；
- 函数报告成功但仍存在无法解释的 task temp/backup/lock；
- 函数报告失败并同时丢失旧、新两套完整 pair。

可以提取内部 replacement helper，或给文件操作注入只用于单元测试的窄 adapter/hook。默认生产路径必须继续直接使用 Node 标准库；不得新增 npm 依赖、全局状态、测试环境变量后门或 Electron 测试接口。

### 故障注入测试

测试必须确定性覆盖至少以下检查点：

1. 旧 payload 已移动、旧 manifest 尚未移动时失败。
2. 两个旧对象都已移动、新 payload 尚未安装时失败。
3. 新 payload 已安装、新 manifest 尚未安装时失败。
4. 新 payload 与 manifest 都已安装，payload backup 清理失败。
5. payload backup 已清理、manifest backup 清理失败，精确覆盖原缺陷。
6. 正常替换成功且没有 temp、backup 或 lock 残留。

每个失败案例都必须断言最终 pair 的完整性和版本一致性，并断言临时对象的准确状态。测试不得通过真实 ACL 破坏、管理员权限、系统文件占用、随机竞态或 sleep 制造失败。

现有 allowlist、污染排除、reparse/path、deterministic manifest、cleanup 和 Forge 静态接线断言必须保留。

## 有限验证

只运行：

1. `package-resources.test.ts`
2. 相邻 `toolchain.test.ts`
3. TypeScript `tsc --noEmit`
4. desktop lint
5. 两个 staging/package Node 脚本语法检查
6. Forge CLI metadata 静态解析，不运行 Forge package
7. 真实 source 的 stage → verify → clean，一次
8. `git diff --check`

如果 `node_modules` 不存在，允许使用固定 Node `24.21.0`、pnpm `12.7.0` 和 frozen lock 恢复依赖；安装前后 lock 摘要必须不变。不得运行 Electron、Forge package、app.asar、EXE、sidecar、Python 服务、数据库或独立测试。

## P0 停止条件

出现任一项立即停为 `blocked / finished`：

- 起点或 198 文件 H1 source mismatch/missing
- lock、依赖版本或来源漂移
- 无法在固定文件边界内保证 pair 一致性
- 故障注入只能靠系统权限、真实文件锁或不稳定竞态
- 修复要求改变 allowlist、staging 路径、Forge 三入口或 Electron 安全边界
- 需要启动 Electron、Forge package、sidecar、数据库或独立测试
- 同一问题连续两个检查点没有新证据

停止时清理任务工具、staging 和测试临时目录；保留脱敏失败证据，不通过删测试、skip/xfail 或放宽原子性断言获得通过。

## 交付物与完成规则

交付：

1. 最小脚本返修和确定性故障注入测试
2. 在 `docs/b7-r1-h1-package-hygiene-running.md` 追加 H1-R1 章节
3. 更新 `apps/desktop/b7-r1-h1-source.sha256`
4. 更新 `docs/coordination/agents/executor.md`

报告必须列出：缺陷机制、commit point、每个故障注入位置、预期最终 pair、实际结果、测试统计、lock 前后摘要、文件边界、资源收口和逐文件 SHA-256。

只有六类 replacement 测试、原 H1 测试和有限验证全部通过，source manifest 全匹配且无临时资源残留时，才可提交 `review / finished`。完成后停止，不启动 E3、P4-C12、技术顾问或测试智能体，不执行 Git 写操作，等待头脑风暴总控复算。
