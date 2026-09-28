# P4-B7-R1-H1 总控核对：package resource 静态 staging

核对时间：2026-09-28，Asia/Shanghai
核对角色：头脑风暴总控
结论：`review / needs_fix`；H1 的 allowlist、静态接线和大部分测试证据有效，但 `P4-H1-ATOMIC-001` 阻止总控标记 complete

## 1. 有效交付

总控接受以下执行方证据：

- 209 文件起点复算结果为 205 matched、4 个授权文件变化、0 missing、0 invalid；变化文件精确为 `.gitignore`、Forge 配置、desktop package 配置和执行智能体状态。
- H1 source manifest 为 198 entries，复算结果 198 matched、0 mismatch、0 missing；manifest SHA-256 为 `9e152288b5b1aaa2cb2fa979c877de617c8cdead08680e3d85430fb0b066f32e`。
- `pnpm-lock.yaml` 前后 SHA-256 保持 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- source allowlist 精确覆盖 `alembic.ini`、`migrations/env.py`、`migrations/versions/*.py` 与 `src/wife_system/**/*.py`；`.pyc`、`.pyo`、`.pyd`、`.egg-info`、测试、cache、build、dist 和未知扩展不进入 payload。
- Forge `extraResource` 已从直接复制仓库 `src/migrations` 改为只读取 `.maris-staging/python-runtime` 下三个固定入口；package wrapper 固定为 stage → Forge → finally cleanup。
- 执行方报告记录专属 8 passed、相邻合计 10 passed、TypeScript/lint/syntax/static metadata 通过；真实 source staging 为 67 entries、67 payload、0 forbidden、0 missing。
- 最终 `node_modules`、任务工具、`.maris-staging`、out、Vite、Playwright 和测试输出均不存在；Electron、Maris、项目 Python/Pythonw 进程为 0。
- Electron、Forge package、app.asar、fuses、最终 resources、sidecar 和 EXE 均准确登记为 `not_run`，没有冒充发布验收。

## 2. 阻断缺陷 `P4-H1-ATOMIC-001`

位置：[stage-python-resources.mjs](../apps/desktop/scripts/stage-python-resources.mjs) 的替换提交与 backup 清理段。

当前顺序是：

1. 旧 payload 重命名为 payload backup；
2. 旧 manifest 重命名为 manifest backup；
3. 新 payload 安装到正式路径；
4. 新 manifest 安装到正式路径；
5. 删除 payload backup；
6. 删除 manifest backup；
7. 上述任一步抛错都进入同一个 catch 并尝试回滚。

如果第 5 步已经成功，而第 6 步因文件占用、权限或暂时 I/O 错误失败，catch 会删除已经安装的新 payload 和 manifest，然后尝试恢复两个旧 backup。旧 payload backup 已在第 5 步删除，无法恢复；旧 manifest 仍可恢复。函数最终抛错，但正式 staging 可能只剩旧 manifest，没有 payload。

这不是个人数据或生产数据库损坏风险，因为 staging 是可再生成的构建输入；但它违反 H1 冻结的“失败不能把已存在的正式 staging 变成半成品”和执行方报告中的“失败回滚”结论，因此是 H1 接受前必须关闭的 P1 构建正确性缺陷。

## 3. 现有测试为什么没有覆盖

当前测试 `keeps the previous target intact and removes temporary siblings on failure` 通过在 source tree 中放置 junction 触发 `resource_reparse_rejected`。该异常发生在新 staging 构建和旧正式目标重命名之前，因此只能证明“准备阶段失败不会触碰旧目标”。

它没有覆盖：

- 旧 payload 已移动、旧 manifest 尚未移动时失败；
- 两个旧目标都已移动、新 payload 尚未安装时失败；
- 新 payload 已安装、新 manifest 尚未安装时失败；
- 新 payload 与 manifest 都已安装，但任一 backup 清理失败；
- 回滚自身遇到错误时是否保留原始异常并留下可恢复状态。

## 4. 最小返修边界

`P4-B7-R1-H1-R1` 只允许：

1. 为 staging 文件操作增加可测试的窄接口或内部 helper；默认生产路径仍使用 Node 标准库，不增加依赖。
2. 明确定义 commit point：在 commit point 前失败必须恢复旧 payload+manifest；在 commit point 后的 backup 清理不得再进入会删除新正式 pair 的旧回滚路径。
3. 对 replacement transition 的关键步骤增加确定性故障注入测试，至少覆盖旧目标移动、新目标安装和 backup 清理。
4. 保证函数返回成功时，新 payload+manifest 完整匹配；返回失败时，旧完整 pair 保留，或在已经越过明确 commit point 时新完整 pair 保留。禁止出现只有 payload 或只有 manifest 的最终状态。
5. 保持 allowlist、staging 路径、Forge 三入口、lock、依赖、Electron 安全边界和 H1 的 `not_run` 口径不变。

不要求重做 H1 的依赖调查、Electron/Forge package、sidecar、数据库或全部桌面测试。返修执行方只跑专属 staging 测试、相邻 toolchain、TypeScript、lint、两个 Node syntax check 和静态 metadata；新增故障注入不得依赖真实权限破坏或修改系统设置。

## 5. 状态与下一步

- H1 保持 `review / finished`，不标记 `complete`。
- 当前不创建 H1 验收提交；上一份 D13 文档检查点保持不变。
- E3 与 P4-C12 继续 `not_started`。
- 下一步由既有执行智能体接收 `P4-B7-R1-H1-R1`，只关闭 `P4-H1-ATOMIC-001` 并生成新稳定 source manifest。
