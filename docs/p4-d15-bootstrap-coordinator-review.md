# P4-D15：首次诊断交付总控核对与前置取证裁定

核对时间：2026-10-03 01:05，Asia/Shanghai。角色：头脑风暴总控。

## 结论与当前状态

接受D15材料为可复算的技术诊断输入，保持其`blocked / finished`；不宣布根因定位完成。P1、P2分别证明各自隔离实例的导入拒绝与默认loader安全错误映射。P3没有持久阶段回执，不能证明观察包装、测试正文、main、Router或DOM到达了哪一步。

当前只授权技术顾问执行[P4-D15-R1前置阶段观察](coordination/prompts/p4-d15-r1-bootstrap-technical-adviser.md)。保留原D15与全部独立首次失败，不要求产品返修，不再增加等待时限或重打包。`LAZY-001`、`UI-02`和P4-B均未关闭。P4-C/D仍未开始，既定参考图及前端模型分工提醒门禁保持。

## 实际核对

总控及两个只读子任务检查文件、代码和原始结果，没有运行测试、诊断目标、产品、构建或服务，没有编辑其他角色日志。

| 对象 | 实际结果 |
| --- | --- |
| D15固定起点 | 429/429匹配，0缺失、0差异；技术顾问日志不在清单内 |
| 新交付清单 | 31/31匹配、31唯一路径；诊断目录30文件全部登记，含清单自身 |
| 冻结探针源码 | 8/8匹配；没有修改后重跑 |
| P1 | factory一次，直接import reject，Vitest包装及虚拟cause匹配；CLI 4069ms、exit 0 |
| P2 | 真实默认内置loader约1ms reject，安全`desktop_module_unavailable`匹配；CLI 3443ms、exit 0 |
| P3 | stdout仅26字节RUN横幅，stderr空；15051ms硬限，root实际exit -1；无p3.json，worker与finally状态未知 |
| 会话 | 22663ms，三目标各一次、零重试，completed=false |
| Git与缓存 | 暂存空；原tracked变化仅顾问日志；D15新文档/诊断目录新增，temp不存在 |

清单SHA-256：

```text
docs/coordination/snapshots/p4-d15-start.sha256
583d21945b0d1e307374f34f4cca04f88fb4d862cad32c2e09844f017b7e43af

docs/coordination/diagnostics/p4-d15/delivery.sha256
1d80751b735a27d89ff942f7df864f0c049eb4007e1c1afa2c22ea5d32f45d87

docs/coordination/diagnostics/p4-d15/probe-source.sha256
583897cd18ecc891000f036fddaa802e551f62c8c76c081ca109c66ae7e8a3fd
```

以上是技术诊断结果与证据核对，不计入独立验收通过数量。P1/P2不能补签旧main实例或P3实例的传播终态。

## 已确认的取证缺口

1. [P3的record初始化](coordination/diagnostics/p4-d15/p3.test.tsx:68)只追加内存timeline，[finally中的save](coordination/diagnostics/p4-d15/p3.test.tsx:157)才写文件。硬限终止会丢失已经发生的前置阶段，不能将“无回执”解释为“未创建worker”或“没有进入main”。
2. [Router观察mock](coordination/diagnostics/p4-d15/p3.test.tsx:18)没有工厂进入、`importOriginal`开始或返回的持久事件。mock注册提升不代表工厂已经执行，也不能从静态源码判断它必然在body之前或之后运行。
3. [main导入和act](coordination/diagnostics/p4-d15/p3.test.tsx:115)共用一个await。必须区分导入Promise终态与React act返回，才能判别最后等待点。
4. [controller](coordination/diagnostics/p4-d15/run-once.ps1:69)从最终receipt取得worker PID；P3缺失receipt，因此worker的身份与正常finally未知。下次在worker setup阶段就持久保存PID/parentPID和阶段记录。

上述缺口属于诊断观察与证据保存。新增Router包装是优先调查位置，但尚不能宣布`importOriginal`死锁、React/Router故障或产品吞掉异常。原loader/Shell代码保持不动。

## 资源结论的限制

[P3进程记录](coordination/diagnostics/p4-d15/results/p3.process.json)只确认已知root在硬限后退出。[资源观察](coordination/diagnostics/p4-d15/resource-observation.json)正确丢弃CIM权限失败后的空集合，替代读取支持可见固定Node与已登记进程退出；不能据此认定P3正常root卸载、订阅归零或完整进程树验收通过。报告准确保留了这些限制，不要求补写不存在的成功回执。

## 新任务的唯一范围

在新的专属目录即时记录worker setup、mock注册/工厂、真实Router导出、body、main import及act的进入和终态。每个关键await之前先保存enter，返回后立即保存terminal；超时后能指出最后持久阶段及其未完成的下一阶段即可。

不继续独立恢复测试或Windows门禁，不重复P1/P2。新目标最多一次实际main启动。允许一次明确发生在`main_import_enter`之前的观察工具修正，首次材料保留；若main已经开始、阶段缺失无法证明是否开始、所有权未知或无法收口，立即停止，不能借修正预算再次启动main。继续沿用15秒进程、10秒测试时限，不用加时掩盖取证问题。

本轮形成新固定起点与台账后，由用户把新任务发给既有技术顾问。总控不把Prompt发布称为任务已经接单，不代替顾问运行探针，不把观察诊断称为独立关闭。仅保存未验收的本地检查点，不推送远端。

来源：[D15建议](phase-4-d15-lazy-propagation-advice.md)、[计划与首次源码](coordination/diagnostics/p4-d15/probe-plan.md)、[P1结果](coordination/diagnostics/p4-d15/results/p1.json)、[P2结果](coordination/diagnostics/p4-d15/results/p2.json)、[会话记录](coordination/diagnostics/p4-d15/results/session.json)。
