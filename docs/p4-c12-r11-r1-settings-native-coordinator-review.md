# R11-R1 设置恢复接受与原生定位续接裁定

2026-11-03，Asia/Shanghai，头脑风暴总控。依据[独立报告](testing/phase-4-c12-r11-r1-windows-report.md)、[首次停止回执](../tests/independent/desktop/evidence/r11-r1-windows/stop-receipt.json)和冻结源码作只读核对。总控未运行测试、EXE、helper、系统查询或安装打包。

## 有限接受

**限定关闭 `P4-C12-R9-R3-SETTINGS-001`。** 已接受的 R11 源级水合证据与本次实际 W2 首次有效页面样本闭合：theme=dark、privacy=on、themeControl=dark、privacyControl=true，原四条 ID/预期保持。首次样本前设置写入数0，磁盘设置摘要不变；真实daily/Shell/导航/Agent和可见性已观察，没有用接口回包替代页面。

W2/W3 18条比较通过，第二实例自然exit0，原主实例及Host身份保持；随后普通关闭主窗，自然exit0、资源0。H2 13条原生比较通过，实际读回稳定owner、原draft/event/body摘要；全部基线通过后才加入四条虚拟数据，共五条。接受这些子条件，不再次运行W2/W3/H2。

R11-R1整体仍blocked/finished。完整CMP-06仍缺透明降级、对比、焦点、动效和设备条件；原UI-02/LAZY-001失败保留，P4-B未接受。矩阵只有CMP-06从failed改blocked，当前B为 **1 passed、1 failed、20 blocked、2 not_run**。120个ID、12列、原预期及A/C/D保持。

## 复算范围

| 对象 | 总控实际结果 |
| --- | --- |
| 原1550项起点 | 1546原字节保持，四份测试共享文档获准变化，0缺失 |
| 交付/工具/证据 | 129/17/106项逐项匹配 |
| 首次材料/源码归档 | 103/30项逐项匹配 |
| R9固定构建/包/Python资源 | 1432/140/67项逐项匹配 |
| R1停止后虚拟现场 | 68项路径/大小/摘要匹配，未解密或更改 |

交付清单SHA-256为 `f147d734de1b138a45a069013a8d0a10800ba7b5d092e305d96ca1eca2b86a21`；首次材料为 `fc799fa951caa23b24b9fd4333395c410e0720b4fe38dfc9a98b7606672f349e`。停止后68项库存为 `ea0462dbb09e264840a1e5daa73bda4cd7843264ecd92a42c1abcd03191aba12`，基准根是 `C:/MarisC12/C12-R11-R1-WINDOWS-20261103-002800`，包含continuity.json和profile-main，不能再拼一层profile-main。总控首次路径读取误用后者，纠正基准根后全匹配；未修改现场。

已跟踪文件diff检查退出0。冻结源码归档 `first-source/tests/independent/desktop/r9-r3-storage.cjs` 第23行保留一处原行尾空白；它属于首次材料，不为消除格式提示改写。完整暂存检查中的这项提示不应宣称为零。

## 定位缺口与不能推断的结论

`r11-r1-windows-os.ps1` 的 Main() 仅按root PID与标题Maris枚举顶层窗口，close要求结果唯一。产品main/index.ts主窗标题Maris，outbox-retention.ts的原生老化提示同样明确title=Maris。实际W4-OS-1、OS-2和OS-5三次成功库存均记录visibleMainCount=2，证实这一现场的同标题唯一假设不成立。

按钮查询也对所有同PID、Name=Maris的UIA顶层候选扫描后代，缺少主窗与模态窗的owner/窗口层级绑定、候选去重和失败时数量记录。首错为owned_dialog_button_ambiguous，后续普通收口为owned_main_ambiguous。**首错究竟是零按钮还是多个按钮仍unknown**；不能用邻近快照补造出错调用的精确数量，也不能证明用户保留操作失败。

本轮未Invoke按钮、未成功PostMessage普通关闭，最终核实身份后强制退出1、资源0。强制收口不算产品正常退出，也不证明草稿删除/保留。H2之后outbox密文变化可以来自重新加密，语义状态未由H3确认，不能按密文推断丢失。

内部只读助手指出相同标题冲突及缺候选观测，父已亲自复核相关源码与三条实际记录；该辅助不作为独立测试或完整新卡审阅。

## 下一任务与明确新增额度

发布[P4-C12-R11-R2-NATIVE](coordination/prompts/p4-c12-r11-r2-native-tester.md)，由既有Tester负责，[新起点](coordination/snapshots/p4-c12-r11-r2-native-start.sha256)首次匹配后接单。Executor/顾问停止，实际接单unverified。

1. 新工具副本按真实窗口所有权/层级区分主窗和模态，保存安全候选元数据；不取第一个同名项，不放宽进程归属，不新建通用框架。
2. 从停止后68项现场普通复制新副本，先一次只读H0，比对H2 after五条语义和owner基线。不得reset、重seed、换原W1或执行方profile掩盖变化。H0是失败后续验前置，不是H2重跑。
3. H0通过才唯一W4-R→H3→W5→H4，然后按新卡能力分支在同任务继续W6/W7。已接受41/321/109、H1/W1/W2/W3/H2和其他旧通过仅引用。
4. 历史实际累计产品5、helper4保持。恢复额外需要W4一次、H0一次，**总控明确将本系列上限由8/6调整为9/7**：本卡最多产品4（W4-R/W5/W6/W7）、helper3（H0/H3/H4）。不追溯重置旧失败、不允许第二次W4或额外诊断启动。无安装/package/开发服务器/辅助UI夹具。

这不是新的产品返修依据。只有真实公开比较失败才提交相应产品发现；工具/所有权未知仍准确归类。新卡冻结原生定位、现场基线、停止和收口要求，不为每个成功步骤再派发。仅保存本地检查点，不推送。真实P4-C前端启动前的参考图与模型分工提醒保持。
