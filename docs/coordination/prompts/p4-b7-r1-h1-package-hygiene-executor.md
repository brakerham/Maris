# P4-B7-R1-H1 执行智能体任务卡：Python package resource 静态 staging

你是执行智能体，唯一负责 `P4-B7-R1-H1`。本任务只实现 Python runtime source allowlist、确定性 staging、manifest 和静态/单元测试。它不处理 Electron Windows 启动崩溃，不启动 Electron、Forge package、app.asar、Maris.exe、sidecar 或数据库。

用户把本文件全文发送给你，即表示授权你在本任务边界内恢复项目锁定的 Node/pnpm 开发依赖、修改列明的桌面 package 配置/脚本/执行方单元测试，并生成交付证据。依赖恢复不得修改版本或 lock；不要再次要求用户确认这些已授权动作。

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
9. `docs/phase-4-interface-freeze-005.md`
10. `docs/phase-4-d13-electron-windows-crash-advice.md`
11. `docs/p4-d13-coordinator-review.md`
12. `docs/b7-r1-e2-windows-shell-running.md`
13. `docs/b7-r1-e2-r1-windows-shell-running.md`
14. `apps/desktop/b7-r1-e2-r1-source.sha256`
15. `docs/coordination/snapshots/p4-b7-r1-h1-start.sha256`
16. 本任务卡

最新 control 与本任务冲突时，以 control 为准。恢复依赖或运行超过五分钟的操作前，重新读取最新 control。先在 `docs/coordination/agents/executor.md` 登记接单、当前步骤、开始时间、下一检查点和可观察 session。

## 已确认且不得重复的事实

- `P4-D13` 已由总控接受；根因仍是未命名 DLL/装载机制，H1 不调查或修复 Electron 环境。
- 既有 D 盘最小 fixture 已触发 GPU child `0xC0000135`、后续 `0x80000003` 弹窗；禁止重跑。
- Electron `44.4.5`、Forge/Playwright 和 lock 继续冻结；H1 不升级、降级或 patch 第三方依赖。
- E2 已发现最终 package 带入 11 个 `.pyc` 和 6 个 `.egg-info`；这证明 source 直接复制存在独立 hygiene 缺口。
- `apps/desktop/b7-r1-e2-r1-source.sha256` 为 194 matched、0 mismatch、0 missing，manifest SHA-256 为 `d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715`。
- H1 只证明 staging/allowlist 静态行为；Forge package、最终 resources、app.asar、fuses、EXE 与 sidecar 都必须报告 `not_run`。

## 起点门禁

任何修改或依赖恢复前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-h1-start.sha256`，必须全部匹配。
2. 独立复算 `apps/desktop/b7-r1-e2-r1-source.sha256`，必须为 194 matched、0 mismatch、0 missing。
3. 核对 D13、总控审阅、P4-IF-005 和执行智能体现状。
4. 只读确认 Electron、Maris 和本项目 sidecar 没有由旧任务遗留的活动进程；不要启动、停止或按名称清理用户的其他进程。
5. 重读最新 control，确认你仍是 H1 唯一负责人；技术顾问、测试智能体、E3 与 P4-C12 均停止。

任一 mismatch、missing、职责冲突或未知旧任务进程占用时，立即停止，不 restore、不 reset、不覆盖现场。

## 文件边界

允许修改：

- `apps/desktop/.gitignore`
- `apps/desktop/forge.config.ts`
- `apps/desktop/package.json`
- 新建或修改 `apps/desktop/scripts/stage-python-resources.mjs`
- 新建或修改 `apps/desktop/tests/unit/package-resources.test.ts`
- 如实现需要，可在 `apps/desktop/scripts/` 下新增只服务于 staging 的小型模块，但必须在报告中说明理由
- `docs/b7-r1-h1-package-hygiene-running.md`
- `apps/desktop/b7-r1-h1-source.sha256`
- `docs/coordination/agents/executor.md`

可以只读核对其他源文件。不得修改：

- `pnpm-lock.yaml`、`.node-version`、`.npmrc`、根 workspace/package 定义或任何依赖版本
- Electron main/preload/renderer 产品代码、security、fuses、E2E 和 Playwright launcher
- Python 产品代码、migration 内容、Host/Finance/Agent/activity import 语义
- `tests/independent/**`、测试矩阵、独立报告
- interface freeze、control、overview、其他角色状态
- `.claude/**`
- Git 状态、分支或远程仓库

如果正确实现必须越过边界或改变 runtime allowlist，停止并把具体路径、原因和最小扩展建议交回总控。

## 固定实现合同

### staging 根

使用被忽略的：

```text
apps/desktop/.maris-staging/python-runtime
```

每次构建先在 `.maris-staging` 下创建 task-owned 临时 sibling，完成所有路径与摘要验证后再原子替换 `python-runtime`。开始时存在旧 staging、未知文件或上次中断半成品时，新运行不能继承它们。成功、失败和测试结束后清理本任务临时 sibling；交付时不保留生成内容。

### allowlist

只复制：

```text
alembic.ini
migrations/env.py
migrations/versions/*.py
src/wife_system/**/*.py
```

显式拒绝：

```text
**/__pycache__/**
**/*.py[cod]
**/*.egg-info/**
tests/**
.pytest_cache/**
build/**
dist/**
scratch/**
任意 symlink、junction、reparse point
任意绝对路径、.. 越界、源根外路径
任意未列入 allowlist 的文件类型
```

`migrations/README` 与 `migrations/script.py.mako` 不复制。若现有 sidecar/migration 代码静态证明它们是运行必需项，先停止并返回证据，不自行扩大 allowlist。

### manifest

为 staging 生成排序稳定的 manifest。每行或每项只含：

- POSIX 风格相对路径
- 字节数
- SHA-256

manifest 不得含绝对路径、用户名或时间戳等非确定性字段。staged 路径集合必须精确等于 allowlist 展开集合，每个摘要必须等于 source。

### Forge 静态接线

`forge.config.ts` 的 `extraResource` 只引用 staging 中的三个入口：`alembic.ini`、`migrations`、`src`，并保持最终 runtime 需要的相对布局。允许增加在 package 前准备 staging、在 package 完成或失败后清理 owned staging 的 hook/脚本接线，但本任务不得实际运行 Forge package。

不要依赖 `.gitignore` 作为 package filter。`.gitignore` 只负责禁止 `.maris-staging` 进入版本控制。

## 执行方测试

新增专属 Vitest/static tests，至少覆盖：

1. 正常 source tree 的精确路径集合、大小和 hash。
2. source tree 存在测试专属 `__pycache__`、`.pyc`、`.pyo`、`.egg-info`、测试文件和未知扩展时均为零命中。
3. 目标 staging 预先存在旧文件时，新运行不会保留旧内容。
4. staging 失败时不会把半成品替换为正式目标。
5. symlink、junction/reparse、绝对路径、`..` 与源根外路径 fail closed。
6. `alembic.ini`、`migrations/env.py`、全部现有 revision `.py` 和 `src/wife_system/**/*.py` 完整存在。
7. manifest 排序与内容确定，且不含个人绝对路径。
8. Forge 配置只引用 staging 三入口，旧的 `../../src`/`../../migrations` 整目录直接复制合同消失。

只运行新增/受影响的 Vitest 与必要的 TypeScript/static check。可以复用现有锁定依赖；若 `node_modules` 不存在，允许按项目固定 Node `24.21.0`、pnpm `12.7.0` 和 frozen lock 恢复依赖。恢复前后 `pnpm-lock.yaml` 摘要必须不变。不得运行 Electron、Forge package、app.asar、EXE、sidecar、Python服务、数据库或独立测试。

## P0 停止条件

出现任一项立即停为 `blocked / finished`：

- 起点或 194 文件 source mismatch/missing
- frozen install 改写 lock、依赖来源/版本漂移或需要新增依赖
- staging 不能在不跟随 reparse/symlink 的条件下 fail closed
- 必须复制 allowlist 外文件才能满足现有 runtime 合同
- Forge 静态接线要求修改 Electron 产品代码、fuses 或运行时业务
- 测试需要启动 Electron/Forge package/sidecar/数据库
- 需要修改独立测试、矩阵、冻结、control、overview 或越过文件边界
- 同一问题连续两个检查点没有新证据

停止时清理本任务 staging、测试污染物和临时依赖工具，保留脱敏失败证据；不得通过删除断言、skip/xfail 或扩大 allowlist 获得通过。

## 交付物与完成规则

交付：

1. 授权范围内的 staging 实现、Forge 静态接线和执行方单元测试
2. `docs/b7-r1-h1-package-hygiene-running.md`
3. `apps/desktop/b7-r1-h1-source.sha256`
4. 更新 `docs/coordination/agents/executor.md`

报告必须包含：起点复算、变更文件、allowlist/reject list、原子替换、manifest、测试统计、lock 前后摘要、未运行项目、临时资源收口和逐文件 SHA-256。

只有专属测试和必要 static check 通过、lock 不变、staging/污染物清理、文件边界准确后，才可提交 `review / finished`。明确写出：

> source allowlist staging 与静态测试已通过；Electron/Forge package、app.asar、fuse、最终 resources 扫描、sidecar 和 EXE 启动均为 `not_run`。该结果没有解除 P4-B 的 Electron 环境阻塞，也不构成发布验收。

完成后停止，不启动 E3、P4-C12、技术顾问或测试智能体，不执行任何 Git 写操作，等待头脑风暴总控复算终点快照。
