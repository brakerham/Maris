# P4-B7-R6-MODULE-READY 总控交付核对

2026-10-13，Asia/Shanghai。执行方R6保持`review / finished`，接受为新独立验收输入；不据自测关闭LAZY-001、完整UI-02或P4-B。旧R7 W1现场原因仍`unverified`。

## 交付与实际变化

[R6运行说明](b7-r6-module-ready-running.md)和[814项source](../apps/desktop/b7-r6-module-ready-source.sha256)已读取。仓库精确5文件：module-routes和executor日志2修改，新执行方测试、运行说明、source清单3新增；产品改动仅renderer模块同步/路由生命周期，无main/IPC/依赖/原独立材料修改。

交付清单`C:/MarisModulesR6/R6-20261013-002100/evidence/inputs/delivery-five.sha256`逐项5/5匹配，SHA-256为`20817a1b756c194cf0b180536eddb75e8db3a1d262ca0d5af74d1785778356e5`。source清单本身SHA为`74c6df4829b2f9ce8b0de2b84b748f14cc3dec520ceab234b91113d3a269a68e`。

814项在总控接单后仅本人brainstorm授权变化，该文件HEAD原字节精确匹配交付摘要；随后总控自己的5个协调文档变化另列。812起点的执行方终点为810未变、2授权变化。旧R7的68项交付逐项精确不变。无关`.claude/`和`.pnpm-store/`不纳入本次交付或Git检查点。

## 证据结论与限制

| 证据 | 执行方实际结果 | 总控接受边界 |
| --- | --- | --- |
| 首次可控顺序 | red/red2各2失败；初读为空、两次同值就绪通知后仍无页面；补充移除当前模块1失败保留 | 可复现启动同步缺口，不倒写旧W1现场原因 |
| 最终开发验证 | 定向28、完整16文件150通过；新增18；TypeScript/lint通过 | 执行方层级，不重复累计唯一节点 |
| 新package | 1次exit0，静态7/7，67资源、140产物 | 固定新包可供测试，不是独立设备验收 |
| 新EXE | 1次22/22；首次daily真实可见，recover后设置hash/dark/privacy保持，切回daily仍可见 | 已分开后台与DOM取样，仍为执行方冒烟 |
| 退出 | exit0、自然结束，未超时/未强制收口，登记进程/监听/窗口归零 | 不替代真实Tray、注销或全系统历史后代审计 |

源码改变订阅/初次读取顺序，用有限合并及代次保护读取模块；有效交集相同则保持Router，真正变化才重建，并在移除当前模块后留下Shell内空页。新实例与Provider生命周期涉及原lazy恢复周边，下一任务需独立验证同集合不自动重试、状态保持与已移除页面不被旧结果恢复；不重跑完整历史集合。

新包EXE SHA-256：`4ef5bce604fc61fc2b815300edee8a29ab593083d308e849445c6c97235c5f1e`；asar：`5eb153002f4c48ce704f1d0f90b3bf441d5edf3799ea5fe4428f706aee7c69db`。输入、产物和环境清单绑定见下一任务，不修改受验包或为验收另打包。

总控本轮实际只读复算新根813构建源码、140产物、67资源、73dist及12443项冻结依赖均匹配；最终full JSON有16个唯一测试文件/150通过，定向28通过，原red/red2各2失败及directed2的27通过/1失败原样保留。静态7个布尔门禁与EXE22个门禁均为true，页面四阶段取样与退出/收口记录相符。没有重跑测试或产品。

关键外部回执冻结摘要如下（基准新根`evidence`）：

| 回执 | SHA-256 |
| --- | --- |
| `inputs/closeout.json` | `f403ca096b67ca03992ff5bacf5f5aaafb24f7f2507de06bad4c5cd43d0e895f` |
| `static/result-v4.json` | `a015054df0235caa0e912e194619d4abe8077b799f5ef9c9ec839c6e9ebce2ab` |
| `final-exe/result.json` | `4a419e37acac0a71a9fb1cc5e0f98b3b8463bb6f69879bdacbe080253ef410b3` |
| `static/module-ready-source-binding.json` | `d3ef5d1d06fe9fd3b7b7491454fb7f510331da3b3d008c76bec28683380f8baf` |

两项只读辅助审查始终pending_init，未取得执行或结论，已停止，不计为完成复核。本页核对由总控主代理实际完成；这项工具调度限制不影响已经取得的逐文件与原始结果核查。

## 后续裁定

发布[P4-C12-R8-MODULES](coordination/prompts/p4-c12-r8-modules-windows-tester.md)，既有测试智能体唯一负责人。先独立模块同步与最小邻接保护，再必要开发兼容28项，随后同任务继续新包Windows剩余条件。旧B、完整R7五组和旧EXE不重复。

实际工具不支持的chunk或缺设备条件只保留对应未验证范围，可继续无依赖的已计划场景；真实业务失败及P0/P1、安全/所有权/资源问题仍按门禁停止，不能以“基础设施”标签掩盖。每次页面采样独立保留exists/count/visible/路由枚举和安全错误阶段，不用一个合并unknown代替所有观察。

新任务818项[固定起点](coordination/snapshots/p4-c12-r8-modules-start.sha256)包含当前受控输入，不含自身。只保存名称明确的本地待独立验收检查点，不推送。执行方和顾问停止，新测试任务`ready / waiting_user`，实际接单`unverified`。本次总控仅核对已有证据与任务范围，不运行产品、测试、打包或服务；真实前端前的参考图与模型策略提醒保持。
