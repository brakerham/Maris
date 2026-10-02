# C12-R2总控核对：关闭setting缺陷，接受path冲突并冻结R4

- 日期：2026-10-02，Asia/Shanghai；角色：头脑风暴总控。
- 输入：[C12-R2报告](testing/phase-4-c12-r2-registry-windows-report.md)、分组首次JSON/log、[R2起点](coordination/snapshots/p4-c12-r2-start.sha256)、原UI-04/IF-003、registry实现及renderer路由消费。
- 只读证据与定向代码核对，没有重跑测试、启动产品或修改实现。

## 裁定

**关闭`P4-C12-R1-REGISTRY-001`设置键P1**。原R1-SHELL-13断言未变、一次通过；原相邻6及新增8节点通过，证明跨模块全局查重、同/异schema、顺序、合法键、输入不变和失败恢复。原OUTBOX-001关闭状态保持，不重复42独立节点。

**确认新`P4-C12-R2-REGISTRY-PATH-001`为待修P1**。原矩阵UI-04第八列明确有`route/path/setting/profile/companion 冲突`，预期整体稳定拒绝；并非测试方临时增加要求。两个routeId不同、path完全相同的合法虚拟贡献被接受为2个。registry只加入routeId seen token，未加入path；renderer直接使用route.path创建路由，首次失败与代码一致。

当前证据只证明编译期路由唯一性合同失败，不证明真实账目损失、权限利用、真实模块导航错乱或Windows崩溃。测试方按P1停止正确，产品0/8、辅助0/4，不能算Windows已验收。

前轮R3范围限定setting、不允许顺带改path；总控没有要求完整UI-04开发对照。这使同一注册项的遗漏分两轮暴露。R4在路径最小修复后，必须先列UI-04已定义条件→代码/开发节点→结果的完整映射，再打包；不得仅新路径红绿通过就进入包门禁。此举不保证后续不再发现其他缺陷，也不替代独立验收。

## 实际核对

| 项目 | 结果 |
| --- | --- |
| 新文件delivery-verification摘要 | 22/22匹配；verification自身另纳入新起点 |
| 原327起点 | 323 unchanged，4授权文档变化，0非授权/缺失 |
| 旧报告与人工清单 | 原始字节前缀精确保留，只追加 |
| 独立JSON | 原setting1、相邻6、新边界8 passed；path1 failed，16唯一 |
| 开发兼容 | 26 passed，单独统计 |
| 原矩阵 | 120唯一ID/12字段；A64 passed、B1failed/19blocked/4not_run、C20/D12 not_run |
| R3 EXE/asar/lock | 现存文件复算精确匹配输入；无产品启动 |

四项旧起点变化仅tester、原C12主报告、人工清单和矩阵；总控不改测试方材料或其他角色日志。原C12/R1/R2首次失败和通过记录继续只读。

## 修复边界与后续

发布[R4-ROUTE任务](coordination/prompts/p4-b7-r4-route-executor.md)。产品仅registry.ts、开发测试仅registry.test.ts：同次编译中route ID及完全相同path字符串均全局唯一，同模块/跨模块冲突都整体抛既有desktop_registry_conflict。不同路径合法，不重命名/自动覆盖/首个优先，不变更schema或返回合同。

这次确定范围是已复现的完全相同path冲突。大小写、尾斜杠、动态参数或模式重叠的语义未另冻结；如发现实际相关风险先带具体证据交回总控，不自创归一化算法或假设所有路由歧义已关闭。

开发方须在打包前核对UI-04的全部已定义身份/路径/设置/版本拒绝条件和Shell无具体moduleId业务分支要求，说明行为证据与只读证据的区别。超出两个允许实现路径的缺口在打包前报告；不掩盖、不擅自扩大业务实现。

使用R3已验证普通依赖/本地官方ZIP，在新隔离副本完成有限开发验证、新package及新EXE各一次；旧树/证据只读。新asar绑定新源，后续独立复验路径和必要注册回归后再继续未执行Windows。

P4-B仍未complete，真实老化原生提示/Tray/注销/启动项/多屏等未覆盖条件保持。执行R4 ready待用户派发，测试/技术顾问停止。保存明确未验收的本地检查点，不推送远程，不进入P4-C，前端/模型提醒门禁保持。
