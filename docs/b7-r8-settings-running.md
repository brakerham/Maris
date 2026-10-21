# P4-B7-R8-SETTINGS 执行交付与停止记录

本轮状态为 **blocked / finished**。窄设置读取与启动水合已经实现，执行方开发回归通过；唯一新包及静态绑定通过。正式 S1 在启动后的原生进程身份观察阶段受阻，尚未取得真实页面样本，S2 未运行。不能以开发测试、后台进程出现或当前资源清零代替两次真实生命周期通过。

依据为 [R8 任务卡](coordination/prompts/p4-b7-r8-settings-executor.md)、[SETTINGS-R8 补充合同](p4-c12-r9-r3-settings-coordinator-review.md) 和 `2026-10-19T07:58:21+08:00` 版 control。SETTINGS-001、CMP-06、LAZY-001/UI-02、P4-B 的最终结论仍由后续独立复验和总控决定。本轮未运行独立测试、旧 EXE、H1/W1、独立模块、冷入口 B 或旧恢复集合，未启动测试方、顾问或后续任务。

本文时间采用 Asia/Shanghai；原始 JSON 的 `Z` 时间为 UTC。外部任务根为 `C:/MarisSettingsR8/R8-20261019-103900`，以下 `R/` 均指此根。

## 1. 起点、边界和最小修复

起点 `docs/coordination/snapshots/p4-b7-r8-settings-start.sha256` 为 1,363 项，原字节 SHA-256：

`c20d449109248327b68a09427c785bda9af79990eafd93c271bb99b6435c2de3`

已核验 UTF-8 无 BOM、LF、唯一排序、两列 `path<TAB>sha256<LF>`、排除自身、1,363/1,363 匹配及暂存区为空。接单与续接记录见 [执行方状态](coordination/agents/executor.md)；外部复核回执为 `R/evidence/inputs/start-gate.json`。

原实现虽然把 theme/privacy 保存到 main 的设备设置，DesktopApp 启动时却直接使用 `system/false`，没有读取已加载设置。修复保留既有存储和写接口，增加：

1. main 使用既有 `registerMainHandler` 注册 `settings:get-snapshot@1`，每次从当前内存设置返回仅有 theme、reducedMotion、privacyMode 的新对象。
2. IPC 合同限定零参数，保留已有 sender、主 frame 和 origin 校验；preload 仅开放 `settings.getSnapshot()`。
3. shared 定义严格三字段 schema。renderer 在一次挂载读取后校验并恢复 theme/privacy；读取未成功前不显示业务内容或设置控件，拒绝或非法回包显示安全错误态，不写默认值、不自动重试。
4. effect 清理使卸载/过期回包失效。模块就绪与设置就绪分别管理，合法空模块集合不等于设置失败；相同模块通知、recover 和正常用户设置不重新水合、不重建相同路由、不隐式重试 lazy。

未新增持久字段、迁移或 reducedMotion 视觉行为，未改 device-settings、Shell/CSS、composition、Host、outbox、registry、supervisor、依赖、lock、Forge 或 staging。

实际仓库交付严格为以下 **12 路径**：

| 路径 | 变化 |
| --- | --- |
| `apps/desktop/electron/main/index.ts` | 只读 getter 注册及类型导入 |
| `apps/desktop/electron/main/ipc-contract.ts` | 零参数固定 channel |
| `apps/desktop/electron/preload/index.ts` | 窄 getter |
| `apps/desktop/src/shared/contracts.ts` | 三字段类型/schema/bridge |
| `apps/desktop/src/renderer/module-routes.tsx` | 启动水合、安全加载/失败态 |
| `apps/desktop/tests/unit/module-readiness.test.tsx` | 仅两处 mock 补 getter |
| `apps/desktop/tests/unit/lazy-isolation.test.tsx` | 仅一处 mock 补 getter |
| `apps/desktop/tests/unit/settings-hydration.test.tsx` | 新增 27 项执行方覆盖 |
| `apps/desktop/tests/unit/settings-snapshot.test.ts` | 新增 21 项执行方覆盖 |
| `docs/b7-r8-settings-running.md` | 本说明 |
| `apps/desktop/b7-r8-settings-source.sha256` | 终点清单 |
| `docs/coordination/agents/executor.md` | 本人状态、里程碑与交接 |

两个旧测试文件没有修改业务断言。原有 `.claude/`、`.pnpm-store/` 不在本轮修改范围，也未清理。未执行任何 Git 写操作。

## 2. 首次红灯与执行方开发验证

原产品红灯实际挂载 DesktopApp、Router、Shell；虚拟 bridge 提供 dark/true，但首个页面观察为：

| 观察 | 实际 |
| --- | --- |
| Shell / daily 已挂载 | true / true |
| 页面 theme / privacy | system / off |
| 主题控件 / 隐私控件 | system / false |
| getter / settings write 调用 | 0 / 0 |

首次结果为 0 passed、1 failed、0 skipped，真实退出码 1；不是 TypeError 或未加载环境。源码、JSON、观察和退出回执分别保存于 `R/evidence/inputs/red-settings-hydration.test.tsx`、`R/evidence/tests/red.json`、`red-observations.jsonl`、`red-exit.json`，没有覆盖为绿灯。

修复后的结果：

| 验证组 | 时间 | 结果 |
| --- | --- | --- |
| 新 hydration | 包含于定向及 full | 27 passed |
| 新 snapshot/IPC/preload/main | 包含于定向及 full | 21 passed |
| 定向邻接 | 10-19 15:36:50–15:36:54 | 8 文件，99 passed / 0 failed / 0 skipped，exit 0 |
| TypeScript | 10-19 15:36:54–15:36:56 | exit 0 |
| lint | 10-19 15:36:56 | exit 0 |
| 唯一完整 desktop 回归 | 10-19 15:37:21–15:37:25 | 19 文件，217 passed / 0 failed / 0 skipped，exit 0 |

原 17 文件 169 项保留；新增 48 项，合计 217 唯一节点。定向与完整运行不重复累计。日志未发现开发 warning，四组 stderr 均为空；红灯是刻意保留的修复前失败。各组完整参数、起止时间、signal、实际退出码和受验源码清单见 `R/evidence/tests/*-exit.json`、`*-source.sha256`、`*.json` 和 stdout/stderr。

完整 19 文件节点数为：composition-root 1、electron-zip 14、host-client 3、ipc 3、lazy-isolation 8、main-quit 19、module-readiness 18、outbox-retention 14、owner-session 1、package-resources 14、registry 52、security 3、settings-hydration 27、settings-secure 2、settings-snapshot 21、shell 1、supervisor-outbox 13、toolchain 2、window-lifecycle 1。精确文件名与断言以 `full.json` 为准。

新测试使用实际 main/preload/validateIpc 和实际 DesktopApp/Router/Shell，替换 Electron、存储、Host 等外部边界。覆盖合法主题及隐私恢复、三字段投影和新对象、update 后读取、延迟/拒绝/非法/额外字段、无默认保存、StrictMode、卸载与过期回包、相同模块通知/recover 保持选择、无额外路由加载/隐式 retry、身份权限及无额外副作用。此处均为执行方自测，不属于独立验收。

## 3. 固定普通环境与唯一新包

只读来源 `C:/MarisQuitR7/R7-20261014-191500`，新任务根普通复制，不使用 reparse/junction。固定版本为 Node 24.21.0、pnpm 12.7.0、Electron 44.4.5、Playwright 1.63.0、Python 3.14.7；Python 使用仓库已有 `.venv/Scripts/python.exe`。

- lock：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- 官方 LOCALZIP：158,184,819 bytes，`11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- 实际 Forge 使用本任务 tools/node、forge-pnpm-bin、已有 LOCALZIP；回执 `actual-forge-env.jsonl`。
- 没有下载、安装、换版本、永久 PATH、代理或安全软件修改。

冻结构建 source **1,365 项**（起点加两新测试），清单 `R/evidence/static/workspace-source.sha256`：

`c880730b84d726dec41e077867e44e942855ba60790e3a0ddb38940b89efd1d4`

只执行一次 package：10-20 00:09:53.816–00:10:02.159，8,343 ms，exit 0、signal null、stderr 0。`package-started.json` 与 `package-result.json` 保留；未重复打包。

原 7 静态门禁全部通过：out 140 文件、386,496,773 bytes；Python 资源 67；asar 实体文件 11、列表项 18、link/unpacked 均 0；production fuses 前六项 48/49/48/48/49/49；污染命中 0、staging/transition 残留 0。见 `R/evidence/static/result-v4.json` 和三份 TSV 清单。

| 产物 | 字节数 | SHA-256 |
| --- | ---: | --- |
| 新 Maris.exe | 246032896 | `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b` |
| 新 app.asar | 763591 | `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2` |
| asar main.js | 120524 | `cb4a633125acd1c690ccf18827373555755bc45fb50c5a4bb4a8deee11d228ce` |
| asar preload.js | 741 | `857e28033aff741f13600df78f998659a15631eadc1c7a414910f8ab49371e84` |
| asar main renderer JS | 411614 | `cf52d756c95af4317e76ddb0d20850c63286a70b8cf7379ca525747a31a721a1` |

新读取链的 8 项静态绑定通过，6 个实际 archive JS 与本次 Vite 输出逐字节一致；main channel/投影、preload getter、renderer getter/加载态/失败态/schema 均有定位。见 `settings-chain-binding.json`。这是代码入包来源证据，不替代动态行为。

## 4. S1 首次失败、S2 停止及资源状态

启动前 driver 语法、native AST/C# 声明、参数、清单、路径和安全边界共 21 项静态检查通过，见 `final-driver-freeze.json`。静态检查未覆盖下面实际运行中的日期对象二次解析缺口，不能因静态通过否定正式失败。

冻结的 driver 与窗口工具：

- `settings-exe-runner.mjs`：`f78ab28dffdad2a9decde29ba34328d11ae27ed42149e78b3cdd520d7281a7b0`。
- `normal-close.ps1`：`e5224103c28c05ea7ba859ada029ccf421f249908d7350f7179eda2aeaa86745`。

S1 于 10-20 00:18:36.935 直接 spawn 新 EXE，shell=false；没有 MARIS_E2E_EXIT_MS。只 seed 本轮新虚拟 profile：light、privacy=false、quit、closeHintShown=false、companionVisible=true。五项 seed 比较通过，不能算真实页面门禁。

原始根进程身份观察曾匹配直接 spawn PID、路径、父进程、创建时间和 marker。8,328 ms 后首个原生窗口观察失败：

`normal-close.ps1:57 → known_identity_unknown`

首次记录在 `R/evidence/settings-exe-S1/raw/driver-events.jsonl`、`native-1-stderr.log` 和原始 `result.json`。随后同一工具的 cleanup、final-window-observe 也因相同谓词失败；原始结果的资源字段保持 null/unknown，没有填 0。

后续只做数据转换核查，没有修改冻结驱动或再次启动。`ConvertFrom-Json` 已把 `created` 转为 `System.DateTime`，再传给 `[DateTimeOffset]::Parse($k.created)` 会重新字符串化并丢失时区/小数秒。使用同一 PowerShell 7.6.5 对原始值的纯转换证据：

- typed UTC：`2026-10-19T16:18:36.9569120Z`，ticks `639280235169569120`。
- 二次 Parse UTC：`2026-10-19T08:18:36.0000000Z`，ticks `639279947160000000`。

见 `R/evidence/inputs/date-conversion-only.json`。这足以解释 known 身份比较的工具缺口；没有证据将它归为产品设置恢复失败。目标开始后的原稿不修、不重跑，S2 保持 not_run。

| 层次/节点 | 本轮实际结果 |
| --- | --- |
| S1 新 EXE 直接启动、登记根身份 | 已发生并有回执 |
| seed 文件与五项初始值比较 | passed；只代表输入 |
| 后台 online/authenticated、canonical daily | 未取到正式断言，unverified |
| 真实页面 Shell/daily/导航/Agent、双窗口/bridge 安全 | 未完成取样，not_run |
| 真实 UI 保存 dark/true | not_run，driver 设置写操作 0 |
| 一次 recover 与页面/设置保持 | not_run |
| S1 正常 WM_CLOSE/10 秒内自然 exit 0 | not_run；normalClose=null，exit=null |
| S2 同 profile 首次恢复样本 | not_run；没有启动、没有 seed 或补写 |
| 当场资源清理 | 工具受阻，原始 result 为 unknown |
| 09:12、22:34 当前资源只读复核 | 自有进程 0、监听 0、窗口 0；查询成功 |
| 中断期间真实退出原因/时间/root 及子进程退出码 | unknown，不能追补自然退出通过 |

S1 seed 文件及原始失败收尾样本均为 414 bytes，light/false 等六个安全值保持，SHA-256 `845e69b33c0a5c9abd5696f058aed9a2f00954a23558029bb18e869db21752f5`。没有“保存后的 dark/true 文件”，也没有 S2 四值首样。`settingsWriteOperations=0` 仅表示 driver 未调用真实设置操作，不是产品内部 IPC 计数器。

00:18 原始结果的 `timedOut=false` 只表示观察代码在约 15 秒内写出失败；此后控制进程仍受子进程影响，不能宣称产品满足 120 秒退出硬上限。原控制会话 42927 后续不可恢复，外层退出回执没有生成；缺失事实保留。

失败后首次补充查询还观察到 8 个登记 PID；进一步核查因自动审批额度不足未执行。用户继续后 09:12 与 22:34 的成功只读查询确认这些 PID 和任务路径下资源已不在，未实施额外终止操作。当前零资源回执分别为 `postfailure-final-resources.json` 与 `closeout-resources.json`。它们与当场失败记录并存，不覆盖原始 unknown。

## 5. 所有失败、警告和执行中断

1. 修复前真实组件红灯 1 failed，已完整保留。
2. 首次普通物化读取清单使用系统 GBK 造成 UnicodeDecodeError；保留 `materialization-first-error.json`，明确 UTF-8 后完成。另有旧证据目录层级/Windows wildcard 的只读定位错误，没有改旧文件或运行产品。
3. driver 草案生成时模板变量 `port` 的 ReferenceError 发生在目标调用前；首次草稿、复核修正记录均保留。
4. 同一包首次 chain-binding 因 asar 路径分隔符导致 statFile not found，保留首稿及错误；仅改工具为原验证器采用的 native 分隔符后 8 项通过，没有第二次 package。
5. 目标前两轮有限工具检查处理空查询、未知身份、原生枚举失败、最终观察失败回执、bridge 键集与 spawn 监听；21 静态检查通过仍未防住 S1 日期对象转换错误。正式失败后未修后重试。
6. S1 的 launch/cleanup/final-window-observe 均抛 `known_identity_unknown`；root 实际退出码未取得，S1 blocked、S2 not_run。
7. 原生 electron.log 有一条 `ERROR GetGpuDriverOverlayInfo: Failed to retrieve video device`，127 bytes。保留原记录，不猜测与身份检查错误的因果。stderr 100 bytes 含本次 CDP 身份，仅外部保存；stdout 2 bytes。没有完成 renderer console/pageerror/crash 或系统事件门禁，不能把它们填为 0。
8. 补充查询首次在沙箱内 Get-CimInstance 被拒绝；输出中的 false 不当作进程不存在。获准沙箱外只读查询随后得到有效结果。
9. 多次自动审批/辅助模型额度耗尽中断。被拒绝的操作明确未执行，没有通过其他入口绕过；时间空档不计持续工作。最后的内部只读辅助也未能产出结论，由父执行完成纯转换核查。没有把辅助额度失败计作产品失败。
10. Git 只读有用户 ignore 文件权限和 LF→CRLF 提示；不改变原字节快照，未执行暂存、提交、还原、重置、切换或推送。
11. 首次终点生成器已写 source/delivery，随后把沙箱内外的 `.claude/` 可见性差异误判为范围失败。原始生成器、候选清单和 exit 1 已保存为 `first-closeout-*`。只读核实：沙箱拒读全局 ignore 时出现 `.claude/`，获准环境遵守原忽略规则则不出现；12 个交付路径均在。仅把收口判断改为必须包含全部 12 交付、额外仅允许两个原有未跟踪根，原字节非授权路径门禁不变。没有产品/测试/driver 重跑。

开发最终无 failed/skip/warning；唯一 package exit 0；上述历史红灯、工具失败、动态阻塞、日志 ERROR 与未取证项全部保留，不以总数掩盖。

## 6. 不变性、清理与可复算交付

`R/evidence/inputs/final-audit.json` 在 10-20 09:12 开始的只读审计中确认：

| 旧来源范围 | 文件数 | 清单 SHA-256 |
| --- | ---: | --- |
| R7 构建 source | 932 | `e7cec440e4420bec3f6fec274b6521ecd413d0d4c4fc1f304a584823ea9732a0` |
| R7 out | 140 | `1953b0f91d94b4d64850d4d81c5da8c803bb1da5eebda6bf32eda64935214521` |
| R7 Python resources | 67 | `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |
| R7 Electron dist | 73 | `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| R7 完整依赖 | 12677 | `035c05bffbbf5f297ac098e7fbda16d5bd48cf76a89e4036c3dc35ddb64b3ef8` |
| R7 执行证据 | 157 | `63a94a2177dbe0107f1c9ea327d9d26b694137a91824d2733ad038aaf9d99615` |
| R9 外部现场 | 83 | `39934224bccb0eb0352740769a87e5f2404b9de71ae1b7dd1961e0c1a2fff0fc` |
| R9-R1 外部现场 | 72 | `9c5aa9f976f8d7e5d7f4f0c6aeb565c3908df987d27c55ce845f88b816d949f7` |
| R9-R2 外部现场 | 103 | `90031e854006d379ebc62d44f5a5e8b17d2cf952ba4ae33b446d20c4ee5497ed` |
| R9-R3 外部现场 | 114 | `b4beb3c1022f16aa6390618bc5f35ea754db7e22b8de0f6d61c27140f8fbb29a` |

以上全部逐项匹配；out/resources/dist/dependencies 和四个 R9 现场还核对完整路径集合。新 1,365 构建 source、12,677 依赖、73 dist 及开发输入同样匹配。最终交付生成器另核对新包 140 项、67 资源和冻结驱动，并再次审计仓库非授权路径。

22:34 在核实绝对边界、全部祖先/子项无 reparse 后，仅清理新 tests/tmp 的 88 个临时文件与 12 个子目录，以及两个虚拟污染标记文件。回执 `temp-cleanup-before.json`、`temp-cleanup-result.json`。新 package、完整原始证据、新虚拟 profile/数据库全部保留；未读取真实密钥/个人数据，未复制/解密旧 owner/profile，未操作 Docker/OpenClaw/微信/真实 provider。

终点 [source 清单](../apps/desktop/b7-r8-settings-source.sha256) 为 **1,366 项**：1,363 起点更新授权摘要，加两新测试和本报告，排除该清单自身。12 路径交付逐文件摘要、source 总摘要和所有外部清单总摘要统一写入 `R/evidence/closeout.json` 及 `R/evidence/delivery-twelve.sha256`，避免报告或角色日志自引用自己的摘要。

清单按原始文件 bytes 计算 SHA-256，使用唯一 ordinal 路径排序、UTF-8 无 BOM/LF；两列 source/delivery 为 `path<TAB>sha256`，三列外部 inventory 为 `path<TAB>bytes<TAB>sha256`。验证时以对应 base 拼接相对路径、读取原字节比较每行最后一列，再对清单文件本身计算 SHA-256。base 与准确数量记录于 closeout.json；证据清单排除自身及后生成的 closeout.json，虚拟 profile 单独列清单，只读文件摘要而不解密内容。

## 7. 交接与停止

开发修复可以审阅，动态生命周期不能签通过。本轮预算最终为 package **1/1**、EXE **1/2**、safeStorage helper **0/0**、完整 desktop **1/1**。S1 首次失败已触发停止规则，剩余 EXE 配额不构成自行续跑授权。

执行智能体提交 12 路径、固定新包和完整失败证据后停止，状态 **blocked / finished**。需要总控评估工具日期身份比较及失败后独立收口通道，并另行明确后续有限验证权限；本轮没有修改冻结 driver、再打包、重启 S1/S2 或自行派发独立验收。当前资源零残留不改变动态阻塞结论。
