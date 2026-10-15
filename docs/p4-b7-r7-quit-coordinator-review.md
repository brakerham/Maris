# P4-B7-R7-QUIT 总控核对与独立复验裁定

2026-10-16，头脑风暴总控。R7执行方交付保持 **review / finished**；接受其固定源码和新包作为独立复验输入，不将开发自测或执行方EXE结果认定为独立关闭。发布 [P4-C12-R9-QUIT](coordination/prompts/p4-c12-r9-quit-windows-tester.md)，由既有测试智能体负责；执行方和技术顾问停止。

## 已实际核对的输入与结果

- 编辑协调文档前，仓库933项source逐项匹配，清单自身SHA-256为 `3dc1f54d632de331515404174bce8686f03114da4695e5a8bb8d5a8c89af0f46`。5项交付全部匹配，清单摘要 `5ff2d0d30048ae4b131e9cbee87993755fb45acfba9b3d6dd5fe59fd582fa5a8`。
- 外部157项证据逐项匹配，清单摘要 `63a94a2177dbe0107f1c9ea327d9d26b694137a91824d2733ad038aaf9d99615`。10月16日恢复工作后再次复算5项交付及157项证据，仍匹配；中断不计持续运行。
- 亲自只读复算新外部副本932项构建输入、140项产物、67项Python资源、73项Electron dist及12677项完整依赖库存，全部匹配。旧R6与旧R8-R1外部不变性采用已核对摘要的执行方final-immutable-audit记录，不冒称本轮重新遍历了全部旧环境。
- 精确仓库交付仅main/index.ts、新main-quit.test.ts、R7运行说明、R7 source清单、执行方日志。原931项中929项保持、2项授权变化；总控随后修改的协调文档另行列举，不回写执行方清单。

| 证据 | 核对结果 | 结论层级 |
| --- | --- | --- |
| 原实现red.json | 1 failed；实际close收到，shutdown=0、毛毛和Tray仍存活 | 原实现开发复现，首次保留 |
| directed.json | 5文件48 passed，0 failed/skip，其中19新增 | 执行方定向回归 |
| full.json | 17文件169 passed，0 failed/skip | 一次完整开发回归；不重复累计48 |
| 类型/lint、package、静态 | 类型/lint退出0；一次package退出0；静态7/7 | 执行方交付可测性 |
| 最终EXE | 一次启动，25/25门禁；正常关闭后约501ms自然exit0 | 执行方真实Windows证据，尚待独立复验 |

## 修复与普通关闭来源

[main/index.ts](../apps/desktop/electron/main/index.ts)的主窗口close在shutdown完成前阻止默认销毁；显式quit进入requestQuit，before-quit的shutdownStarted守卫避免最后窗口销毁同步引起的退出重入。设置/outbox flush及owned停止继续走原composition；没有修改renderer、依赖、接口、旧测试或生产停止预算。

新开发测试执行实际main与composition，Electron边界替身维护活窗口集合并触发before-quit/window-all-closed；覆盖退出等待、重复请求、首次提示与ask取消、迟到提示和老化窗口退出保护。内部只读子任务曾核对守卫及501ms来源一致；未取得最终回复，不作为完成的独立审查。总控未执行测试或产品。

受验根：`C:/MarisQuitR7/R7-20261014-191500`。真实result及冻结driver证明：quit、closeHintShown=false、毛毛可见、继承EXIT_MS已删除；向核实身份的唯一主窗口投递一次WM_CLOSE。投递时间 `2026-10-15T03:31:33.8178995Z`，root退出时间 `03:31:34.318Z`，自然exit0、signal=null，无timeout或forced cleanup。最终登记的产品/后端/窗口/监听为0，子进程退出码仍unknown。PostMessage成功只证明投递，不冒称直接记录了真实main内部handler调用。

新EXE SHA-256：`183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65`；app.asar：`16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3`。后台认证/canonical模块与真实页面证据分开，恢复后主题/隐私及日常页可见。设置和草稿文件关闭前后存在；密文hash变化不能证明内容相同，也不能替代重启持久化验证。

## 保留限制与下一步

- 原GPU overlay ERROR、启动前工具错误、审批/额度中断与子码unknown均保留，不扩大为根因结论，不重跑EXE。
- 关闭QUIT-001需要独立新包正常退出证据；CMP-03还包括hide/ask/cancel/Tray，SUP-05还包括未授权的系统场景，不能因单一路径通过而整项签收。
- UI-01已接受passed；已通过模块13节点、旧冷入口B、R7恢复五组和原注册/outbox集合不重跑。LAZY-001、UI-02及P4-B未关闭；矩阵保持1 passed、3 failed、17 blocked、3 not_run，等待测试方按本轮实际结果更新。
- R9先做必要独立退出边界及48项相邻开发兼容，再在新固定包复验原正常退出断言，通过后同任务继续尚缺的重启/同ID/关闭策略/原生提示等Windows条件。真实chunk注入或人工设备条件不具备只阻塞对应条件，不反复开启观察任务。
- 新任务最多8次有计划产品启动、4次辅助；包含1次修复包必要复验和原计划剩余条件，不重跑已通过独立集合，不以预算上限为目标。未知/业务失败不重跑；纯工具错误的有限更正规则写入任务卡，首轮证据不可覆盖。

总控同步README、project-coordination、control、overview及本人状态，生成 [新固定起点](coordination/snapshots/p4-c12-r9-quit-start.sha256)。本地Git仅保存待独立验收的修复检查点，不推送、不宣称P4-B完成。真实前端参考图及模型分工提醒门禁继续保持。

R9任务卡发布前由总控内部只读子任务r9_card_check复核：原失败断言、固定清单摘要、5文件48兼容、8/4上限、旧集合复用及有限工具修正规则一致，无阻断；未运行独立目标。
