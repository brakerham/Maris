# C12-R1 总控核对：关闭 outbox P1，接受 registry P1 并冻结返修

- 角色：头脑风暴总控。
- 核对日期：2026-10-02，Asia/Shanghai。
- 输入：[C12-R1 独立报告](testing/phase-4-c12-r1-outbox-windows-report.md)、原始分组 JSON/log、[C12-R1 起点](coordination/snapshots/p4-c12-r1-start.sha256)、IF-003 §5及实际 registry 代码。
- 本轮只读证据和定向代码核对，未重跑测试、启动产品或修改产品。

## 两项裁定

1. **关闭 `P4-C12-OUTBOX-001`**，范围为未经确认的老化消息持久删除问题及相邻确认/并发/失败恢复逻辑。原 PUB-11 文件和断言不变，新首次运行证明 30 天 +1ms 经 load→cleanup→reload 保持两条虚拟消息、正文、digest 和原 ID。原其余十项、新 outbox 26 项、可执行 main 5 项均通过。
2. **接受 `P4-C12-R1-REGISTRY-001` 为待修 P1**。IF-003要求 setting 全局唯一，但 `compileRegistry()` 使用 `setting:${item.moduleId}:${setting.key}` 查重，两个模块的同名键得到不同 seen key，实际接受两个贡献。独立 `R1-SHELL-13` 首次失败与实现一致；无需总控第三次运行该失败。

outbox 缺陷关闭不等于 SUP-06 或 P4-B complete：真实 Windows 原生老化提示、恢复提交及原场景尚未覆盖，SUP-06 继续 blocked。新缺陷是已冻结注册合同未落实，不是新的架构需求；不把它解释为已发生真实财务覆盖或权限漏洞。技术顾问不需重复选型。

## 实际复算结果

| 项目 | 总控本轮核对 |
| --- | --- |
| 测试方交付列出的新文件和更新文件 | 28/28 SHA-256 匹配 |
| 原296文件起点 | 292 unchanged、4 authorized changed、0 missing/非授权差异 |
| 原八项独立代码/首次证据 | 精确不变 |
| 原主报告及人工清单 | 原前缀完整保留，仅追加 |
| 独立运行原始JSON | 原节点1+10、新outbox26、main5、其余Shell17 passed/1 failed |
| 独立唯一实际执行节点 | 60，59 passed、1 failed；没有把filter未选项计为执行 |
| 执行方兼容 | 27 passed，独立统计 |
| 真实产品/辅助Electron | 0/8、0/4，未执行 |
| 原矩阵 | A64 passed；B1 failed/19 blocked/4 not_run；C20/D12 not_run |
| 新R2 EXE、app.asar、lock | 现存文件实际复算与固定摘要匹配 |

四项起点内授权变化仅 tester、旧C12主报告、人工清单、P4矩阵；总控不修改测试角色或独立材料。原始八项与本轮首次失败保留。

新R2 EXE SHA-256：`8eb56f3f63b923471a9239e2a01f29a8111067a6093d8c9d118e62e1ccfb5c2a`。

app.asar SHA-256：`74225ea63dbc7201dc7f7f3299a099ac573f51680ef705536e560a9d9df6b6c7`。

lock SHA-256：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

## 最小后续范围

发布 [P4-B7-R3-REGISTRY](coordination/prompts/p4-b7-r3-registry-executor.md)：仅更正全局 setting 冲突检查、补跨模块回归，保留同模块冲突、canonical Profile、Host intersection 和其他身份冲突行为。用同一任务完成必要开发验证及新版package/EXE，避免拆成多次工具恢复任务。

使用R2已验证普通依赖和官方本地ZIP，在新隔离副本构建；旧R2产物/证据保持只读。修改renderer模块源码后新asar必须重新生成，但不重跑Python/P0～P3，不扩展真实业务UI。

测试方C12-R1保持 blocked/finished；新的测试续跑尚未派发。执行方自测后只能review/finished，由总控核对新快照再安排原失败节点独立复验和未执行Windows阶段。已经通过且不受本次变更影响的outbox 42独立节点不要求重新运行。

本次保存为明确未完成的本地缺陷检查点，不推送远程，不把整项P4-B写成已验收。高保真前端及模型分工提醒门禁保持，尚未进入P4-C。
