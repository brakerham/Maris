# P4-D16 总控接受与公开行为验收路线冻结

2026-10-03，Asia/Shanghai。头脑风暴总控接受 D16 的**有限技术裁定**为 `complete`；顾问本人 `review / finished` 原记录保留。该接受不关闭旧 A 的未知根因，不关闭 LAZY-001、UI-02 或 P4-B，也不增加矩阵 passed。

## 实际交付核对

- [正式裁定](phase-4-d16-harness-and-acceptance-advice.md)及[39 项交付](coordination/diagnostics/p4-d16/delivery.sha256)逐文件 39/39 匹配；清单普通 SHA-256：`e045d8fd1d8f26b9f3d93072dc07132bb0d43e2fc5c07b984bbe38b00d931c75`。
- [E1 源码](coordination/diagnostics/p4-d16/e1/source.sha256)10/10、[E2 源码](coordination/diagnostics/p4-d16/e2/source.sha256)11/11 匹配，基准均为 D16 诊断根。旧 R4-R3 的 52 项交付、15 项源码保持。
- [E1 真实结果](coordination/diagnostics/p4-d16/e1/results/process.json)：CLI 6,982 ms，root exit 0；jsdom/React 分段导入进入正文。[E2 真实结果](coordination/diagnostics/p4-d16/e2/results/process.json)：CLI 1,703 ms，root exit 0；与旧 A 同三项静态依赖的新极小模块进入正文。实际诊断 2 次，产品 main/loader/fixture/旧目标 0，未使用第三次盲试。
- 顾问交付时 596 起点为 595 未变、本人角色日志 1 项授权变化；总控本轮接单再修改自己的日志，实时核对将两项角色变化单列。后续协调更新不倒写为顾问越界。
- 四个登记 root/worker 已核对退出；worker 自己的 exit 回调未取得，不复制父退出码。完整系统后代枚举权限限制仍 `unverified`。空 stdout/stderr 不是成功依据，成功由阶段记录及实际进程退出支持。

旧 A 的实际停点仍只有 setup 后、collect 导入返回前的缺失边界。两次极小实验反证了“这些固定依赖必然无法加载”，没有证明完整 A 已通过，也没有证明单纯加时会解决旧问题。两项残余假设保留为 unknown。

## 冻结决定

1. **公开 B 独立执行，辅助 A 按需归因。** 撤销后续公开节点读取旧 A pass receipt 的进入门禁。保留旧 A 和所有首次结果，不修改旧任务或重跑旧目标。本轮不派 A、D16-R1 或新 bootstrap 诊断。
2. **P 成功证据只读复用。** 不重做默认 loader 三次拒绝验证；新 B 必须取得本次精确映射、真实 ESM 顶层 throw 命中、当前 `#/daily` 和局部安全错误提示，不能用 P 或取消请求替代。
3. **原四条公开断言保持。** 同一观察时点核对安全提示、Shell、模块导航及统一 Agent 面板；任何失败仍失败。冷 worker、真实 main/StrictMode/default loader、真实 Router 和单 React 根保持，不预热、包装 loader、替换 Router 或额外导航。
4. **内部遥测与公开行为分层。** 无包装 B 不声称记录了每次 abort/内部 Router 错误槽；这些内部字段未采集保持未核实，不再作为启动 B 的门禁。故障来源只按本次映射/throw/身份/持续语义/冷入口判定，当前 hash/局部 alert/四断言单列为公开结果；缺少 alert 不能反过来把已完整的来源判为无效。持续故障来源与当前局部 DOM 合起来支撑公开隔离结论；失败原因不足时保存首次结果交总控，不自动启动 A。
5. **新节点分段预算。** 初始化到 `body_enter` 最多 15 秒；正文最多 10 秒，其中 UI 条件观察仍最多 5 秒；自有收口最多 2 秒；整个 CLI 总体硬限 30 秒，全部包含在内。Vitest 函数外层 12 秒包含正文及 finally，业务阶段仍严格 10 秒，不把 2 秒清理算成业务延时。各阶段用自己的计时源留证，不混算不同进程的相对时间，不修改旧 A 的时限或结果。
6. **失败按实际层级分流。** 正文前停止是初始化阻塞；来源不完整是接线未验证；有效持续故障下公开断言失败才形成产品行为失败证据，具体定级需证据支持；清理无法确认单独保留限制。禁止延时、覆盖首次失败或自动追加目标运行。
7. **通过后同任务接原续跑。** 初始 B 通过且资源收口后，测试方接独立恢复/切换/状态保持与原 24 项剩余公开及 Windows 条件。开发自测单列，已完成集合不重复，真实设备条件不由 jsdom 代替。B 一项通过不等于完整 UI-02 或 P4-B 完成。

## 新任务及所有权

发布 [P4-C12-R5-PUBLIC 测试任务](coordination/prompts/p4-c12-r5-public-tester.md)，既有测试智能体唯一负责人，状态 `ready / waiting_user`、接单 `unverified`。新文件使用 `r5-public-*` 与 `evidence/r5-public/**`，旧独立材料只读；受验产品、依赖、包及资源保持原 R5 固定值，不打包、不修改产品。

输入以新的 [固定起点](coordination/snapshots/p4-c12-r5-public-start.sha256)为当前权威，不拿旧协调摘要断言当前工作区。顾问和执行继续停止；用户只需把新任务卡交既有测试智能体，不需要现在点击窗口。

总控本轮只做摘要、证据和合同核对，没有运行目标或产品。此本地提交接受 D16 技术裁定并保存 P4-B 未完成状态，不推送、不作发布。前端设计与模型/token 策略提醒门禁保持。
