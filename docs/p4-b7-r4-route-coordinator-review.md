# P4-B7-R4-ROUTE 总控交接核对

2026-10-02，头脑风暴总控。接受R4为稳定独立验收输入，执行状态保留`review / finished`；不独立关闭PATH-001，不宣布UI-04或P4-B complete。

## 实际只读核对

已读AGENTS、项目入口/协调规则、最新control、自身角色、R4任务与运行说明、C12-R2原失败代码、registry实现和开发测试、外部原始JSON及清单。总控未运行测试、产品、构建、安装或服务。

| 核对 | 本轮实际结果 |
| --- | --- |
| R4 source | 353/353 matched，353唯一路径，0缺失/差异 |
| 仓库delivery | 5/5 matched |
| 脱敏evidence | 59/59 matched，字节数及摘要逐项相符 |
| 新package out | 140/140 matched，字节数及摘要逐项相符 |
| 352起点边界 | 349 unchanged；3变化仅registry.ts、registry.test.ts、executor；0缺失 |
| 原开发断言 | 原26项相关测试段和断言保持，新增26项；总控只读比对 |
| 修复前红灯原JSON | 2 failed，26 filter未选；不计为本轮最终通过 |
| 定向/完整原JSON | 定向54 passed；完整124 passed，14文件；无failed/pending，重复节点不累加 |
| package原记录 | 1次，exit 0，7571ms |
| 静态产物原记录 | 7/7；Python资源67精确匹配，污染/staging 0 |
| 真实EXE原记录 | 1次，19门禁通过，34835ms，recover 1次，自然exit 0 |
| 资源原记录 | owned进程/监听/窗口0；17:29复核为0。总控未重新启动产品 |

源码只新增独立`route_path:${route.path}`查重命名空间，route ID和全局setting保留。同模块/跨模块完全相同path拒绝；无输入归一化、schema改变或跨调用状态。包内main/renderer均包含path、route ID、全局setting三类独立token，asar与R3不同。该绑定是来源证据，行为结论来自测试。

UI-04开发映射已包含hostUiMajor、module/Profile/route ID/path/setting/appearance冲突、严格ASCII/SemVer和Host交集。Shell/main/preload的无具体moduleId分支核对明确限结构证据；它不能替代真实Windows行为、第二模块接入或lazy错误隔离。路径大小写、尾斜杠和模式等未另冻结语义不冒称全通过。

## 稳定输入

- R4 source：`606048c192bf7cb19852407dee924e30d10562ce26abf35de240af3be436a27f`。
- delivery：`462353a1f40d08c1cd45c66bd1396d4427a0dc33ceb9abbe1be224dbd9b41c9d`。
- evidence：`c3b801eb41905f1c930395e2ed09448fa9fbfdea3bedf722ac1958cc3285eb4e`。
- out manifest：`3e00e2a4851181ba7b6351ce9b0e6c1523f320b002f500403ffa654f08a942df`。
- EXE：`d5868736cbdf63f717f0ea853141b980d06cefc10a3c05196e8856cbe3a4de2b`，246032896 bytes。
- asar：`9a4da50b2c5583e6f2337bdff43e399cd454c360fa6169b1667a1e4506c337d4`，759878 bytes。
- lock：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- 外部根：`C:\MarisRouteR4\R4-20261002-164600`，产物`workspace/apps/desktop/out/Maris-win32-x64`。

执行方旧R3不变审计已落盘成功。首次工具文件名笔误、绑定脚本转义错误、中断和更正均保留，没有追加package/EXE。它们不是新的产品缺陷；总控没有重复12677依赖全量或旧profile读取。

## 下一步与状态边界

发布[P4-C12-R3](coordination/prompts/p4-c12-r3-route-windows-tester.md)，先原`R2-UI-04-PATH`不变断言复验，再必要路径边界及UI-04独立缺口，随后接续原24项未执行公开行为和Windows场景。不重复已关闭outbox42、设置键15成功独立节点、完整124开发回归或旧构建。

OUTBOX-001与设置键REGISTRY-001保持独立关闭。PATH-001仍待独立关闭；UI-04/P4-B未验收，矩阵不由总控预写为passed。执行与技术顾问停止，测试新任务`ready / waiting_user`，接单unverified。真实前端提醒门禁保留，P4-C/D不提前开始。

本轮本地Git仅建立明确未验收的checkpoint，不推送GitHub；不编辑执行/测试/技术顾问角色状态。
