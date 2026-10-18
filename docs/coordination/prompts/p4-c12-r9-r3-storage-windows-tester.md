# P4-C12-R9-R3：原生辅助上下文修正与剩余Windows续验

## 唯一负责人、必读与固定输入

既有测试智能体负责，执行方/顾问停止。按AGENTS读取必读、最新control、本人状态、本卡，以及[总控裁定](../../p4-c12-r9-r2-native-coordinator-review.md)、[R9-R2报告](../../testing/phase-4-c12-r9-r2-path-windows-report.md)、[R9-R2卡](p4-c12-r9-r2-path-windows-tester.md)、[R9-R1完整Windows卡](p4-c12-r9-r1-h1-windows-tester.md)和原R9 Windows计划。本卡覆盖原生上下文、记录及新增一次H1额度；其余原业务预期和安全边界保持。

[新起点](../snapshots/p4-c12-r9-r3-start.sha256)在仓库根按原字节复算，唯一路径有序、UTF8无BOM/LF、`path<TAB>sha256`，全部匹配且staged=0后接单。固定受验根仍为`C:/MarisQuitR7/R7-20261014-191500`，EXE/asar/lock及完整依赖不变；R9-R2的114交付、89首次及9份target源码按真实清单核对。不要重新安装、打包或更换任何版本。

已通过的38项路径/回执工具集合及现场Node门禁只引用；真实H1身份/ready/release仍须每次按当前PID实际核实，不能把历史身份复用于新进程。W1、退出8节点/48兼容、模块13、冷入口B、独立恢复和其他已过公开集合均不重跑。

## 写入边界

- 新`tests/independent/desktop/r9-r3-*`原生辅助、控制器、有限上下文/分段记录辅助与局部工具检查。
- 新`tests/independent/desktop/evidence/r9-r3/**`和`docs/testing/phase-4-c12-r9-r3-storage-windows-report.md`；每轮版本、首次错误分别保留。
- 本人tester；原主报告/人工清单只追加，矩阵仅有证据的B状态/备注；120个ID、12列、原预期及A/C/D不变。

旧工具/首次证据/三个旧虚拟现场、产品/执行方测试、包/依赖/lock、Forge、其他角色、control/overview/snapshot只读，无Git写权限。复用R9-R2已过身份/观察器/parser，保持原文件字节不动；必要新入口配置使用新文件，核对其实际新根/marker/参数和源码摘要，不复制后另造身份算法。

## 先补完整加密上下文，保持隔离

本轮静态已确认：R9-R2 helper在空userData中初始化，读取另一profile的密文，未复制同源Local State。两份encrypted_key字段非空且字符串不同；旧错误具体操作仍unknown。不得声称已经证明损坏或设备不支持。

1. 新现场为`C:/MarisC12/C12-R9-R3-<时间戳>`。核对原R9进程已退出、源marker和63项`evidence/r9-r1/original-profile.tsv`后，普通复制原R9的profile-main和continuity.json到新根；大小/摘要/完整库存匹配，无reparse和越界。原R9、R9-R1、R9-R2三份现场全部只读，不在旧目录重做任何操作。
2. 每个H的helper目录都须全新。**spawn之前**，从新产品副本的`profile-main/Local State`复制完整文件原字节到该helper目录的`Local State`。H1来源为63项已冻结副本；后续H来源为对应产品场景自然结束后的当前新副本。只复制这一个配置文件，不访问真实AppData、不导出/解密key、不构造或替换os_crypt字段、不将Local State或密钥值写入仓库。
3. 复制前后验证源/目标完整文件大小与摘要相等、JSON可解析、所需加密字段存在；安全回执仅布尔/计数/文件摘要。字段相等在内存比较，禁止记录值或其明文。辅助顶层同步设置`app.setPath('userData', helperDir)`与`app.setPath('sessionData', helperDir)`，在ready前完成；ready时验证两路径确指本轮helper及加密字段仍等于来源，不在ready后换目录/复制配置。完整Local State原字节相等仅要求于spawn前复制核验，ready后无关字段更新不据此判失败。release前仍须本次身份、PID/path/hash/marker/callID通过。
4. H1不加载产品main、OwnerSecretStore或其他可能写repair的生产代码；直接读取新副本owner/outbox并用原生同步safeStorage验证，产品文件前后63项保持。helper自身正常生成的日志/cache及Local State其他字段变化分列；后置核对加密字段仍保持来源，不要求helper整个Local State因无关字段重写而逐字节不变。
5. H2/H3/H4使用同一准备逻辑，每次在产品已退出后从当前新产品副本预置同源配置。H2只有在读回与H1基线比较通过后才可seed既定虚拟老化数据，使用该同源原生safeStorage写新副本；H3/H4只读验证保留/删除。不允许空helper生成另一套上下文，也不回写helper的Local State到产品。

来源见总控裁定中的Electron44.4.5固定版本源码。这里仅修辅助工具读取条件，不改变产品加密协议、生产接口、fuse、TTL或任何账户规则。新H1真实解密仍未验证，不预签通过。

## 操作分段记录必须在目标前验证

把原native串联表达式拆成以下可观察阶段，保持原7条H1业务比较及预期：上下文核对、availability、owner文件读取、owner解密、owner JSON解析、owner schema/ready/非明文比较、continuity文件读取/解析、outbox文件读取/解密/解析、count/continuity/非明文比较、baseline/最终结果写入。不要在最外层catch只剩operation_error。

每阶段即时保存enter以及success/error terminal，记录逻辑文件角色、唯一ID、时间/耗时、结果类别、真实error.name与允许列举的error.code；例如ENOENT/EACCES/EPERM/EIO和固定native_decrypt_failed/json_parse_failed。只对已知固定库错误作枚举映射，未知为unknown并保留阶段；**不保存原始message/stack/cause、明文、token、密码、字段值或解密后完整对象**。业务比较保留安全expected/actual，既有baseline只用允许的虚拟身份/内容摘要，稳定owner不以可合法轮换的refreshToken相等代替。

error后的后续操作标not_run，不伪造actual；写结果本身失败须有控制器的独立安全终止回执。controller先收集native已写的阶段/结果，再按真实退出码判断；非零不得丢掉native首错。控制器/observer/native退出各记各的，原日志流捕获与截止不因分段而省略。局部测试证明即时落盘、唯一码和非零下结果收集，不只验证最终全绿。

允许30分钟、最多3轮纯工具开发检查：仅虚拟JSON/密文替身/失败注入和临时目录，不启动Electron、不调真实加解密、不碰旧profile。覆盖同源配置复制与缺失/非法/不同来源拒绝、ready两路径绑定、读取/解密/解析分别失败时阶段和安全分类、结果写入失败及控制器保留首错。实际H1必须调用同一记录/准备逻辑，不能只测无关替身。旧38项全量集合不重跑；若不可避免影响共享身份语义，停止返回总控，不借此扩大。每轮源/结果/差异保留，工具失败不算产品失败。

全部新脚本语法、依赖路径、清单格式、记录字段/唯一ID检查通过后冻结H1全链与本轮Windows计划。旧现场Node检查无需再建新一轮；新目标每次仍做真实身份观察。正式目标前纯工具静态修正在上述3轮内完成，实际spawn后没有修后重跑额度。

## 明确预算和执行顺序

| 目标 | R9系列已用 | 本轮最多新增 | 新系列总上限 |
| --- | --- | --- | --- |
| 产品EXE | 1 | 7 | 8（不变） |
| safeStorage辅助 | 2 | 4：新H1、H2、H3、H4各一次 | 6 |

总控显式增加一次H1恢复额度；R9失败H1与R9-R2失败H1都保持实际已用，R9-R1没有helper启动。新H1仅1次，不要求用满后续预算，不添加用于对比失败上下文的第二个Electron。产品每场景120秒、helper60秒/至少10秒收口预留、observer8秒受剩余总时间裁剪、页面5秒和普通关闭10秒均保持。

新H1同源上下文、完整7比较和安全收口通过后，**同任务**按原卡继续W2/W3→H2→W4/H3→W5/H4→W6及有明确新增覆盖的保留场景，不再等派发。W2首次持久状态取样前不写设置；H2不改OS时钟；真实原生按钮/Tray只操作已核实owned UI。真实chunk只能临时拦截实际请求，不改包、不删文件、不反复启动找命中。退出和持久化子条件保持原要求。

未知所有权/收口、真实原生操作异常或有效产品比较失败立即停止扩大；本轮必须能区分具体阶段，而不能猜定产品损坏。只有明确证实的设备能力缺失才可将依赖场景标未验并安全继续无依赖已冻结场景。产品/H1失败不能用新profile、新密文、重置owner、复制helper配置到产品或删除密文绕过。

## 交付

记录工具开发、旧通过引用、新H1、每个Windows场景和累计启动数，产品与helper分别统计。报告解释“同内容虚拟profile副本续启”，不写成真实用户迁移或旧原目录原地恢复；H1上下文修正成功也不能反证旧operation_error精确阶段。

原24项完整要求不缩减。LAZY-001/UI-02及P4-B不提前关闭；缺设备条件保留人工清单，不要求用户此刻操作。禁止Docker/OpenClaw/微信V002、真实provider/个人数据、系统安全/网络/时间/注销/启动项设置或其他角色启动。

接单/实质进展/阻塞/交付写本人快照，超过5分钟先记检查点，控制可用时至少10分钟心跳。收尾核对新起点、旧首次、包/依赖与三个旧profile；本轮新副本在H1只读阶段保持，H2及产品实际写入分阶段记录，不要求整个已运行profile永久原字节不变。最终review/finished或blocked/finished后停止。真正前端阶段的参考图及模型分工提醒保留。
