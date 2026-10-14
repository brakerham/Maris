# P4-C12-R8-R1 总控核对与正常退出返修裁定

2026-10-14，Asia/Shanghai。接受本轮独立通过的有限范围及UI-01整项通过；确认QUIT-001为待修复P1。原任务保持 `blocked / finished`，LAZY-001、UI-02、CMP-03、SUP-05及P4-B未关闭。测试方停止，下一任务交既有执行智能体。

## 实际核对与接受范围

[R8-R1报告](testing/phase-4-c12-r8-r1-modules-windows-report.md)、测试源码与首次结果已核对。总控复算[82项交付](../tests/independent/desktop/evidence/r8-r1/delivery.sha256)全部匹配，摘要 `437bcded2f0accc0e55e63cb411a48dc1414d76f659e70ddf4cc48a455a6fd58`。四组冻结源码分别6/4/5/2项、首次材料分别6/5/6/2项全部匹配；public使用source-final，Windows使用实际attempt1清单，初版失败保留。

| 范围 | 已证事实 | 接受边界 |
| --- | --- | --- |
| 旧R8-01至09 | 历史9节点通过且不变 | 不计本轮新增通过、不重跑 |
| R8-10至13 | 本轮4通过，184个正式比较唯一配对且全部通过；5工具自检单列 | 与旧9共同完成13节点模块同步及最小邻接保护 |
| 开发兼容 | 28通过 | 执行方测试的兼容层，不计独立节点 |
| 新公开条件 | 6通过，21比较 | 虚拟DTO/生成漂移控制流及真实启动静态接线；不代替实际CI/export或全部UI-03 |
| Windows W1 | 57对完整记录，56通过、1失败 | 页面/安全/一次恢复的已测子条件成立，正常退出失败 |
| 退出与清理 | 10秒内未退出；随后测试方强制收口，登记对象及监听最终为0 | 不算产品正常退出，不推断未取得原生码的历史子进程退出原因 |

848项起点在测试方结束时844不变、4共享文档授权变化；本轮总控协调变化另列。旧主报告和人工清单仅追加。矩阵120个唯一ID、12列不变，只改三项状态：UI-01 blocked→passed、CMP-03 blocked→failed、SUP-05 not_run→failed；原预期和A/C/D保持。P4-B为1 passed、3 failed、17 blocked、3 not_run。

UI-01原要求为只渲染两侧存在且兼容模块，未知/禁用不导航、不预载。旧9+新4独立注册器/真实Router/Shell覆盖全部交集条件，W1固定新包日常页面也取得实机存在/数量/可见性及恢复后的有效样本，接受UI-01整项passed。不把这个接受扩展为UI-02真实chunk故障、跨重启会话、其他关闭策略或整个P4-B完成。

外部R6包和完整环境的不变性由本轮start/end审计逐项记录（813构建源码、140产物、67资源、73dist、12443依赖及12677完整inventory）；总控当前另复算EXE、asar和lock精确匹配冻结摘要。总控本轮只核对清单与结果，不运行产品、测试、服务或打包。

## QUIT-001事实与根因边界

首次证据见[Windows result](../tests/independent/desktop/evidence/r8-r1/windows-W1/result.json)、[journal](../tests/independent/desktop/evidence/r8-r1/windows-W1/journal.jsonl)、[只读分析](../tests/independent/desktop/evidence/r8-r1/windows-first-analysis.json)。新虚拟profile实际 `closePolicy=quit`、`closeHintShown=false`、`companionVisible=true`，已排除E2E自动退出计时器。root路径、创建时间、父子链与场景身份有证据，原生helper仅对该root的唯一Maris主窗口投递WM_CLOSE。

seq121–122证明请求成功投递；不将PostMessage成功外推为所有应用事件已被处理。seq123–125的 `W1-NORMAL-EXIT-OBSERVED` 明确expected=true、actual=false；10秒后root仍存在、7个当时自有进程和2个loopback监听。持久配置仍quit，随后定向强制清理，自有对象/监听归零。场景不是初始化失败、缺样本或仅测试编号错误。

实际 [main入口](../apps/desktop/electron/main/index.ts) 第103行的close监听器只在策略不是quit时拦截并调用handleClose；quit直接放行主窗口默认关闭，没有调用requestQuit。统一退出实际由requestQuit/app.quit→before-quit→shutdown进入，window-all-closed也只在quitting时调用app.quit。此代码缺少显式quit策略的退出接线，与实测一致；历史首次没有逐个生命周期事件记录，不能补造其内部完整顺序。执行方需用真实main的事件回归确认红绿，再用新包验证正常关闭。

原冻结IF-003要求quit统一退出并只清理owned后端，IF-004-F19要求统一bounded shutdown及重复quit幂等。没有新增退出API或改变架构的必要。旧开发smoke允许E2E计时requestQuit或WM_CLOSE两种入口，前者通过不能证明后者接线；新任务只允许普通关闭作为最终退出门禁，不将旧冒烟改写为该门禁通过。

## 下一步

发布[P4-B7-R7-QUIT](coordination/prompts/p4-b7-r7-quit-executor.md)：仅main/index.ts、新main关闭执行方测试、运行说明/source清单和本人日志五文件。先实际main红灯，再最小修复及关闭策略/重入邻接保护；一次完整开发回归、一次新包、一次真实EXE，必须quit+毛毛可见+无退出timer，通过普通WM_CLOSE和10秒退出观察。

保留已通过独立13节点及其余有限证据；新包独立复验需另由总控定向派发，不让执行方运行独立测试或关闭缺陷。不重复旧EXE/旧W1，也不为普通代码接线缺口新建顾问诊断轮次。产品额外范围、新接口、安全或无法收口的问题按新卡停止。

新起点：[R7固定清单](coordination/snapshots/p4-b7-r7-quit-start.sha256)。新任务ready/waiting_user、接单unverified；测试方和顾问停止。只保存准确的本地待返修检查点，不推送；前端参考图/模型分工提醒仍在P4-C开始前触发。

本地归档格式例外：暂存检查在冻结证据 `tests/independent/desktop/evidence/r8-r1/preflight/readiness.test.tsx.diff` 第59行发现尾随空白，该行是原始补丁表示空白上下文的内容。原字节匹配82项交付，保持不修改；其余暂存文件差异格式检查通过。整体cached检查首次退出1如实保留，不把该证据改字节以获得全绿。
