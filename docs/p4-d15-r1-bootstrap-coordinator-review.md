# P4-D15-R1：前置取证结果总控验收与独立复验裁定

核对时间：2026-10-03 03:12，Asia/Shanghai。角色：头脑风暴总控。

## 接受范围

接受D15-R1为`complete`，仅指任务要求的前置取证问题已经回答：同一个隔离worker取得真实React Router导出，实际main导入完成，React act另行返回。顾问原交付`review / finished`状态文件保留，由总控在控制面登记接受，不修改其他角色文件。

旧D15-P3超时根因仍未知，原C12-R4/R4-R1未出现错误提示的原因也尚未定位。D15-R1没有执行四条业务断言，不能关闭`LAZY-001`、`UI-02`或P4-B。当前没有新的产品返修依据。下一步交既有测试智能体执行[C12-R4-R2冷入口传播复验与续跑](coordination/prompts/p4-c12-r4-r2-cold-entry-tester.md)，不再另建纯bootstrap顾问诊断，不增加等待或重打包。

## 实际摘要与预算核对

总控及两个只读子任务检查原始文件、源码和Git边界，没有运行诊断目标、测试、产品或服务。

| 核对对象 | 实际结果 |
| --- | --- |
| R1新delivery | 40/40匹配，40唯一路径；诊断目录39文件全部登记或清单自身 |
| R1固定起点 | 464项：463精确匹配，顾问自身日志1项授权变化 |
| 旧D15 delivery | 30/31匹配，同一顾问日志授权变化；不称旧31项整体匹配 |
| 旧探针源码 | 8/8匹配 |
| attempt-0/1源码 | 各6/6匹配；setup和probe正文逐字相同 |
| attempt-0首次材料 | 17/17匹配，未覆盖失败 |
| Git与缓存 | 暂存空；tracked仅顾问日志变化；新报告/专属目录新增，temp不存在 |

关键清单SHA-256：

```text
R1 delivery: f9009674a9dcc799a972102216fe37515f0fedc6a81d5c1b4aeedcc4d147ed51
R1 fixed start: 1a170a063dcee793aa0310809da8fe215dbd1a005a6fbdfd33530f5e67b27225
attempt-0 source: ce285006670f71700415ce969ccd1e8a0ab57cbf8a6ee315573688bce264830e
attempt-1 source: 4b0519d1bd632343da94ffbeb6d776b069c12cf41e519f046c08ca7dd8ad5427
attempt-0 first delivery: 1eeec3c963dd0bf6178802f82a314687a7b24e88ccf7a8878d614698371c5620
```

[第一次journal](coordination/diagnostics/p4-d15-r1/attempt-0/results/worker.journal.jsonl)仅有连续的worker_start和journal_ready。[冻结setup](coordination/diagnostics/p4-d15-r1/attempt-0/setup.mjs)同步写入并fsync，失败立即终止；冻结probe在hoisted/body/main调用之前先记录事件。结合已停止的自有root/worker和[修正门禁](coordination/diagnostics/p4-d15-r1/attempt-0/results/pre-main-correction-gate.json)，可以确认首次没有请求main。该结论不依赖stdout缺失。

首次controller没有保存具体异常类型，保持unknown。之后虚拟文件的共享读取证明支持修改新controller的ReadWrite共享读法，但不能将新证明的IOException/HResult倒填到首次或旧P3。首次材料先冻结，第二次仅改controller读法/安全分类、首次材料门禁及attempt配置路径，符合唯一前置修正授权。

| 实际运行 | main请求 | root退出/耗时 | 结果 |
| --- | --- | --- | --- |
| attempt-0 | 0 | -1，724ms | controller失败后定向结束，首次记录保留 |
| attempt-1 | 1 | 0，6440ms | 无timeout或强杀，22条连续worker记录 |

CLI2次、main1次、修正1次，没有第三次。两个process耗时合计7164ms；controller末记录合计7176ms；内部7166ms属于不同取值时点。离线整理及用户继续前的聊天间隔另列，不能说整个聊天只持续7秒，也不算目标一直在后台运行。

## 同一次worker的实际阶段

[第二次journal](coordination/diagnostics/p4-d15-r1/attempt-1/results/worker.journal.jsonl)的PID/parent、seq连续且与[controller/process](coordination/diagnostics/p4-d15-r1/attempt-1/results/process.json)一致：

| 阶段 | 证据 |
| --- | --- |
| actual Router导出 | seq8 enter→seq9 resolved，108.825ms，createHashRouter是function |
| main导入 | seq12 enter→seq13 resolved，482.774ms；seq14实际desktopRoot确认 |
| React act | seq11 enter→seq17 return，548.285ms；其间Router建立、原factory命中一次 |
| 收口 | seq18–22真实root卸载、观察退订、DOM/global恢复、bridge2进2出/active0/settings0 |

父CLI自然退出0，root与登记worker的结束证据存在；worker自身exit事件缺失，其具体exit code/退出机制仍未知。不能将父退出码复制给worker，也不能把四个已知PID的检查写成全系统或完整所有后代零残留。

## 为什么不能直接关闭业务缺陷

[R1 probe](coordination/diagnostics/p4-d15-r1/attempt-1/bootstrap.test.tsx:76)在main之前显式await Router，预热了观察mock与真实包。它还去掉旧P3的loader/Router状态/DOM采样。因此证明的是新观察配置中的前置链完成，不是原冷入口的错误UI出现，也没有解释旧超时。

原四要求继续保留：安全错误提示、Shell存在、模块导航存在、统一Agent入口存在。factory命中、act返回、root清空都不能替代这些业务断言。

## 下一任务的明确观察合同

测试方直接启动实际main，启动前不导入Router、module-routes、实际页面或其他可能预热它们的产品入口。setup只建立原生日志。新测试专属同步ESM观察门面在main的正常依赖链首次请求Router时才加载；通过不回指门面的独立alias重导出同一真实包，仅同步透传createHashRouter，返回原Router。禁止async Router mock/importOriginal、人工navigate/revalidate或改变初始路径。

只记录目标loader原Promise终态、同实例Router状态与DOM安全布尔，保留原四断言及5秒上限。门面是测试观察工具，静态可行，尚未动态验证；不能预写为已修复旧超时。精确alias、单实例、原返回对象及所有观察扰动要有验证记录。

观察节点通过后，再在独立新worker以直接真实Router alias启动同一冷main、保留四断言，不安装观察门面，确认业务结果不依赖观察工具。两节点均通过，才继续同任务独立恢复和原未执行Windows。任何目标已运行的失败不修后重跑；首次记录和各自条件分别保留。若失败，必须带上当前可得传播阶段交总控，不再只交“无提示”并建议延时。

下一任务的source/依赖/受验包不变。执行和顾问停止，测试任务发布仅为ready、接单unverified；LAZY-001/UI-02/P4-B仍未关闭，P4-C/D未开始。前端参考图与模型分工提醒门禁保持；本次只建立本地检查点，不推送远端。

来源：[R1正式报告](phase-4-d15-r1-bootstrap-advice.md)、[R1交付摘要](coordination/diagnostics/p4-d15-r1/delivery.sha256)、[旧R4-R1观察节点](../tests/independent/desktop/r4-r1-observed.test.tsx)、[实际模块路由](../apps/desktop/src/renderer/module-routes.tsx)。
