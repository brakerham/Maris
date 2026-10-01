# R2-OUTBOX 总控核对与 C12-R1 输入

- 角色：头脑风暴总控。
- 审阅时间：2026-10-01 23:25，Asia/Shanghai。
- 裁定：接受 R2-OUTBOX 实现、自测、新 package/EXE 为独立复验输入；执行方保持 `review / finished`。`P4-C12-OUTBOX-001` 仍待独立关闭，整体 P4-B 尚未 complete。
- 下一任务：[P4-C12-R1](coordination/prompts/p4-c12-r1-outbox-windows-tester.md)。执行智能体与技术顾问停止。

## 本轮实际复算

总控只读核对产品差异、自测内容、原始结果和清单，没有重复测试、安装、打包或启动产品。

| 对象 | 本轮实际结果 |
| --- | --- |
| 执行方 293 项 source | 293/293 匹配 |
| 八项仓库交付 | 8/8 匹配 |
| 外部 evidence | 38/38 匹配（字节数与摘要） |
| 290 项起点边界 | 286 unchanged、4 authorized changed、0 missing |
| 当前真实新 package out | 140/140 匹配 |
| 原始完整 Vitest JSON | 90 passed、0 failed、0 pending |
| 原始新 EXE JSON | 19 gates 全 true、recover 1 次、exit 0、自然退出、零进程/监听/窗口残留 |

四项起点变化仅为 outbox、main、supervisor-outbox 执行方测试和 executor 状态。四项新增仅为 retention 控制器、专属测试、运行说明和 source 清单；独立测试/首次失败 evidence 未变化。

| 清单 | SHA-256 |
| --- | --- |
| R2 source | `a485add6b497e0aae0641e1397317b273949b2bb89262a9e0faf9680a8b5210d` |
| 八项 delivery | `cd4ceee810112985729d2ba4e63e04597494c86af3c77979d1e86e9f7ea63a1e` |
| 38 项 evidence | `13a722ca4edabb49cf8f3f1a4c391d87285a9bbca11378d711379faf61985217` |

## 产品行为核对

cleanup 现在只按严格超过 24 小时清理 terminal，所有非 terminal 保留。prepare/state/cleanup/load/确认删除共享串行队列，保存成功后才替换内存，失败不会使后续队列永久拒绝。

候选限定 >30 天的 draft/queued。确认使用不可变对象身份，state 更新与 reload 都替换身份；同一时钟下的更新也能令旧确认失效。新增、sending、已变更和仍新鲜条目不在旧删除范围。

原生提示在 ready-to-show 后异步安排，每个控制器只 attach 一次，默认/取消为保留；关闭、dialog rejection、退出或窗口销毁均不提交删除。main 不等待 dialog 才启动 Host，shutdown/before-quit 显式停止 retention。

执行方注入测试覆盖确认、并发、保存失败和 main 真实导入/生命周期，共定向 27 passed；完整桌面单元回归 90 passed、类型/lint 通过。总控接受这些开发证据，不把它们称为独立验收。

## 新受验版本

根：`C:\MarisOutboxR2\R2-20261001-155509\workspace\apps\desktop\out\Maris-win32-x64`。

| 文件 | 字节数 | SHA-256 |
| --- | --- | --- |
| Maris.exe | 246032896 | `8eb56f3f63b923471a9239e2a01f29a8111067a6093d8c9d118e62e1ccfb5c2a` |
| resources/app.asar | 759820 | `74225ea63dbc7201dc7f7f3299a099ac573f51680ef705536e560a9d9df6b6c7` |

新 package 1/1、10.763 秒、exit 0；静态 7 gates 通过，Python resources 67 项，production fuses 不变，污染/staging 为零。新 EXE 1/1 的权威运行时间为 23:04:40.518–23:05:15.411（+08:00），34.893 秒；Host、daily_finance/canonical Profile、毛毛、安全和自然退出通过。

外部证据位于 `C:\MarisOutboxR2\R2-20261001-155509\evidence`。旧 LOCALZIP 的代码、依赖、产物与原始 evidence 保留；新 C12-R1 必须使用本次新版本，不能回到旧 EXE。

## 保留的限制

- 真实 Windows 过期草稿提示仍未独立设备验证；普通双窗口观察不证明该提示或删除动作。
- Tray 零残留是退出后进程树推断，真实菜单和人工多屏/注销/启动项等仍属原 C12 未完成项。
- 初次 repo Vitest 配置解析失败时 0 用例运行；普通副本后已通过。一次 stdout 会话关闭不等于重复 package。原记录保留。
- 运行说明已勘误计划检查点与真实 EXE 时间差，采用原始 JSON，不推断中间未监测活动。
- 当前 unsigned/Forge alpha/外部 Python 仍是发布前限制；不据此宣布正式发行。

## 独立复验和提交口径

绑定 [C12-R1 新固定起点](coordination/snapshots/p4-c12-r1-start.sha256)，先运行原 C12-PUB-11 不变断言，再补确认/并发/失败恢复边界，随后继续原 24 项剩余验收。首次 C12 log/JSON 永久保留，新输出使用独立 R1 目录，不覆盖失败。

本轮仅创建本地检查点，不推送、不宣布 P1 独立关闭。高保真前端参考图和模型分工提醒门禁继续有效，P4-C/D 不提前启动。
