# P4-B7-R3-REGISTRY 执行方运行与交付说明

状态：`review / finished`。本轮完成 `P4-C12-R1-REGISTRY-001` 指定的设置键全局冲突返修、执行方自测、新 package 和真实 EXE 冒烟；停止执行，交总控核对新稳定快照。没有宣告独立缺陷关闭或 P4-B complete，没有启动 C12-R2、测试智能体、技术顾问或 P4-C。

## 起点和范围

按 AGENTS 读取 README、project-coordination、coordination/README、control、executor 和 R3 任务卡；读取 C12-R1 总控核对及独立首次失败报告、IF-003 §5、IF-004/005、registry 实现/执行方测试及 R2 运行说明。外部复制、预检、package、EXE、资源收口前重读 control，版本始终为 `2026-10-02T11:05:00+08:00`。

R3 固定起点 [p4-b7-r3-registry-start.sha256](D:/CodeX_gap/wife-system/docs/coordination/snapshots/p4-b7-r3-registry-start.sha256) **323/323 matched、0 missing、0 mismatch**；清单 SHA-256：`bdae626369a75718e7010b336b35fbfb260eaf89e52dc4d998c45ce19cc2ccec`。暂存为 0。使用新起点；旧 R2 起点没有重跑或更新，旧外部 manifest 只用于旧树不变性核验。

本轮精确交付 **5 文件**：

| 文件 | 变化 |
| --- | --- |
| `apps/desktop/src/modules/registry.ts` | 修改：仅一行 setting 冲突键 |
| `apps/desktop/tests/unit/registry.test.ts` | 修改：保留原 18 项断言，新增 8 项开发回归 |
| `docs/b7-r3-registry-running.md` | 新增：本说明 |
| `apps/desktop/b7-r3-registry-source.sha256` | 新增：有序 source 清单，排除自身 |
| `docs/coordination/agents/executor.md` | 修改：接单、心跳、检查点和最终交接 |

最终起点 **320 文件精确不变、3 文件授权修改**；另有 2 个新增文件。最终 source 清单 **324 项**，由起点 323 路径更新获准摘要、加入本说明、排除清单自身构成。outbox/main/preload/IPC、contribution、Python/Host/migration、依赖/lock、Forge/build/staging/helpers、独立测试/证据/报告/矩阵、冻结/control/overview 和其他角色日志均不变。Git 只读，未暂存、提交、切换或还原；原有 `.claude/` 与 `.pnpm-store/` 保持不动。

## 根因和最小修复

IF-003 §5 冻结 setting 全局唯一和任一冲突整体拒绝。C12-R1 的 R1-SHELL-13 已证明跨模块同名键得到两个不同 seen 值而被接受；本轮只读利用该独立首次失败，没有运行独立节点。

[registry.ts:40](D:/CodeX_gap/wife-system/apps/desktop/src/modules/registry.ts:40) 将查重键从 `setting:${item.moduleId}:${setting.key}` 改为 `setting:${setting.key}`。同一次 `compileRegistry()` 内，跨模块、同模块、同/异 schemaVersion 的同名键均抛出既有 `desktop_registry_conflict`，不会返回部分 registry。交换贡献顺序同样拒绝。

没有自动加前缀、重命名、选赢家或降为告警；没有改解析 schema、route path、错误合同、返回类型或其他身份校验。seen 仍为每次调用的局部集合，失败不会污染后续合法编译；输入仍不修改。`daily_finance.preferences`、`daily_finance.assistant@1` 和 Host intersection 保持原合同，没有新增真实第二业务模块。

[registry.test.ts:87](D:/CodeX_gap/wife-system/apps/desktop/tests/unit/registry.test.ts:87) 开始的 8 项新增测试为：4 项跨模块同键（两顺序×schemaVersion 1/2）、2 项同模块同键（schemaVersion 1/2）、1 项不同键合法编译及 daily_finance/Host intersection、1 项失败输入不变且随后合法编译成功。原 canonical Profile 长度/语法、严格解析、module/Profile/route ID/appearance 冲突断言保持。

| 两个授权源码 | SHA-256 |
| --- | --- |
| `apps/desktop/src/modules/registry.ts` | `881a73855476a3f23f388c9def056bad789833ed324050154af4b2bda459ac97` |
| `apps/desktop/tests/unit/registry.test.ts` | `ec358226be967fb9d447de250e87272d95f6a00e1323321eccd25224458f3d1a` |

## 执行方测试与首次失败

证据根：`C:\MarisRegistryR3\R3-20261002-111556\evidence`。这些结果都是执行方开发验证，不是独立验收；没有运行 `tests/independent/**`、Python/P0～P3/Host 全量或旧 outbox 独立复验。

| 组 | 实际结果 | 原始证据 |
| --- | --- | --- |
| 修复前执行方红灯，首次一次 | 4 个实际选中用例全部 failed，exit 1；旧实现不抛错误 | `tests/registry-before.log`、`registry-before.json`、`registry-before-exit.json` |
| 修复后 registry + shell + composition | 3 files、28 passed、0 failed/skip；registry 26 项 | `tests/directed-after.log/json` |
| TypeScript | exit 0、无诊断 | `tests/typecheck.log`、`development-gates.json` |
| lint | exit 0 | `tests/lint.log` |
| 唯一一次完整 desktop 开发回归 | 14 files、98 passed、0 failed/skip，1.86s | `tests/full-unit.log/json`、`full-unit-exit.json` |
| 固定工具与 Forge 实际 pnpm 调用 | Node 24.21.0，裸/resolve/spawn pnpm 12.7.0 | `inputs/bare-tool-resolution.json`、`forge-pnpm-resolution.json` |
| package | 唯一 1/1、exit 0、7.509s | `package-started.json`、`package-result.json`、stdout/stderr |
| 产物静态检查 | 7/7 全过，额外源码绑定证据通过 | `static/result-v4.json`、`registry-source-binding.json` |
| 真实 EXE | 唯一 1/1、19/19 全过、34.535s，自然 exit 0 | `final-exe/result.json`、`final-exe-driver.log` |

红灯命令使用 `-t` 仅选新增跨模块四项。Vitest 将其余 22 项显示为 skipped，实际是 filter 未选中，没有添加 skip/xfail，也未计作实际执行；修复后的定向和完整运行全部执行且 skip 为 0。完整 98 为原 90+新增 8 个唯一开发案例，不能再叠加 4 个红灯或 28 个定向节点声称额外唯一案例。

一项目标启动前编排错误已保留并使用一次修正：`Get-Command pnpm -CommandType Application` 返回 4 个候选，首项本来就是本轮固定 exe，但将整个数组与单路径比较误报 `bare_pnpm_resolution_failed`。当时没有 package/EXE 或 pnpm 命令启动；诊断后只改为取首个应用候选，再执行真实裸 pnpm 和 Forge `resolvePackageManager/spawnPackageManager --version`，结果全部为固定 12.7.0。分类为 `harness_probe_failure`，证据 `inputs/bare-resolution-initial-failure.json`；不是产品失败、安装失败或新增任务。package/EXE 没有追加预算或重跑。

其他警告：只读 Git 的全局 ignore 权限和 LF→CRLF 提示，未修改配置；只读探查旧 Forge 路径时一次找不到旧 `core/dist/util/package-manager.js`，随后通过文件搜索定位真实 `core-utils/dist/package-manager.js`，未运行错误模块或修改依赖。package stderr 0 bytes。EXE console/page/crash 及 Application/CodeIntegrity 事件均为 0；预期 loopback DevTools 标识只保留在外部受限 stderr，不进入产品 DOM/storage/bridge。

外部操作时间以原始 JSON 为准：package 为 `2026-10-02T11:31:48.048+08:00–11:31:55.557+08:00`；EXE 为 `14:40:28.226+08:00–14:41:02.761+08:00`。工具控制返回后的收口按当时实际时间记录；两者之间未连续观测的外部状态为 unverified，不推断整段持续运行。本轮没有修改系统时钟。

## 普通副本与旧 R2 不变性

工具/普通依赖来源仅为 `C:\MarisOutboxR2\R2-20261001-155509`；新专属根 `C:\MarisRegistryR3\R3-20261002-111556` 创建前验证绝对边界且 create-new。物化复制 R3 清单 323 源文件、R2 普通 node_modules 和 3 个固定工具文件；没有 Junction/symlink/reparse，没有安装、联网、换版本、修改系统/用户 PATH 或 pnpm。修复后只同步两个获准源码，其他副本输入冻结。

普通依赖的完整物理复制 **12677/12677 精确匹配、0 差异**。其中第三方冻结清单 **12443/12443 matched**；其余 234 项均在 `@maris/desktop` 的已存在物化 workspace 包，未当作新第三方版本。应用构建由新 `workspace/apps/desktop` helper/Forge/Vite 输入驱动，未把该附加包当修复源码；新 asar 的 main 与 renderer 实际全局 setting token 证明绑定新源。

旧完整 node_modules 12677 项另外冻结 `inputs/old-r2-full-node-modules.sha256`，SHA-256 `035c05bffbbf5f297ac098e7fbda16d5bd48cf76a89e4036c3dc35ddb64b3ef8`，用于交付后精确复算所有旧普通文件。旧 R2 source271、冻结依赖12443、dist73、out140、脱敏 evidence38、虚拟 profile62 在前置和最终收口均匹配；旧产物、profile、原始失败与独立材料不更新、不删除、不复用。

| 固定输入 | 条目/大小 | SHA-256 |
| --- | --- | --- |
| 新构建 workspace-source.sha256 | 323 | `d0e732a6d7ffbdc5044fee6d8e63b3a3c92a6eb0a5259773730e6a03b240549c` |
| node-modules-final.sha256 | 12443 | `15f5613ce7744083a81c05c68ab06e06b6aa0b6e30f0c9c98ed933d87899e04c` |
| electron-dist-final.sha256 | 73 | `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| pnpm-lock.yaml | 固定 | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| 官方 electron-v44.4.5-win32-x64.zip | 158184819 bytes | `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |

ZIP 只读使用原 `C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\cache\electron\bfa62fe1b54e5e709b522b5f731c7644136b8ab3a8123f8d2facc4ecf2b925fe` 普通目录，现有校验接线未改。真实 Forge `electronZipDir` 一致且 `download` 配置缺席。没有重新 audit/install/download 或网络/代理/安全配置变更。

PATH 仅本任务子进程使用新根 `tools/node`、`tools/forge-pnpm-bin` 前缀。裸 pnpm 首项和 Forge 真实版本调用均核验；package helper 固定 Node 直接 spawn 新根 Forge CLI，`actual-forge-env.jsonl` 记录实际 execPath、argv1、PATH 首两项和 ZIP，未使用复制 `.bin` shim。Electron 44.4.5、Playwright 1.63.0、Python 3.14.7 保持冻结。

## 新产物和真实 EXE

新包根：`C:\MarisRegistryR3\R3-20261002-111556\workspace\apps\desktop\out\Maris-win32-x64`。

| 产物 | 精确大小/数量 | SHA-256 |
| --- | --- | --- |
| Maris.exe | 246032896 bytes | `1df694c0ca39818d1b2af7aad09eefa13383af186a8d0638d96a13882d604a94` |
| resources/app.asar | 759792 bytes | `64f84ddde164c4dea81ab3fcb6933728eda5acf3cfe4917828fe0f4f6dc3e161` |
| out-manifest-v4.tsv | 140 files、386492974 bytes | `6bc7042f47c1637deb58bdfe26550150cb80d77071eb9b9353d576b5d8ee8d34` |

静态 67 Python resources 精确一致、missing/extra/mismatch 为 0；asar 11 个文件、0 link/0 unpacked；production fuses v1 前六项 `48/49/48/48/49/49` 符合冻结，内容/路径污染 0，staging/过渡残留 0。v4 文件名是沿用检查器格式，本轮值来自新产物，不套旧 R2 摘要。

新 asar 摘要与旧 R2 不同。只读解包检查 `.vite/build/main.js` 和 `.vite/renderer/main_window/assets/index-BcK3CMeX.js`：两处都是 `setting:${s.key}`，没有 `moduleId` 前缀。`registry-source-binding.json` 同时记录授权 source SHA；业务行为由前述 26 项回归证明，bundle token 仅用于产物来源证据。

真实 EXE 由固定 Node `spawn(shell:false)` 启动新 Maris.exe；Playwright 仅附加随机 loopback CDP，不使用 `_electron.launch()`、app.asar loader 或 PID 提升。全新虚拟 profile/database/owner 为新根 `evidence/final-exe/profile`，不会加载旧状态。只用实际支持的 30000ms 原生退出参数、120s 硬上限；没有注入冲突真实模块、真实消息、老化弹窗或要求用户点击。

19 项门禁通过：direct ownership、动态 loopback CDP、Maris/毛毛双窗口、两侧窄冻结 bridge 与 Node 隔离、managed/online/authenticated 且 errorCode=null、daily_finance/canonical `daily_finance.assistant@1`、毛毛 idle/daily_finance/openMain、recover 恰好一次且恢复同等状态、隐私/日志/Windows 事件、虚拟 owner/database、源码/dist/resources/out/fuses 不变、自然退出与资源收口。没有用精确进程数量作门禁。

exit 0、signal=null，elapsed 34535ms，无 timeout/forced cleanup。2 个已识别自有 Python 子进程（start/recover）均退出；最终自有进程 **0**、监听 **0**、窗口 **0**。tray 零残留从拥有的产品进程树结束推断，不冒充单独 OS tray 枚举。仅删除绝对路径已验证且无链接的新根执行方 tests/tmp，保留产物/证据/虚拟 profile。没有按全局进程名停止其他程序，没有 Docker/PG/OpenClaw/微信/DeepSeek/provider 操作。

## 最终快照和停止

[b7-r3-registry-source.sha256](D:/CodeX_gap/wife-system/apps/desktop/b7-r3-registry-source.sha256) **324 项**，UTF-8 无 BOM，路径 ordinal 排序，每行 `repo-relative-path<TAB>lowercase-SHA256<LF>`。按每行重算内容 SHA，并对清单原始字节计算 SHA-256 即可复算总摘要。executor 最后停止修改后再生成清单，排除清单自身。为避免本说明/日志自引用，最终总摘要在外部 `evidence/closeout.json` 和最终交付消息提供。

外部 `repository-delivery.sha256` 精确列出 **5 个交付文件**及摘要，包含清单自身；`evidence-manifest.sha256` 冻结脱敏证据，排除自身/closeout 和 profile/os-env/raw/tests/tmp。虚拟数据库、owner session/blob、CDP 标识及原始 profile 不进入仓库。最终旧树、新源、新产物、全部起点其他文件和独立首次失败材料复算见 closeout。

真实原生老化提示、Tray/注销/主题等剩余 Windows 独立条件仍由测试方负责，本轮 unverified/not_run 不改为 passed；旧 OUTBOX-001 独立关闭以总控裁定为准，未再修改。REGISTRY-001 独立复验尚未派发，P4-B 未 complete。交总控核对固定 source/new package/EXE 后停止，不创建后续任务或角色。

最终只读汇总首次把 Python 资源基目录写成不存在的 resources/python，67 项报告 missing；实际包路径为 resources，静态与 EXE 已验证该 67 项。保留 closeout-initial.cjs / closeout-initial-failure.json，仅修正汇总路径，复用同一次已成功的旧树/新依赖字节复算结果并重查清单摘要；没有重跑任何目标。
