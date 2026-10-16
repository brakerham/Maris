# P4-C12-R9-R1：H1 观察工具修正与剩余 Windows 验收

## 身份、必读与固定输入

你是既有测试智能体，本任务唯一负责人。总控已接受 R9 独立退出边界及 W1，关闭 QUIT-001 的普通主窗口关闭缺陷范围。执行方与技术顾问停止。当前是测试工具续验，不是产品返修或 P4-C 界面实现。

按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、本人 tester 和本卡，再读：

- [总控 R9 裁定](../../p4-c12-r9-quit-h1-coordinator-review.md)、[R9 报告](../../testing/phase-4-c12-r9-quit-windows-report.md)、[原 R9 卡](p4-c12-r9-quit-windows-tester.md)。
- `tests/independent/desktop/evidence/r9-quit/` 下 delivery、end-audit、windows-plan、`windows-W1/result.json`、`windows-W1/journal.jsonl`、`helper-H1/process.json`、`helper-H1/journal.jsonl`、`h1-first-analysis.json`；H1 native result 本来未生成，不能当作漏读文件。实际源码为 `r9-quit-h1-attempt1-run.mjs`、`r9-quit-helper-os.ps1`、`r9-quit-h1-native.cjs`。
- IF-003/004/005、原矩阵和人工清单。24 项完整要求不变，不能将助手工具或虚拟生命周期的通过写成原生设备通过。
- [本轮固定起点](../snapshots/p4-c12-r9-r1-start.sha256)：仓库根、原字节、POSIX 排序、UTF8 无 BOM、`path<TAB>sha256<LF>`，不含自身。全部匹配、staged=0 后接单。

固定包、工具和依赖继续使用原 R9 卡输入表，不下载、安装或换版本。受验根 `C:/MarisQuitR7/R7-20261014-191500`，固定 EXE `workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`；asar、资源、dist、12677 项依赖按原清单复核。EXE SHA-256 为 `183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65`，asar 为 `16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3`，lock 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

## 明确复用与文件范围

R9 的 8 独立节点/235 比较、48 开发兼容及 W1 的 62 比较已通过，不再执行。旧模块 13 节点、冷入口 B、完整恢复、注册/outbox 集合及已通过公开条件同样只引用。旧证据和失败保持不变。不要新建退出回归、完整169项回归或只观察不验收的顾问任务。

允许写入仅：

1. 新 `tests/independent/desktop/r9-r1-*` 工具副本、必要配置及局部工具自检；每个目标前冻结源码与最小差异。
2. 新 `tests/independent/desktop/evidence/r9-r1/**`；各场景首次材料独立目录，已落盘记录不覆盖。
3. 新 `docs/testing/phase-4-c12-r9-r1-h1-windows-report.md` 及本人 tester 状态文件。
4. 原 C12 主报告与人工清单仅追加；矩阵仅按实际证据更新 B 状态/备注，120 ID、12 列、原预期及 A/C/D 保持。

旧 `r9-quit-*`、全部旧 evidence、产品/开发测试、其他独立测试、包、依赖/lock、Forge、控制/overview/snapshot 和其他角色文件只读。测试方无 Git 写权限，无构建、package、修改 asar/fuse 或生产接口授权。

## 先修已定位的观察缺口

首次 H1 底层原因仍为 unknown。下面修正的是可定位的工具问题，不声称已证明权限、8 秒期限或任何某个查询是首次根因。

- 保留直接 spawn(shell:false) 及 PID/创建时间/父子/固定 executable/任务 marker 绑定；新 ready 回执还必须核对 PID 等于本次 spawn PID、属于本次新输出目录。冻结 helper 脚本摘要并核对实际运行路径后才允许 release，不采用 launcher PID 提升或进程名查杀。
- observer 使用可观测、可取消的异步子进程，不让同步等待阻塞控制器总截止时间。调用前及 terminal 即时落盘：唯一调用 ID、阶段、起止/耗时、真实 status/signal、允许列举的 error.code、安全错误类型、stdout/stderr 字节数与摘要。原始输出如需保留只在受限外部根；不得将全机进程命令行、环境、连接串或秘密写进仓库。
- 将**身份查询**与**资源查询**拆分：release 前先完成 root 及受管子树的身份核验，不要求同时编译窗口枚举类型或取完整监听列表。原来需要的最终进程/窗口/监听检查仍必须完成，不能借拆分省略。身份失败或 unknown 禁止 release。
- OS helper 对 process query、类型准备、窗口查询、监听查询和 JSON 输出分别写 enter/terminal；显式记录成功空集合与查询失败。不能用 SilentlyContinue、空 stdout 或 parse fallback 把 unknown 变成 0。
- 观察调用单次仍最多 8 秒，辅助总预算仍 60 秒，至少预留最后 10 秒用于停止与收口；身份核验、native 操作和资源观察共用这个总上限，不因拆分重置总时钟。每次调用时限取 8 秒与当前阶段剩余总时间的较小值，收口阶段不能叠加多个完整 8 秒调用越过总限；来不及完成的观察记 unknown 并停止，不写 0。controller、observer、helper 的各自真实退出码分别记录，未知不补 0。观察器超时也只能清理已登记、身份匹配的本轮子进程。
- 保留已有定向退出/清理能力，不另造 Windows Job、固定进程数上限或通用框架；任何观察权限不足显式分类并停止对应目标，不反复更换权限尝试。

目标前完成语法/参数/列数/JSON/schema/唯一码校验。清单格式由真实首行和冻结格式确定，特别区分两列 `path/hash` 与三列 `path/bytes/hash`。仅用虚拟输入验证正常、非零、超时、解析失败、拒绝访问和空集合分类，不导入产品、不启动 Electron，不计产品验收通过。

另允许 **一次只读现场工具自检**：仅以当前任务 controller 的固定 Node 路径、PID、父 PID 和创建时间验证查询/捕获通道以及资源查询返回状态；不启动辅助试跑、不解除任何 helper release。自检进程与 observer 均有界退出。它只证明工具能观察当前 controller，不能代替之后真实 helper 的独立身份核验。

本轮目标前已证实的纯工具配置/记录错误可使用最多一次修正：保留首次代码/日志，新 attempt 只修工具且重做受影响自检，不改业务预期、selector、数据或时限。目标实际启动后未知异常、安全/身份问题、有效产品比较失败均不适用修后重跑。旧 R9 已使用的一次工具更正保留，新卡只授权这里的一次目标前更正，不追溯改变旧结果。

## 虚拟 profile 延续与原现场保护

原 R9 根为 `C:/MarisC12/C12-R9-QUIT-20261016-011200`。只读确认它的 marker、W1 来源和登记进程退出；原 `profile-main`、`continuity.json`、输出和 H1 首次记录均不回写。仅这份 W1 生成的虚拟 profile 可用于本轮，不接触其他旧 profile 或真实个人数据。

在新 `C:/MarisC12/C12-R9-R1-<时间戳>` 根中普通复制完整 `profile-main` 与 `continuity.json`。复制前核实绝对边界、无 symlink/junction/reparse；记录源/副本逐文件字节摘要，源在本轮前后保持。目录存在不是匹配证明。复制失败停止，不转而直接使用旧可写目录，不遗漏数据库边文件，也不输出虚拟秘密正文。

新 helper 始终使用新根内独立 helper userData，与产品 profile 分开；输出目录/marker 也新建。H1 只读产品 owner/outbox 的解密后安全 count/digest/ID 相等结果，不 seed，不改产品配置。H1 前后核对产品文件原字节。H2 才可按冻结计划向这份**新副本**写纯虚拟老化 fixture；不改系统时钟。报告准确称为“W1 关闭后的同内容虚拟 profile 副本续启”，不能写成原目录原地续启或真实用户迁移验收。

跨重启 owner 比较使用稳定 owner 标识/安全摘要，不将合法 refresh token 轮换判为换人。任何明文 token、密码、正文、内部地址只可瞬时处理；仓库仅存安全枚举、相等布尔、计数/摘要，不存解密输出。

## 有限预算及同任务继续

| 范围 | 旧 R9 实际已用 | 本轮最多新增 | 跨两轮总上限 |
| --- | --- | --- | --- |
| 固定产品 EXE | 1（W1 已通过） | 7 | 8 |
| safeStorage 辅助 | 1（失败 H1，无解密） | 4（恢复 H1、H2、H3、H4 各一次） | 5 |

**总控在此显式增加一次 H1 恢复额度。** 原失败启动不消失、不重置为0，不为了保持旧4上限删减保留/删除后的读回。没有第三次 H1 或预算用满要求。单实例第二进程也计产品一次。每产品仍最多120秒、每辅助60秒；产品普通退出相关原观察上限10秒、页面观察5秒及生产停止预算保持。

冻结新 Windows 计划后依次执行：

1. **恢复 H1 一次**：新身份观察、ready PID/source 匹配后 release，取得 native safeStorage 基线、owner/outbox 与 continuity 的有效比较，未 seed，正常退出及资源收口。原 H1 未完成结果不回填。
2. **W2/W3**：W2 用新 profile 副本续启；首次持久化 UI 取样前不写设置。验证设置、同 draft/request/event ID、owner 会话连续性；正常关闭策略/hide/ask/毛毛/真实 Tray 的尚缺条件按原合同。W3 仅作为 W2 活跃期间的第二实例，身份与退出独立记录，不用总进程数猜实例。原生按钮仅用核实 owned PID/窗口/按钮的 UI Automation。
3. **H2**：产品退出后比较与 H1 的稳定 owner/草稿证据，再 seed 有界纯虚拟老化记录。提前冻结数据、操作和预期，不在产品运行时改密文。
4. **W4 → H3、W5 → H4**：分别真实默认保留/取消与明确删除，并实际解密读回计数/摘要。仅文件存在、密文 hash 变化或虚拟 dialog 替身不能签收。H3/H4 未执行不冒称持久化已验证。
5. **剩余无依赖条件**：沿用原 R9 windows-plan 的 W6 及有明确新增覆盖的保留额度；包括受管后端故障/恢复、安全入口及可实施的真实 chunk 故障。先记录新增覆盖与不重复理由。已通过 W1 的普通关闭不是独立重跑节点，作为后续场景必要收口只计该场景生命周期证据。

真实 chunk 仅允许当前实际请求的临时 CDP 拦截，取得故障来源、当前有效加载失败、局部安全页/Shell/导航/Agent 保持及撤销后明确 retry。不得改包、删 chunk、塞假页或反复冷启动找命中；file/asar/cache/设备限制有直接证据时只保留该条件 unverified。

只操作本任务核实的虚拟进程和窗口；不触碰外来应用、真实账户、provider、Docker、OpenClaw、微信 V002、OS 注销/重启、启动项、主题、多屏或安全软件。人工检查条件只更新清单，不要求用户此刻操作电脑。

## 停止、证据与交付

未知所有权/资源收口问题、有效来源下的产品比较失败立即停止后续目标，保留首次源码/记录/真实退出，不能再丢失具体安全 expected/actual 或底层工具分类。目标前自检失败与目标已启动失败分开；审批未执行不计启动，实际 spawn 即计预算。

明确局部能力不可用只阻塞依赖该能力的条件；资源安全收口后继续无依赖且已冻结的场景。不要将任何未知错误自动解释为设备不支持，也不要因为单项未授权人工条件使全部无关项目永远不执行。

新报告记录：工具差异和静态/现场自检、各实际启动与累计预算、首次断言/来源、profile 副本边界、H1 只读及 H2 seed 授权、自然/强制退出、unknown、剩余24项映射。R9 的8/48/62只列历史复用，不计本轮新增；矩阵整项全部条件具独立证据才可passed。LAZY-001/UI-02及P4-B最终由总控裁定。

结束复算新仓库起点、受验包/依赖、旧首次证据和原 R9 profile；四个共享测试文档变化精确列举，不宣称它们的旧清单仍全字节匹配。保留新虚拟 profile、基线、首次材料；仅清理本轮路径已核实且无reparse的临时项，完整后代查询受限保持unverified。

接单/里程碑/阻塞/交付更新本人快照，超过5分钟先写下一检查点，有执行控制时至少10分钟心跳。最终 `review / finished` 或 `blocked / finished`，不自动创建新任务、启动其他角色或推送。真正前端设计阶段的参考图和模型策略提醒仍由总控执行。
