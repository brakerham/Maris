# P4-B7-R2-OUTBOX 执行方运行说明

交付状态：`review / finished`。本轮完成 C12 已报告的 `P4-C12-OUTBOX-001` 范围内返修、自测、新 package 和真实 EXE 冒烟；不作独立缺陷关闭或 P4-B complete 结论。总控和测试智能体后续独立派发；本执行任务停止。

## 输入与文件边界

读取最新 control `2026-10-01T15:37:09+08:00`，在 package、EXE 和资源收口前重新读取，指令未变化。已按 AGENTS 读取入门、角色日志、任务卡、IF-003 §10、IF-004/005、C12 首次失败报告和 LOCALZIP 交付依据。没有重新运行 C12 独立失败节点。

起点清单 [p4-b7-r2-outbox-start.sha256](/D:/CodeX_gap/wife-system/docs/coordination/snapshots/p4-b7-r2-outbox-start.sha256) 为 **290/290 matched、0 missing、0 mismatch**；清单 SHA-256：`7b9048400de42eab8c596e126939eff5d3809debbafce6dd80d08053418d2dcd`。接单前与交付时暂存均为 0。

本轮只交付以下 **8 文件**：

| 文件 | 性质 |
| --- | --- |
| `apps/desktop/electron/main/outbox.ts` | 修改：非 terminal 保留、串行持久化、限定确认集合 |
| `apps/desktop/electron/main/index.ts` | 修改：仅 retention import、原生 dialog 接线、窗口就绪和退出接线 |
| `apps/desktop/electron/main/outbox-retention.ts` | 新增：可注入原生 dialog 的窄控制器 |
| `apps/desktop/tests/unit/supervisor-outbox.test.ts` | 修改：保留原 3 项断言，新增 10 项执行方回归 |
| `apps/desktop/tests/unit/outbox-retention.test.ts` | 新增：10 项 adapter 和 4 项可执行 main 生命周期测试 |
| `docs/b7-r2-outbox-running.md` | 新增：本说明 |
| `apps/desktop/b7-r2-outbox-source.sha256` | 新增：最终有序逐文件快照，排除自身 |
| `docs/coordination/agents/executor.md` | 修改：接单、检查点、自测、运行及交接日志 |

起点中 **286 文件精确不变、4 文件授权修改**；另有 4 个授权新增文件，其中快照自身排除于快照内容，因此最终 source 清单 **293 项**。没有修改 renderer、preload、IPC/shared、Host/Python/migration、依赖、lock、Forge、构建/staging/helper、独立测试、报告/矩阵、control/overview 或其他角色日志。没有 Git 写操作；接单时已有 `.claude/` 与 `.pnpm-store/` 未跟踪目录保持不动。

## 缺陷原因与实现

原 `cleanup()` 使用 30 天创建时间过滤全部非 terminal，启动后的保存会把老 draft/queued 删除；C12 首次失败已经证明持久化 2→0。本轮不重复其独立测试，也不推断发生过真实用户数据丢失。

- [outbox.ts:33](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/outbox.ts:33)：自动清理只删除 `terminal` 且 `updatedAt` 严格超过 24 小时的条目；恰好 24 小时和所有非 terminal 均保留。load/start/shutdown 保留正文、digest、原 ID 和时间字段。
- [outbox.ts:39](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/outbox.ts:39)：候选仅为创建时间严格超过 30 天的 draft/queued；恰好 30 天不提示，sending 不进入集合。时钟仍可注入。
- [outbox.ts:42](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/outbox.ts:42)：确认绑定冻结条目的对象身份和当次候选数组；load/state 更新替换对象，包括同一时钟下同状态更新。确认时重新检查年龄和状态，只删除仍为原对象的已展示候选。重复确认不能扩大范围；新增、已变化、仍新鲜或 sending 条目保留。
- [outbox.ts:57](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/outbox.ts:57)：load、prepare、setState、cleanup、候选读取和确认删除共享串行队列；写加密文件成功后才发布新内存列表。失败保持旧内存和旧磁盘，队列尾部吸收拒绝但调用者仍收到错误，后续操作可恢复。没有改变存储格式、引入依赖或自动腾容量；20 条容量上限、重试/重启 ID 和 sending 后改文案的新 ID 语义保持。
- [outbox-retention.ts:17](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/outbox-retention.ts:17)：每启动最多安排一次，窗口 ready-to-show 后异步取候选。原生提示只传数量及固定安全说明，按钮为“保留 / 明确删除”，defaultId/cancelId 都为 0。保留、关闭、dialog rejection、窗口销毁和退出均不删除。捕获失败且不输出正文、ID 或原始错误。
- [index.ts:49](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/index.ts:49)、[index.ts:107](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/index.ts:107)、[index.ts:160](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/index.ts:160)、[index.ts:202](/D:/CodeX_gap/wife-system/apps/desktop/electron/main/index.ts:202)：注入现有 `dialog.showMessageBox`；窗口就绪接线与 shutdown/before-quit 停止接线。`composition.start()` 不等待确认。没有 renderer 删除 IPC，也没有新增财务 UI。

五个代码/测试文件的冻结摘要如下；其余交付逐文件摘要见最终清单。

| 文件 | SHA-256 |
| --- | --- |
| `electron/main/index.ts` | `d8ca205168a5961227fa131a03ddce80a9684571bc25c1947d2d6e7bf5ac0872` |
| `electron/main/outbox.ts` | `8dfe0b0b2f75450afcb578f14b51ec81b392988d63c5bd3f630eaf1ae4d4ab57` |
| `electron/main/outbox-retention.ts` | `6667a26d81d1521f574d8a39112911cd2c6e1010109ded8fa72993998236e18e` |
| `tests/unit/supervisor-outbox.test.ts` | `cacda0d28de3d45e8e146af0868de25cf1d15e752eeb83d58ce1f448dce6710a` |
| `tests/unit/outbox-retention.test.ts` | `c21e83630a9cd7bc144ff0705c339e9653fc93add29aed8321fdc4217a9ba3fd` |

## 执行方验证

所有测试为执行方开发责任，不是独立验收。没有运行或修改 `tests/independent/**`；没有运行 Python/P0～P3/Host 全量。

证据根：`C:\MarisOutboxR2\R2-20261001-155509\evidence`。

| 组 | 实际结果 | 证据 |
| --- | --- | --- |
| 定向 outbox/supervisor/retention/main | 2 files，27 passed，0 failed，0 skipped | `tests/directed-attempt-1.log` |
| TypeScript | exit 0，无诊断 | `tests/typecheck-attempt-1.log`、`tests/gates-attempt-1.json` |
| lint | exit 0 | `tests/lint.log` |
| 唯一一次完整 desktop 执行方单元回归 | 14 files，90 passed，0 failed，0 skipped，约 1.93s | `tests/full-unit.log`、`tests/full-unit.json`、`tests/full-unit-exit.json` |
| 脚本/Forge/依赖/lock 与文件边界 | scripts/Forge/lock 零差异，固定起点其余项不变 | `inputs/prepackage.json`、`closeout.json` |
| package | 1/1，exit 0，10.763s | `package-started.json`、`package-result.json`、stdout/stderr |
| 新产物静态检查 | 7/7 passed | `static/result-v4.json`、`static/reader.log` |
| 真实新 EXE | 1/1，19/19 passed，34.893s，自然退出 0 | `final-exe/result.json`、`final-exe-driver.log` |

定向覆盖：draft/queued/sending 在 30 天、30 天+1ms、远超期限经历 load→cleanup→模拟退出 cleanup→reload 保留；terminal 的 24h/+1ms；无老项不提示；最多一次、安全数量和默认保留；保留/关闭/rejection；明确删除后 reload；未决 dialog 下 prepare/setState；同钟状态更新与 reload 使旧确认失效；重复确认有界；并发容量拒绝；pending write 未发布；prepare/state/cleanup/delete 写失败不漂移，后续队列恢复；原密文/ID/容量和 sending 修改正文语义。4 项 main 测试真正导入 main、运行 whenReady 和事件，通过注入 Electron/Host ports 检查 Host startup 不等 dialog、就绪前退出、未决时退出/销毁和正常确认，未用源码字符串代替行为。

本轮唯一初始非预期失败发生在普通副本建立前：从 repo 运行固定 Vitest 无法解析 `vitest/config`，exit 1，**0 用例运行**。使用任务卡授权普通工作副本和其本地依赖后解决，无安装、无依赖变更；保留 `tests/initial-repo-config-error.txt`。之后定向、类型、lint、完整回归均首次通过；没有降低断言或增加 skip/xfail。

其他观察：只读 Git 输出全局 ignore 权限和 LF→CRLF 提示，未执行 Git 写入；package 观察工具有一次 stdout 会话关闭，已持久化结果证明 package 成功，未重复 package。package stderr 为 0 bytes。EXE console/page/crash 和 Application/CodeIntegrity 事件均为 0。EXE stderr 的 100 bytes 是预期 loopback DevTools 标识，仅留在专属运行证据；没有展示在产品 DOM、存储或 bridge 中。此前手工日志 16:09 检查点为计划标注，真实 EXE 的权威起止为 23:04:40.518–23:05:15.411（+08:00），以原始 JSON 时间为准；中间未连续监测的外部状态为 unverified，未推断持续运行。

## 普通环境、输入冻结与旧树不变性

新专属根为 `C:\MarisOutboxR2\R2-20261001-155509`，普通 workspace、固定 tools、证据和全新虚拟 profile 都在该根。复制前校验绝对目标范围、create-new 根，不用 junction/symlink，不修改旧树、系统/用户 PATH 或 pnpm。仅本任务子进程 PATH 首两项指向固定 Node 和 `forge-pnpm-bin`。

普通源副本 **271 项**，依赖 **12443/12443 matched**、0 reparse，工具 **3/3 matched**（Node、固定 standalone pnpm 和另一固定 pnpm exe）。没有信任复制的 `.bin` shim：构建 helper 固定 Node 直接 spawn 其解析的 Forge CLI；`actual-forge-env.jsonl` 记录真实 Forge 子进程 execPath、argv1、PATH 首两项和 ZIP 目录，均指向授权固定工具/输入。Node `24.21.0`、pnpm `12.7.0`、Python `3.14.7`；未安装、下载或配置网络。

| 输入 | 条目/长度 | SHA-256 |
| --- | --- | --- |
| 新 package workspace source manifest | 271 | `e6a3b393b9f08ff83f9c912f4ba1dbc72283247544fea06ce4fcc231afd94789` |
| node_modules 输入清单 | 12443 | `15f5613ce7744083a81c05c68ab06e06b6aa0b6e30f0c9c98ed933d87899e04c` |
| Electron dist 输入清单 | 73 | `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| pnpm-lock.yaml | 固定 | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| electron-v44.4.5-win32-x64.zip | 158184819 bytes | `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |

ZIP 只读使用旧根已接受普通目录 `cache\electron\bfa62fe1b54e5e709b522b5f731c7644136b8ab3a8123f8d2facc4ecf2b925fe`。现有 helper 核验长度/SHA，`real-forge-zip.log` 证明真实 Forge `electronZipDir` 正确且 `download` 配置缺席，没有修改 local ZIP helper 或 Forge。

旧 `C:\MarisE5Final\E5-PKG-FINAL-20260929-1732` 的 source269、node_modules12443、dist73、out140、LOCALZIP evidence115 在新打包前和交付时都逐文件核对，无变化；旧 evidence 清单 SHA：`8de482784b4506419d6eb5629176fca89ffe51be945287ba1b6272207bc310da`。旧 EXE/profile/out 不复用、不覆盖、不删除；不使用 E4/E5-R1/E5-R2 依赖。

## 新产物与真实 EXE

新包根：`C:\MarisOutboxR2\R2-20261001-155509\workspace\apps\desktop\out\Maris-win32-x64`。

| 产物/清单 | 精确数量或大小 | SHA-256 |
| --- | --- | --- |
| Maris.exe | 246032896 bytes | `8eb56f3f63b923471a9239e2a01f29a8111067a6093d8c9d118e62e1ccfb5c2a` |
| resources/app.asar | 759820 bytes | `74225ea63dbc7201dc7f7f3299a099ac573f51680ef705536e560a9d9df6b6c7` |
| out-manifest-v4.tsv | 140 files / 386493002 bytes | `283e308769ea2a77d08ca0e75d562c9e9a56f60f149c4c7e3c35c3b828d0eb23` |
| python-resources-v4.tsv | 67，missing/extra/mismatch 均 0 | `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |

静态 asar 11 个文件、0 link、0 unpacked，67 个 Python resources 精确匹配；production fuses v1 前六项 `48/49/48/48/49/49` 与冻结配置一致；路径/内容污染 0，staging/过渡文件 0。v4 文件名沿用已接受只读检查器输出格式，内容为本轮新产物，未套用旧摘要。

动态由固定 Node `spawn(shell:false)` 直接运行新 Maris.exe；Playwright 只通过随机 loopback CDP 附加，不用 `_electron.launch()` 或 app.asar loader。全新虚拟 profile 为 `evidence\final-exe\profile`，指定已验证 Python，30 秒原生退出、120 秒硬上限。2 个窗口分别为 Maris/毛毛；两侧无 Node primitives、bridge 冻结且键集合符合合同；Host 为 managed/online/authenticated、errorCode=null；仅 daily_finance 且 Profile 为 `daily_finance.assistant@1`；毛毛 idle/daily_finance/openMain 正常；recover 恰好一次并恢复同等状态；隐私检查通过。随机会话、虚拟 owner/db 仅保留在外部专属根，不进入仓库。

所有输入、EXE/asar/resources/out 和 fuses 在启动后复算不变。exit 0、signal=null，无 timeout、无 forced cleanup，自有产品进程 **0**、监听 **0**、窗口 **0**；tray 零残留从产品进程树已结束推断，不冒充单独 OS tray 枚举。记录了本轮 2 个自有 Python 子进程（首次 start 与一次 recover），最终均退出。仅移除经过绝对路径边界校验的执行方 tests/tmp，保留新证据/profile 和旧树；没有 Docker/volume/prune 或其他服务操作。

用户在本轮反馈“有弹窗 是正常的”，记录为用户对可见窗口的观察，与双窗口冒烟一致；不作为真实老化删除确认或独立验收证据。

## 快照复算与交接

最终 [b7-r2-outbox-source.sha256](/D:/CodeX_gap/wife-system/apps/desktop/b7-r2-outbox-source.sha256) 含 **293 项**，每行 `repo-relative-path<TAB>lowercase-sha256<LF>`，按路径 ordinal 排序，UTF-8 无 BOM；排除自身，包含本说明与最终执行日志。逐项重算文件 SHA-256 可验证内容，总摘要为该清单文件原始字节的 SHA-256。为避免文档/日志/清单互相自引用，总摘要和所有 **8 文件**逐文件交付清单存于外部 `evidence\closeout.json`、`evidence\repository-delivery.sha256`，并在执行方最终交付消息中提供；正文不内嵌自身最终摘要。

外部 `evidence-manifest.sha256` 保留脱敏证据逐文件摘要，排除自身及 closeout 以避免循环，排除 profile/os-env/raw 和 tests/tmp。外部 profile、数据库、session、CDP 原始标识不复制入仓库。

真实 Windows 过期草稿原生提示的设备级独立证据仍为 **unverified**：本轮通过注入原生 adapter 与可执行 main 测试证明行为，没有载入真实草稿或要求用户点删除。没有启动 C12-R1、测试智能体、技术顾问、高保真前端、Docker、OpenClaw、微信、DeepSeek 或真实 provider。总控接手此固定 source/new package/EXE 输入后安排新 C12 快照及独立复验；本执行任务停在 review，未改总控或其他角色状态。
