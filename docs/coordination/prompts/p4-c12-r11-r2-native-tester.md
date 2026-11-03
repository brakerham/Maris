# P4-C12-R11-R2-NATIVE：原生定位修正与剩余 Windows 验收

## 负责人、必读与当前检查点

你是既有Tester，本轮唯一执行负责人。按AGENTS读README、project-coordination、coordination/README、最新control、本人tester、本卡，再读[R1总控裁定](../../p4-c12-r11-r1-settings-native-coordinator-review.md)、[R1独立报告](../../testing/phase-4-c12-r11-r1-windows-report.md)、[R1任务卡](p4-c12-r11-r1-windows-tester.md)、原矩阵/人工清单及IF-003/004/005。Executor/顾问停止。

SETTINGS-001已限定关闭，IPC-ORIGIN-001及QUIT-001普通关闭范围保持关闭。R11独立41/321及109兼容、R1 W2/W3的18比较、H2的13比较均接受，禁止重跑。旧H1/W1/冷入口/恢复/模块/退出、执行方S1/S2仅引用。当前唯一阻塞是W4原生按钮/主窗定位，未形成产品缺陷证据。

所有获准门禁通过后同任务继续后续步骤；最终review/finished或blocked/finished，最终项目接受仍由总控决定，不自动派发新任务。

## 固定输入与文件范围

接单前核对[本轮固定起点](../snapshots/p4-c12-r11-r2-native-start.sha256)全部路径、原字节SHA-256、唯一排序/TAB/LF、staged=0；本人接单后日志单列。旧输入与首次材料不改写。R1 delivery129、tools17、evidence106、first103、archive30按清单基准根复算。

唯一受验包仍为 `C:/MarisIpcR9/R9-20261101-161412/workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。固定包/来源/工具版本与入口沿用[原R11固定输入](p4-c12-r11-origin-settings-windows-tester.md#固定输入)：核对closeout、构建1432/产物140/资源67、EXE/asar/lock及实际运行入口；不重装、不重复每条命令全扫历史依赖。源级新代码和生产分支裁剪等旧证据只引用。

仅新增 `tests/independent/desktop/r11-r2-native-*` 工具/配置/虚拟检查、`tests/independent/desktop/evidence/r11-r2-native/**`、`docs/testing/phase-4-c12-r11-r2-native-report.md`；更新本人tester，主报告/人工清单只追加，矩阵仅B充分证据下的状态/备注，原120ID/12列/原预期/A-C-D保持。产品/执行方测试/旧独立源码与证据/依赖/包/control/overview/快照和其他角色只读；无Git写权限。

外部仅新建 `C:/MarisC12/C12-R11-R2-NATIVE-<时间戳>`。先核实绝对边界、未存在、无reparse；普通复制不用junction。旧外部根保持，不清除旧profile或原始日志。必要只读观察按既有获准工具通道办理，不改系统/WMI/ACL/服务、安全软件，不RunAs或改变产品运行身份。

## 第一段：精确修正定位工具，禁止同标题取第一个

旧脚本的Main()将root PID下所有标题Maris的窗口视为主窗口；实际主窗和老化模态均为Maris，W4三次库存visibleMainCount=2。按钮首错未保存候选数量，不能预设零或多个。

在新副本中机械复用已成功的进程身份、异步观察、路径/时间、原生上下文和收尾逻辑；只修主窗/模态/按钮选择及相关回执。不重新开发通用进程管理器，不以产品启动检验控制器基本功能。

- 先验证实际root与已知树的exe、创建时间、父子及marker；精确排除本轮已验证观察器PID，不能按进程名称忽略。
- 在本轮所有权范围内记录窗口候选：HWND、PID、owner/根owner关系、类/类型、可见与启用、模态属性（能取得时）、有限白名单标题；UIA候选记录NativeWindowHandle/RuntimeId、层级、ControlType、已知按钮名分类、Invoke支持。未知值不补造；不遍历或保存无关程序正文、路径、命令行或用户内容。
- 主窗口与模态由实际所有权和结构区分；标题只能辅助，不能唯一标识。按钮仅在已核实模态内定位，按真实RuntimeId/句柄或等价元素去重；零、一、多分别记录，实际唯一且启用可操作才调用。不能取第一个、删除安全条件、用renderer假按钮、全局键盘盲按或调用产品内部删除接口替代原生操作。
- 固定按钮期望源于真实产品options：老化框保留/明确删除，首次关闭知道了，询问隐藏到托盘/退出/取消。明确保留与明确删除仍由各自不同场景执行，不因名字类似扩大匹配。未知辅助名称先留安全分类；不得在运行后为获得通过随意增加匹配规则。
- 每次动作前重新验证句柄身份/owner关系和当前状态，防止窗口关闭或句柄复用。普通收口只向正确主窗发WM_CLOSE；模态仍在时不把它当主窗。业务动作成功后明确等待模态消失，再正常关闭。不能为收口点击“明确删除”；未知定位异常只做已有身份约束内的有界定向清理，forced不得计正常通过。
- 查询阶段先即时记录候选数量与关系，再判定/操作，失败时也有安全计数和具体原因。保留首错、普通收口错及最终强制清理结果，finally必须落盘和释放，unknown不得填0。

目标前最多30分钟实际准备、3版有限更正（审批等待不计）。只用静态和纯虚拟候选集合检查同标题主窗+模态、零/多/重复按钮、跨PID/错误owner、不可用/失效句柄、已关闭模态、缺失/坏result、双错保留、比较ID唯一和记录脱敏。复用实际将运行的选择函数，不写与实现脱节的自检。无需新的Electron/Node进程夹具；真实应用/辅助UI额外启动0。新工具与实际输入清单完整冻结后才进入H0/产品。

允许在一次已授权场景内、有界等待原生窗口稳定并重新只读采样；这不是重启或更换选择器。候选尚未出现可在冻结窗口等待内观测，稳定的多候选/所有权异常须停止；最多5秒，单次observer8秒且受场景剩余截止限制。UIA读取成功不代表已具备Tray动作，not_implemented、unavailable与unknown必须分开。

## 第二段：新副本与只读 H0

源根 `C:/MarisC12/C12-R11-R1-WINDOWS-20261103-002800`，只复制 `profile-main` 和 `continuity.json`。按R1 [new-profile-after-stop.tsv](../../../tests/independent/desktop/evidence/r11-r1-windows/new-profile-after-stop.tsv)核对68项，其SHA-256为 `ea0462dbb09e264840a1e5daa73bda4cd7843264ecd92a42c1abcd03191aba12`；清单路径相对源根，不能再拼profile-main。核实相关旧目标已退出后普通复制，源和副本路径/大小/摘要精确相等。

旧W4强制退出后outbox密文已变化，**H2 seed结果不能直接当当前明文**。本轮唯一H0先从新产品副本复制完整Local State至全新helper目录，ready前同时绑定userData/sessionData；原生存储可用、同源上下文、身份与release全部通过后，逐段读取/解密/解析。

H0必须只读：对照R1 `helper-H2/native-baseline.json`（及native-result baseline.after）的五条记录，逐项比较draft/event/body/digest/state/createdAt/updatedAt、稳定owner及原continuity保护项，数量/集合完全一致。允许refresh token轮换，不要求token值相同；不记录明文token/正文。H0不是重跑H2，无seed、repair、reset或写产品配置。读取前后产品副本字节保持，helper自己的Chromium状态变化单列。不满足基线就停止并保留实际差异，不能重新生成数据进入W4。

准备时还须按真实当前时间计算候选集合：原continuity和近期queued必须仍未满30天，过期draft/queued属于候选、sending保护。若等待过久使保护对照也老化，停止并报告fixture时效变化，不能改OS时钟/改日期/reseed。本轮不自动刷新基线。

## 第三段：一次 W4-R 及后续场景

W4-R为新授权的有限补验，旧W4失败不覆盖。产品由固定Node直接spawn(shell:false)，Playwright仅connectOverCDP，动态端口loopback、独立marker和普通用户环境、无退出计时器；配套观察权限保持已核实上下文。

| 顺序 | 原要求与本次放行 |
| --- | --- |
| W4-R → H3 | H0通过，closePolicy仍quit，原生老化框选择默认保留；记录唯一owned模态与按钮，Invoke成功及模态消失后正常关主窗，10秒内自然退出/资源0。H3另一次只读原生读回全部五条语义与原ID不变，不以密文hash代签 |
| W5 → H4 | H3通过才同副本一次启动，明确选择删除；正常退出后H4只读证明仅当次展示的两条过期候选删除，原continuity、近期queued、sending三项保持。操作期间改变候选的更多并发条件仅引用已有源级证据，不额外操作真实数据 |
| W6 | H4通过，产品全退后按R1合法配置规定。可用且已冻结的本任务Tray动作适配器才允许hide_to_tray分支；当前只读根可用/适配未实现不能冒充设备不支持。本卡不扩建Tray框架：若适配仍not_implemented，在启动前冻结为保持quit，仅一次owned后端失效/显式恢复及原可支持的真实chunk失败/retry，正常退出；Tray相关留未验并说明工具范围 |
| W7 | W6通过，产品全退后预置ask_every_time、closeHintShown=false；一次启动内实际首次提示/知道了后隐藏、毛毛恢复、后续询问取消/隐藏、最终明确退出。须使用本轮已核实原生动作；若缺必要操作能力，启动前记未验，不使用全局按键或要求用户盲点 |

保留R1关于W6实际chunk请求、当前有效失败、撤销拦截与明确retry的原合同，不能删除/改写包、用假页面或额外冷启；不支持时准确unverified。预期故障本身不是停止条件，实际公开断言不满足才失败。W6后端只能停止已核实自有实例，不能影响外来程序。W7未使用Tray动作不等于Tray已验收。

H3/H4严格只读，分别全新helper上下文，同源Local State每次从当时新副本复制；owner、各消息语义与时间均有具体比较。不要只更改旧H2场景名使seed路径执行，目标前虚拟检查必须覆盖H0/H3/H4禁止写入。产品副本仅在W6/W7全退阶段获准预置closePolicy/closeHintShown，其他设置和消息不手改；严格三字段IPC不含closePolicy，不能调用非法设置接口。

## 明确额度、停止与交付

| 目标 | 历史实际已用 | 本轮新增上限 | 修订后的系列上限 |
| --- | --- | --- | --- |
| 产品EXE | 5 | 4：W4-R/W5/W6/W7各一次 | 9（原8，新增一次W4补验） |
| 原生helper | 4 | 3：H0/H3/H4各一次 | 7（原6，新增一次失败后只读基线） |
| package/安装/开发服务器/辅助UI夹具 | 0本轮 | 0 | 禁止 |

这项额外额度由本轮总控明确授予，不重置历史计数。实际spawn即计，未执行审批不计；无第二次W4-R或额外诊断启动。每个产品120秒（业务105、末15收口），helper60秒（末10收口），页面/原生稳定观察5秒，普通退出10秒，observer8秒且裁剪至剩余时限。

正式目标的有效比较失败、未知身份/工具错误或非预期异常，停止后续业务，只做必要有界收口；不能改工具后重跑。工具问题不自动定级产品P1；原生保留/删除/关闭提示是预定操作，不按“任何弹窗”误停。不使用系统注销/重启、启动项/多屏/安全设置变更、真实账户/provider、Docker/OpenClaw/微信或个人数据。

记录接单、实质进展、阻塞、交付及当前执行快照；长操作前写下一检查点，有控制权时至少10分钟心跳。首次源码/操作前后安全候选/每条expected与actual/真实退出/普通与强制收口分别保留。只清理已核实本轮临时项，旧根与新虚拟profile/首次材料保留。终点核对起点授权变化、固定包/工具/旧首次/旧68项现场不变；新清单基准根/格式明确，避免自引用。

报告沿用原24项完整要求，历史已过、本轮和未验分开；SETTINGS-001/IPC-ORIGIN-001不重新开启或重跑，完整CMP-06、SUP-06、UI-02/LAZY-001、P4-B据足够证据分别判定。提交review/finished或blocked/finished，不替总控签全阶段。真正前端实现前的两张参考图与模型分工提醒保持。
