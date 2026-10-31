# R8-R2：执行方设置续启通过与 R10 独立复验裁定

头脑风暴总控，2026-10-31，Asia/Shanghai。审阅对象为 [R2 运行说明](b7-r8-r2-finalizer-running.md)、[原 R2 任务](coordination/prompts/p4-b7-r8-r2-finalizer-executor.md)及固定外部首次材料。本轮只读核对和协调，没有运行产品、测试、辅助程序、安装或打包。

## 接受的证据和结论边界

接受 R8-R2 的 `review / finished` 执行方交付，作为独立复验输入。控制器收尾修正和同包 S1/S2 已完成；原 R8/R1 阻塞历史保留，不把历史首次失败改成通过。SETTINGS-001、CMP-06、LAZY-001、UI-02 及完整 P4-B 仍未关闭。

| 原始结果 | 核对结论 |
| --- | --- |
| 共用收尾自检 | 47 场景、267 唯一比较通过；第二版 10 场景、69 比较是受影响复验，不额外累加 |
| 普通 Node 集成 | 两次：首次失败保留，第二次 11,381ms 通过；旧 `fixture_listeners_query_failed` 缺原始查询回执，具体原因仍 unverified |
| S1 | 26/26 gates、39/39 比较；真实 UI 保存 dark/true，一次 recover 后保持；完整控制会话 40,560ms |
| S2 | 同 profile 原样续启，26/26 gates、42/42 比较；首次页面 dark/on、select dark、checkbox true；完整控制会话 33,646ms |
| S2 首样来源 | driver 设置写入、seed、recover 均为 0；设置文件与 S1 保存后同为 412 bytes、摘要一致，不靠再设置或刷新取得结果 |
| 生命周期 | 两次 root/worker 真实 exit0、signal=null，正常主窗口关闭，未强制清理；各自原始终态回执为进程/监听/窗口 0 |

S1/S2 原始 result 摘要分别为 `739e177c595704b968fc08aa19d1a7add57fab87e1b4d4c7aa7b0a4d5f81aa5a`、`f2cd82c958732d908fccfc3521f5badff3b0662fa956cb049ba3a457b9aaab66`。原始路径分别为 `C:/MarisSettingsR8/R8-R2-20261030-040716/evidence/settings-exe-S1/result.json` 与同根 `settings-exe-S2/result.json`。

设置文件摘要为 `c4a59c9ec06fe45910a5eab4d1bf0e9a438856cdcd064489f7cd9b6c055ff622`。driver 零写入不外推为监控了产品全部内部写入；资源结论来自已冻结实测回执，本轮没有额外运行系统枚举。controller 自身 elapsed 与完整控制会话计时分别保存，不混为一个时长。

## 固定输入及亲自核对

首次协调编辑前，R2 source 1377、交付 3、工具 6、输入副本 4、证据 255 均逐项匹配；原 1376 起点仅 executor 授权变化，无缺失。续接时再次核对三交付，并亲自复算 R8 构建 1365、产物 140、Python 资源 67，全部匹配。总控之后的协调变化由新 R10 起点明确纳入，不再要求旧 source 中这些协调文件仍匹配旧字节。

| 清单 | 条目数 | 原字节 SHA-256 |
| --- | --- | --- |
| R2 source | 1377 | `2cbc27ed7eb814a792b94aa896ae32d3aa1ad45c833f025d5dc0d40c3178356b` |
| R2 delivery-three | 3 | `bb1f735398a1d521f8f971b38635de930f34479cc6714108fbc7d58f94b55ee0` |
| R2 frozen-tools | 6 | `c2f231c2d30ad014bc87da919a50c6a0f441b755132680eb73e371b22b6e5472` |
| R2 inputs | 4 | `a05b47ad813e52a1b515a5138ee4b7111939f57c8bc13f3140c928f96144c053` |
| R2 evidence | 255 | `643d889a26c0b77157e63a8a9cf253f76109e233bd0ca2e063544b1b52735ab3` |

上述外部清单由 `C:/MarisSettingsR8/R8-R2-20261030-040716/evidence/closeout.json` 绑定，其 SHA-256 为 `7f1c23ab0c9cbfa578b5e9b136ec3b728b17917f4621917ca20882eff78edf24`。R8 完整历史依赖审计沿用已绑定结果；没有声称再次扫描全部依赖或运行加解密。

原独立 W1 的 63 项虚拟 profile/continuity 也已逐项复算匹配，来源 [original-profile.tsv](../tests/independent/desktop/evidence/r9-r1/original-profile.tsv)，清单 SHA-256 为 `575f132e0bc44a949391c9ab7c31747e4e21e58fdb8a344dc29a00e6639ce7ee`。原 [H1 7/7 通过](../tests/independent/desktop/evidence/r9-r3/helper-H1/native-result.json)及 W2 四条失败证据保持。H1 结果 SHA-256 为 `f6c493c244f18832b0e69e5fa7c45a09108e304bd72fb685951c92252b7a62e3`。

## 下一步：独立设置复验并续接剩余 Windows

发布 [P4-C12-R10-SETTINGS](coordination/prompts/p4-c12-r10-settings-windows-tester.md)与[新起点](coordination/snapshots/p4-c12-r10-settings-start.sha256)。唯一负责人是既有测试智能体，Executor/顾问停止。R8 系列 package1/1、EXE3/3 已耗尽；本次不再给执行方动态额度。

测试方先验证新增三字段只读接口、严格响应和启动水合边界，定向兼容只运行 settings-snapshot/settings-hydration 两文件 48 项一次，不重跑完整 217 项。随后使用固定 R8 新包、原 W1 完整虚拟副本，复验原 W2 四条同次首样断言；H1 已通过且来源相同，不重新解密建立基线。H2 仍要独立验证经过新产品续启后的主人/草稿连续性，不能用旧 H1 或执行方 S1/S2 替代。

已定位的工具适配在产品启动前解决：settings bridge 白名单为 getSnapshot/update；写接口仍仅接收 theme/reducedMotion/privacyMode。禁止旧工具发送 closePolicy。W2 保持原 quit 配置与首样前零改写；需要 hide/ask 的后续场景只在本轮产品完全退出后预置明确的虚拟设备配置。配置预置不是用户设置入口通过的证据，不能扩大产品 IPC。

Tester 系列累计产品2/8、helper3/6，本次最多使用剩余6/3，不增加上限：W2/W3、H2、W4/H3、W5/H4、W6、W7；每个不同场景一次，失败不重跑。新卡明确 H2 seed 和 H3/H4 读回、同源 Local State、合法关闭入口、已核实 UI/进程所有权及分段证据要求。真实设备能力不足只影响有依赖的条件，未知错误不自动分类为能力缺失。原24项完整预期与首次失败停止规则保持。

总控内部只读复核用于任务边界检查，不构成独立验收。新任务发布为 ready/waiting_user，实际 Tester 接单仍 unverified；不替用户启动侧边栏角色。协调与交付保存为明确未完成的本地检查点，不推送。P4-B 矩阵暂保持 1 passed、2 failed、19 blocked、2 not_run；P4-C 真正前端开发前仍须先提醒用户并复核既定效果图和模型分工。
