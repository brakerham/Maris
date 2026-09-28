# P4-B7-R1-H1-R1 总控核对

核对时间：2026-09-28 08:57，Asia/Shanghai
核对角色：头脑风暴总控

## 1. 结论

`P4-H1-ATOMIC-001` 已关闭。H1-R1 把 staging replacement 明确分成提交前与提交后两个阶段：新 payload 与 manifest 共同安装并重新核对内容之前，任何失败都恢复完整旧 pair；共同安装且一致性复核完成之后，backup 清理失败只报告结构化的 committed cleanup error，不再删除已经提交的新 pair。

H1-R1 接受为 `P4-B7-R1-E3` 的固定输入。这个结论表示 package resource 静态 staging 切片可以继续向动态环境门禁流转；它不等于 P4-B 独立验收、Windows 桌面应用可运行、P4-C12 通过或产品发布完成。

## 2. 快照与边界核对

| 核对项 | 总控结果 |
| --- | --- |
| H1-R1 起点清单 | 209 entries；203 unchanged，6 authorized changed，0 missing，0 非授权 mismatch；清单 SHA-256 `cd77aa32af97f6a3b894d05a563583c745c3090b49cea7d47737a5fc697fcbe7` |
| 6 个授权变化 | staging `.mjs`、`.d.mts`、专属测试、H1 运行说明、198 文件 source manifest、执行智能体状态 |
| H1 终点 source manifest | 198/198 matched，0 missing，0 mismatch；manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| staging 实现 | SHA-256 `8a81d9671e3789ce0d21ffbaad657f83ddf737c6188e3d87f9adcc7d76c17f9c` |
| TypeScript 声明 | SHA-256 `a945fdab17b256b388fc24b610f833d380e3dddd4fcc977364dd50b222af63c3` |
| 专属测试 | SHA-256 `1fc77f04469df00b350455f4d682a0704f7410626e000eac071473c3435132e1` |
| lock | `pnpm-lock.yaml` 仍为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| 临时资源 | `node_modules`、`.maris-staging`、out、Vite、test-results、Playwright report 与 H1-R1 工具目录均不存在；Electron/Maris 进程为 0 |

总控没有复跑完整 Node 依赖安装或 16 项测试。项目流水线规定在固定 source manifest 全匹配、报告与代码一致且没有冲突证据时，协调者做定向代码核对，不重复执行方的完整自测。本次核对了提交点、两类错误语义、六个注入位置、finally 清理分支和终点摘要。

## 3. 原缺陷如何关闭

提交点现在位于以下四个事实全部成立之后：

1. 新 payload 已通过同卷 rename 安装到正式目标；
2. 新 manifest 已安装到正式目标；
3. 正式 payload 的路径、bytes 与 SHA-256 再次匹配 source entries；
4. 正式 manifest 文本与同一 entries 的确定性序列化完全一致。

`committed=false` 时，catch 会删除已经安装的新对象，再按旧 payload、旧 manifest 的 backup 恢复正式 pair。若回滚本身失败，代码抛出 `staging_precommit_rollback_failed` 的 `AggregateError` 并保留仍可用于恢复的 backup。

`committed=true` 时，backup 清理错误带 `STAGING_COMMITTED_CLEANUP_FAILED`、`committed=true`、准确的 `cleanupStep` 与 `recoverableBackups` 返回。catch 不再进入旧回滚，finally 也不会删除 recovery backup，因此完整新 pair 保持正式状态。

旧 payload 与旧 manifest 只有一侧存在时，replacement 在移动任何正式对象之前以 `staging_existing_pair_incomplete` 拒绝继续。测试注入只通过 `beforeReplacementStep(step)` 的窄内部 hook 实现；生产默认路径没有环境变量、全局开关、Electron 接口或新依赖。

## 4. 六个故障边界

| 边界 | 代码/测试结论 |
| --- | --- |
| 旧 payload 已移动，旧 manifest 尚未移动 | 在 `move-old-manifest` 前注入失败，完整旧 pair 恢复，transition artifacts 为 0 |
| 两个旧对象已移动，新 payload 尚未安装 | 在 `install-new-payload` 前注入失败，完整旧 pair 恢复，transition artifacts 为 0 |
| 新 payload 已安装，新 manifest 尚未安装 | 在 `install-new-manifest` 前注入失败，删除部分新对象并恢复完整旧 pair |
| 新 pair 已验证，payload backup 清理失败 | 保留完整新 pair，并保留两份可恢复旧 backup |
| payload backup 已删除，manifest backup 清理失败 | 保留完整新 pair，仅保留旧 manifest backup；原 P0 路径被精确覆盖 |
| 正常 replacement | 新 pair 与返回 entries 一致，temp、backup 与 lock 为 0 |

执行方报告记录专属测试 14/14、专属加相邻 toolchain 16/16、TypeScript、lint、Node syntax、Forge metadata 静态解析和真实 source 67/67 stage→verify→clean 全部通过。Electron、Forge package、app.asar、Maris、sidecar、数据库与独立测试均未运行，符合 H1-R1 边界。

## 5. 后续门禁

下一步是 `P4-B7-R1-E3`，只做 D13/IF-005 冻结的 C 盘三角验证：

1. 同摘要 Electron `44.4.5` 与同一最小 fixture 在 C 盘短 ASCII 任务根直接启动一次；
2. 只有 direct 完全成功，才在同目录、同 fixture 下通过 Playwright 默认 loader 启动一次；
3. 任一启动出现 `0xC0000135`、`0x80000003`、新非零退出、Windows 弹窗、证据记录失败或 owned process 无法收口时，整个 E3 立即停止并交回总控；
4. E3 不运行 Procmon、诊断安全开关、版本对照、app.asar、Forge package、Maris.exe、Host、数据库或 P4-C12。

H1-R1 后续不再修改。E3 的动态结果出来前，P4-B 仍保持开发中，24 项 P4-B 独立矩阵保持 `not_run`。
