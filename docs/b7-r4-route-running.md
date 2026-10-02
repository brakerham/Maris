# P4-B7-R4-ROUTE 执行方运行与交付说明

状态：`review / finished`。执行方完成路径最小修复、打包前 UI-04 完整开发映射、有限自测、新 package 与真实 EXE 检查并停止。不是独立验收，不关闭 PATH-001、不宣布 UI-04 或 P4-B complete。

## 起点、范围与根因

最新 control `2026-10-02T16:34:00+08:00`；按 AGENTS 读取项目入口、协调规则、角色与完整任务卡，读取 C12-R2 总控核对/报告/首次 path 代码及 log、IF-003 §5、IF-004/005、R3 说明。起点 `docs/coordination/snapshots/p4-b7-r4-route-start.sha256`：352/352 matched、0 missing/mismatch，SHA-256 `5a39eb876fef6d4965c5fc89bb1cf3000a098fe56a7d6985e54ffdf2f52964ad`，staged=0。

仅修改 registry.ts（path 查重）、registry.test.ts、executor；新增本说明与 R4 source 清单。其他产品/测试/独立证据/报告/矩阵/冻结/control/其他角色/依赖/lock/构建 helpers 不修改；无 Git 写操作。

首次独立事实是两个合法虚拟 contribution 的 route ID 不同、path 相同却返回 2 个贡献。原实现只有 route ID token。registry.ts:40 增加 `route_path:${route.path}`，独立于 `route:${route.routeId}` 和其他身份命名空间，沿用既有局部 seen 集合及 desktop_registry_conflict。完全相同字符串全局拒绝，所有输入先严格解析；不会覆盖、部分返回、变更输入或污染下一调用。不归一化大小写、尾斜杠、参数或模式，不扩大 path schema。

## 打包前 UI-04 完整已定义注册映射

原矩阵 UI-04 输入是 hostUiMajor、route/path/setting/profile/companion 冲突，预期不兼容/冲突稳定失败且 Shell 无具体 moduleId 业务分支。IF-003 §5 补全以下约束；IF-004/005 未撤销。行为结果来自本轮定向 `tests/directed.json` 的 54 passed（registry 52、Shell 1、composition 1），TypeScript/lint exit 0。原 26 节点及断言保留，新增 26 节点；已有充分断言不另写镜像测试。

| 已冻结条件 | 产品位置 | 开发节点和实际证据 | 结论层级 |
| --- | --- | --- | --- |
| hostUiMajor 精确为 1 | registry.ts:11 | 新 incompatible/mistyped hostUiMajor：0、2、字符串 1 均拒绝 | 行为通过 |
| module 全局冲突 | registry.ts:36 | 原 every registry conflict：duplicate module 拒绝 | 行为通过 |
| Profile 全局冲突 | registry.ts:37 | 原 every registry conflict：duplicate canonical Profile 拒绝 | 行为通过 |
| route ID 全局冲突 | registry.ts:39 | 原 route 冲突；新 equal route IDs/different paths，双顺序拒绝 | 行为通过 |
| 完全相同 path 全局冲突 | registry.ts:40 | 新跨模块双顺序、同模块多 route 双顺序、末 route/末 module 冲突；无输出/输入不变/下次成功 | 行为通过 |
| setting 全局冲突 | registry.ts:41 | 原 R3 同/异 schema 双顺序及同模块重复；保持原断言 | 行为通过，不重做独立关闭 |
| appearance 全局冲突 | registry.ts:38 | 原 every registry conflict：duplicate appearance 拒绝 | 行为通过 |
| module/local ASCII 语法，不 trim/lowercase/Unicode 归一化 | registry.ts:3、9、14、16、17；Python contracts.py:35、75 | 新 ASCII module/route/setting/appearance：大写、连字符、前后空白、换行、Unicode/全角、空值、65 位拒绝；原 canonical Profile 语法/长度 | 行为通过；Python 仅只读语法对照，未跑 Python |
| canonical Profile 与长度/版本语法 | registry.ts:4、15 | 原 canonical grammar、14 非 canonical 参数、64/65 边界 | 行为通过 |
| ASCII 三段 SemVer | registry.ts:5、10；Python contracts.py:36、86 | 新 8 节点拒绝前导零、缺段、后缀、空白/换行/全角 | 行为通过 |
| 严格对象解析 | registry.ts:8、13～17 | 原 extra top-level、新 undeclared nested route fields 均拒绝 | 行为通过 |
| module major 与 Host 相同 | registry.ts:59 | 原 strict Host intersection：1.2.3 兼容、2.0.0 不兼容 | 行为通过 |
| Profile 属于 Host 摘要 | registry.ts:60 | 原 canonical 成功、legacy Profile 不导航 | 行为通过 |
| 所有 expected API prefix 属于 Host | registry.ts:61 | 原 empty Host prefixes 排除模块 | 行为通过 |
| setting schema version 精确相等 | registry.ts:62 | 原 schemaVersion 2 Host 不兼容，1 成功 | 行为通过 |
| 未知/禁用/桌面缺失模块不进入交集 | registry.ts:55～58；composition-root.ts:82～84；renderer/main.tsx:23 | 新 missing/disabled 排除；原 composition 实际调用交集，unknown Host 不返回；原 different keys 保留 daily_finance | 行为通过 |
| 任一冲突整体拒绝、无跨次状态、输入不变 | registry.ts:33～48 | 原 every conflict/setting recovery，新末尾 path 冲突 output undefined、输入精确相等、随后合法编译成功 | 行为通过 |
| Shell/main/preload 无具体 moduleId 业务分支 | Shell.tsx:13～18；main/index.ts:92；全部 preload 文件；renderer/main.tsx:23～31 | 完整只读查看：Shell 由贡献生成导航/面板，main 注册首版 contribution 后交 composition，preload 窄 IPC 不按 module ID 分派；未发现具体 moduleId 比较/条件业务分支。原 Shell 行为和 composition 虚拟端口消费各 1 passed | 结构只读核对；不冒充真实第二模块/Windows导航运行证明 |

目前未发现必须越界修复的上述明确注册条件缺口，可进入完整开发回归与新包门禁。renderer 当前 lazy import 固定首版 daily-finance 页面，不能据此声称第二业务模块加载能力或 lazy 故障隔离通过；这些实际界面/设备条件保留独立任务。main 首版 contribution 注册、默认 appearance 字符串不是具体 moduleId 条件业务分支；未修改它们。

不同大小写/尾斜杠的输入仍精确保留，只证明不擅自归一化，**不证明** React Router 大小写、动态参数、模式重叠或保留 settings 路径等未另冻结语义没有歧义。未知语义不扩展合同，也不计为 UI-04 独立通过。

## 首次与当前开发结果

证据根 `C:\MarisRouteR4\R4-20261002-164600\evidence`。首次红灯只选新增跨模块同 path 两顺序：2 failed/0 passed、26 filter 未选；没有 skip/xfail 修改，未选节点不算执行。修复后定向 3 文件 54 passed/0 failed/0 skip；registry 52（原 26+新增 26），Shell/composition 各 1。TypeScript 无诊断、lint 通过，均 exit 0。独立测试执行次数为 0。

原始 `tests/red.json/log/red-exit.json`、`directed.json/log`、`typecheck.log`、`lint.log` 永久保留。唯一完整回归为 14 文件 124 passed、0 failed/skip（98 基线+新增 26）；完整和定向/红灯重复节点不叠加称唯一案例。

## 隔离环境与前置记录

新普通根 `C:\MarisRouteR4\R4-20261002-164600`，创建前验证绝对边界及不存在；只读来源 `C:\MarisRegistryR3\R3-20261002-111556`。源码 352、普通依赖实际 12677/12677、第三方冻结 12443、Electron dist 73、工具 3 全部 matched，0 copyDifferences/链接；附加 234 项是现有 @maris/desktop 物化 workspace 包。复制后只同步两授权源码，缓存/TMP/证据专属，不依赖旧 .bin shim。

固定 lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`，deps manifest `15f5613ce7744083a81c05c68ab06e06b6aa0b6e30f0c9c98ed933d87899e04c`，dist manifest `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`。Node 24.21.0 / pnpm 12.7.0 / Electron 44.4.5 / Playwright 1.63.0 保持固定，Python 沿用已验证路径；未安装、下载、audit 或修改永久 PATH。

首次目标启动前工具复制笔误：猜 `tools/pnpm/pnpm.exe` 不存在，普通依赖复制实际 robocopy exit 1（成功复制）；定位实际 `tools/pnpm/pnpm-native.exe` 后一次定向修正。首次错误在 inputs/tool-copy-initial-failure.json，copy-result.json 是复制真实退出值；没有目标启动或预算消耗。该失败记录的 sourceDependencyCopyExit=0 是手工记录误填，以 copy-result.json 的 1 为准；这是复制成功码，不是产品失败。只读初始 glob/猜测文件路径未找到也记录，随后改用明确 rg --files 结果，不运行未知模块。

后续外部 package/EXE 前重读 control。旧 R3/R2/LOCALZIP 依赖/源码/包/profile/证据保持只读；真实 Windows 原生提示、Tray/注销/启动项/多屏等不能由本轮 smoke 代替。禁止其他角色/独立验收、Docker/PG/OpenClaw/微信/DeepSeek/provider 或 Git 写操作。

## 新包与真实 EXE 结果

所有前置通过后 package 唯一 1/1，固定 Node 直接运行现有 scripts/package-desktop.mjs，实际 Forge CLI 的 execPath/argv1、PATH 首两项、ZIP 记录在 actual-forge-env.jsonl。固定 Node/pnpm 是本次子进程环境，不改永久环境。官方 LOCALZIP 普通目录及 158184819 bytes、SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` 通过实际校验，Forge electronZipDir 一致且没有 download 冲突。

| 验证组 | 次数和结果 | 证据 |
| --- | --- | --- |
| 修复前自有路径红灯 | 1 次，2 failed，26 filter 未选；exit 1 | tests/red.json/log、red-exit.json |
| 修复后 registry/Shell/composition | 54 passed、0 failed/skip，exit 0 | tests/directed.json/log、directed-exit.json |
| TypeScript / lint | 均 exit 0，无诊断 | tests/typecheck.log、lint.log 与各自 exit JSON |
| 完整开发回归 | 唯一 1 次，14 文件 124 passed、0 failed/skip | tests/full.json/log、full-exit.json |
| package | 唯一 1 次，exit 0、signal null，7571ms，stderr 0 bytes | package-started/result.json、stdout/stderr.log |
| 静态新包 | 7/7 全通过 | static/result-v4.json、reader.log、out/asar/Python manifests |
| 双 bundle 来源绑定 | main 和 renderer 均含 path/route ID/global setting 三种独立 token，新 asar 与 R3 不同 | static/registry-source-binding.json |
| 真实 EXE | 唯一 1 次，19/19 门禁通过，exit 0、signal null，34835ms | final-exe/result.json、final-exe-driver.log |

新根 out/Maris-win32-x64 下：

| 产物 | 大小/数量 | SHA-256 |
| --- | --- | --- |
| Maris.exe | 246032896 bytes | `d5868736cbdf63f717f0ea853141b980d06cefc10a3c05196e8856cbe3a4de2b` |
| resources/app.asar | 759878 bytes | `9a4da50b2c5583e6f2337bdff43e399cd454c360fa6169b1667a1e4506c337d4` |
| out-manifest-v4.tsv | 140 files、386493060 bytes | `3e00e2a4851181ba7b6351ce9b0e6c1523f320b002f500403ffa654f08a942df` |
| 构建输入 workspace-source.sha256 | 352 项 | `b16283e1f881054afd8d555dd43e81d55fa60eebfe86006b1565f97465531900` |
| registry.ts | 仅增加 path token 一行 | `a3bc948f77da7d227312652005147a5cd15e0991be5a050566941c2178a03edf` |
| registry.test.ts | 原 26 保留、新增 26 | `ddfb2e911674779670ff9e71caf339fb9bfca8cda6725a8ac837393bc49a8c2b` |

静态资源 67/67 matched，missing/extra/mismatch 0；asar 11 files、0 links/unpacked；fuses v1 前六项 48/49/48/48/49/49 符合冻结，路径/内容污染 0、staging 0。v4 文件名是既有证据格式，本轮内容来自新产物。main `.vite/build/main.js` 和 renderer `.vite/renderer/main_window/assets/index-B8hApuvH.js` 都是 route_path:${s.path}、route:${s.routeId}、setting:${s.key}；这是来源证据，行为由注册测试单独证明。

EXE 用固定 Node spawn(shell:false)、Playwright 仅随机 loopback CDP 附加；没有 _electron.launch、app.asar loader、PID 提升或新进程数量门禁。全新虚拟 profile/owner/database、新任务 root marker、Python 3.14.7、产品支持的 30000ms 自动退出、120 秒硬上限；NODE_OPTIONS/ELECTRON_RUN_AS_NODE 移除，APPDATA/TMP 隔离。

19 门禁覆盖双窗口、窄冻结 bridge 与 Node 隔离、managed/online/authenticated/errorCode=null、daily_finance 与 daily_finance.assistant@1、毛毛 idle/openMain、recover 恰好一次且状态一致、隐私/日志/Windows 事件、虚拟 owner/db、源码/dist/resources/out/fuses 不变、自然退出和自有资源关闭。console/page/crash 与相关 Windows 事件为 0；2 个已识别自有 Python（启动/recover）均退出。0 remaining owned processes/listeners/windows，无 timeout/forced cleanup。tray 零残留是由产品拥有的进程树消失推断，不冒充 OS tray 单独枚举或完整设备验收。

外部时间以原始 JSON 为准：package `2026-10-02T16:55:28.478+08:00–16:55:36.049+08:00`；EXE `17:20:24.275+08:00–17:20:59.110+08:00`。中间工具调用中断的未连续观测时段为 unverified，恢复后重新读 control 并查看落盘状态；中断调用未执行更正，未重复目标，不修改系统时钟。

## 全部失败、警告与收口

保留首次两项产品红灯、前目标工具文件名笔误以及只读搜索路径 miss。新包静态已通过后，bundle 补证脚本因命令 JS 字符串转义先丢失反斜杠导致语法失败；首次定向只修路径表达式后，syntax check 又发现换行转义错误，未运行读取主体。初始和中间脚本都保留；完整 raw string 更正的调用被中断未落盘，随后一次 functions 编排解析失败也没有执行命令；恢复用正确原始字符串完整更正，syntax check 与实际绑定均通过。全部属于证据编排，不改变产品/包，不增加 package/EXE 预算，不隐藏失败；inputs/failures-warnings.json 和 static/binding-initial-failure.json 可查。

只读 Git 报全局 ignore 读取权限、LF→CRLF 提示；不改变配置，staged=0，diff --check 无内容错误。依赖来源/冻结不变，package stderr 0 bytes。EXE 预期 DevTools 标识及原始 profile/日志只受限留在外部现场，不进入仓库或脱敏 evidence manifest。没有用户参与要求、真实消息、账户/密钥或真实财务数据。

前后旧 R3 source323/冻结deps12443/实际deps12677/dist73/out140/evidence52/profile62 全部逐字节一致，目录清点无增加；old-r3-full-node-modules.sha256 12677 项总摘要 `035c05bffbbf5f297ac098e7fbda16d5bd48cf76a89e4036c3dc35ddb64b3ef8`。新352构建输入、deps/dist、out140与resources67收口复算均通过，见 inputs/final-immutable-audit.json。旧 R2/LOCALZIP 无写操作；它们没有被当本轮产品/profile现场。

资源关闭后仅删除绝对路径精确核对且无 reparse 的新根 evidence/tests/tmp，保留全部产物、虚拟 profile 和证据。resource-closeout.json 新核对自有进程 0、tmp 不存在、profile 保留、forcedCleanup=false。没有按全局进程名停止程序，没有启动 Docker/PG/OpenClaw/微信/DeepSeek/provider。

## 固定交付与停止

本轮精确 5 文件：修改 registry.ts、registry.test.ts、executor.md；新增本说明与 apps/desktop/b7-r4-route-source.sha256。352 起点中 349 unchanged、3 authorized changed，0 missing/越界；全部独立首次失败/通过材料和报告/矩阵保持字节一致。既有 .claude/.pnpm-store 未修改，Git 只读。

最终 source 清单 353 项，起点 352 更新获准摘要并加入本说明，排除清单自身，UTF-8 无 BOM、ordinal 路径排序、repo-relative-path<TAB>lowercase-SHA256<LF>。逐行重算文件内容 SHA，再对清单原始字节算 SHA-256 即可复算。角色最后停止修改后生成；为避免自引用，总摘要放外部 closeout.json 和最终交付消息。

外部 repository-delivery.sha256 精确 5 文件（包含 source 清单自身）；脱敏 evidence-manifest.sha256 排除自身/closeout、raw/profile/os-env/logs、tests/tmp/cache；准确数量与摘要见 closeout。控制和其他角色只读，未发起独立复验、未创建 C12-R3/P4-C。PATH-001 独立关闭、完整 UI-04 和剩余 Windows 验收等待总控/测试方，执行方停在 review / finished。
