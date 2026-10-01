# C12 总控核对：P4-C12-OUTBOX-001

- 角色：头脑风暴总控。
- 时间：2026-10-01 15:29，Asia/Shanghai。
- 裁定：确认 P1 产品数据丢失缺陷 `P4-C12-OUTBOX-001`；接受 C12 的 `blocked / finished` 停止。整体 P4-B 保持 `blocked`，不进入 P4-C。
- 下一任务：[P4-B7-R2-OUTBOX 执行任务](coordination/prompts/p4-b7-r2-outbox-executor.md)。测试智能体与技术顾问保持停止。

## 本轮实际核对

总控读取产品 cleanup、main 启停接线、IF-003 §10、独立测试、首次 log/JSON 和交付核对记录，没有重跑测试或启动产品。

| 对象 | 总控实际结果 |
| --- | --- |
| C12 交付 verification 中 11 项 | 11/11 普通 SHA-256 匹配 |
| 277 项起点 | 276 unchanged、1 authorized changed（测试矩阵）、0 missing |
| 原始 Vitest JSON 与 log | 10 passed、1 failed；失败为 C12-PUB-11 |
| P4-B 矩阵 | 1 failed、19 blocked、4 not_run；0 整项 passed |

10 个公开行为节点通过只属于部分证据，不能等同于 10 个矩阵整项通过。P4-A 与 P4-C/D 的原状态不变。执行方此前的 package/EXE 成功仍保留，但不能关闭新的独立数据丢失缺陷。

## 缺陷与原因

`apps/desktop/electron/main/outbox.ts` 的 cleanup 以 `createdAt >= now - 30 days` 保留所有非 terminal 条目；超过该期限直接滤掉并持久化。main 的启动 `load → cleanup` 和退出持久化回调均走此入口，没有用户确认。

独立测试使用虚拟 draft/queued、注入时钟及内存加密 adapter。在 30 天边界保留，推进 1ms 后启动清理，再用新对象读取持久化，两条正文与 client_event_id 均消失。该公开逻辑与调用路径足以确认缺陷，不需要再次启动 EXE 复现。

IF-003 要求的是 30 天后提示用户确认删除，IF-004/005 未撤销它。问题发生在筛选与持久化逻辑，不是加密、网络、Docker 或 Windows 的故障；没有证据表明真实个人数据已丢失。

## 最小返修裁定

1. 自动 cleanup 只按原 24 小时规则清理 terminal；未提交和 sending 均不得按年龄自动删除。
2. 超过 30 天的 draft/queued 作为待用户处理内容；正文、digest 和原 client_event_id 在取消、关闭提示、退出及重启后均保留。
3. 采用现有 Electron main 的原生确认对话框，不增加 renderer 删除接口、不进入驾驶舱视觉设计。默认/关闭/取消全部保留，只在用户明确选择删除时处理当时提示的候选。
4. 确认期间变更或进入 sending 的条目不得被旧确认删除；删除与既有保存操作须有串行或等价原子边界，存储失败不得产生内存/持久状态分裂。
5. 提示每次应用启动最多一次，主窗口准备好后执行，不阻塞 Host readiness，不在退出过程中询问，不形成定时弹窗循环。
6. 20 条容量和 terminal 24 小时规则保持；容量满时仍明确拒绝，不能偷偷腾位置或重新生成原请求 ID。

现有合同已足以确定该行为，无需重新设计 Host 或额外派发技术方案。返修范围、开发自测和新 package/EXE 收口放在同一执行任务；不把每次无副作用工具错误拆成新恢复任务。执行方不得运行或修改测试方用例。

## 后续门禁

执行方提供修复、定向自测、新源码/产物摘要与真实 package/EXE 结果后，测试方才绑定新快照独立复验 C12-PUB-11、相关 outbox 边界，并继续原 C12 未完成项目。原始失败 evidence 不覆盖。

LOCALZIP 旧 EXE 含有本缺陷，不作为修复版本；只保留历史证据。多屏、Tray、开机启动等人工项目仍按原清单记录，不要求用户现在操作。前端参考图和模型策略提醒门禁保持。

Git 只保存明确的本地缺陷检查点，不推送；不是 P4-B 验收提交。
