# C12-R4-R1 故障命中但无错误UI：总控核对

2026-10-03，头脑风暴总控。接收blocked/finished；原LAZY-001仍未关闭，未据此新增已定级产品缺陷，UI-02/P4-B未通过。

## 原始事实及复算

新节点一次0 passed/1 failed，mock factory命中1次、hash为#/daily、观察5016ms无alert。Shell/nav/Agent采样存在。生产StrictMode的两次bridge调用及最终订阅归零均记录；真实root卸载、DOM/global恢复。首次日志/回执保持，不重跑。

总控实际核对：410输入406未变、4授权变化、0缺失；15项新增摘要匹配，两份旧追加文档prefix匹配；95项旧独立文件与Git起点规范化内容一致；120矩阵ID/原预期/原状态不变；R5 EXE/asar普通摘要匹配。产品与辅助Electron均0次。

## 已能排除与尚不能判断

本轮已经进入故障factory，不能再称“故障完全没命中”。5秒观察仍无alert，不能继续把旧200ms等待当确定根因。factory抛出只证明该点发生错误，不证明dynamic import Promise已向实际页面loader发布拒绝、Router已接受错误状态或React已提交该状态。

静态代码main→DesktopApp→真实createHashRouter→内置动态import→loader catch→子route errorElement→Shell Outlet接线存在，RouteErrorBoundary确实含role=alert。安装的Vitest mocker会包装factory异常，RouterProvider会在状态更新中使用React transition；这些仅是调查位置，不是已确认根因。当前首次回执没记录这些层之间的终态。

总控只做源码/证据核对，没有新增测试、修改产品或把开发八项通过当独立关闭。不要再派一份只改等待时间的测试任务，也不在根因未分流时让执行方打包。

## 裁定

发布[P4-D15有限异常传播诊断](coordination/prompts/p4-d15-lazy-propagation-technical-adviser.md)：既有技术顾问先静态追踪，再按需要最多3个虚拟jsdom/Node探针，分别观察直接import、实际loader、实际生产入口中的Router状态与DOM。

探针只观察/转发原操作，不代替产品Router/loader，不改产品、依赖、旧独立测试，不启动Electron/EXE或打包。技术顾问交根因证据、反证和最小后续范围；不能代替独立验收关闭缺陷，也不能创建后续任务/接口冻结。

技术顾问ready/waiting_user，接单unverified；测试与执行finished停止。新起点覆盖本轮交付/协调更新，旧410清单不改。P4-C前端设计/模型策略提醒保持。保存明确未验收的本地检查点，不推送。
