# P4-B7-R9-IPC-ORIGIN 执行方交付

本任务交付状态为 `review / finished`，等待总控冻结独立复验。唯一产品修改是 `apps/desktop/electron/main/security.ts` 的开发来源分支。执行方原反例、定向回归、类型检查、lint、唯一一次 package 和静态产物核对已完成；不宣布 IPC-ORIGIN-001、SETTINGS-001、SEC-04 或 P4-B 关闭。

## 输入、范围与接续

- 总控版本：`2026-11-01T15:58:19+08:00`。2026-11-01 首次接单，2026-11-02 恢复最终交付；恢复时重读 AGENTS、README、项目协调说明、协调 README、control、executor 和原 R9 卡。
- 固定起点：`docs/coordination/snapshots/p4-b7-r9-ipc-origin-start.sha256`，**1,432 项**，清单 SHA-256 `a5ca0dca98e9bde4ffaf79204bbf94225cad0db92095c950475a2a0ef4cd5e6a`。接单前原字节、逐项摘要、路径唯一有序、UTF-8 无 BOM/LF、真实 TAB、排除自身全部通过，暂存区为空。
- R10 交付 50 项、正式来源 8 项、首次材料 29 项按各自实际基准根核对。原独立测试、报告和首次材料保持只读，没有运行独立测试。
- 仓库交付严格限于任务卡七路径：security.ts、security.test.ts、ipc.test.ts、settings-snapshot.test.ts、本说明、新 source 清单、本人 executor 日志。其余起点 **1,427 项原字节保持**；既有授权变化五项，另新增说明与 source。
- 新外部根：`C:/MarisIpcR9/R9-20261101-161412`。普通复制工具与必要依赖、物化起点源码；无 junction/reparse、无依赖安装或下载、无新产品 profile。旧 `C:/MarisSettingsR8/R8-20261019-103900` 和 R8-R2 根保持只读。
- Node 24.21.0、pnpm 12.7.0、Electron 44.4.5、Playwright 1.63.0 及已有 Python 3.14.7 保持。实际 Node、pnpm、Vitest、TypeScript、Electron/Forge 入口及 lock 的九项前置核对通过。完整历史依赖审计绑定旧 `inputs/final-audit.json`，SHA-256 `465624f22064e7c9ccb5915932d325254e0dced7c43db5f9f3c779b62941d269`，未逐命令重扫依赖。
- lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；官方本地 Electron ZIP SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。无永久 PATH、系统配置或 Git 写操作。

## 最小实现与原合同

旧开发判断使用 `url.startsWith(developmentOrigin)`，配置 `http://127.0.0.1:5173` 会错误接受 `http://127.0.0.1:51730/index.html`。现在分别用平台 `URL` 解析配置与请求，仅在双方均为 HTTP/HTTPS、无用户名密码、origin 非 null 且规范化 origin 全等时放行开发网络分支。不同协议、主机、有效端口拒绝；同源路径、query、hash 不影响结果。平台处理主机大小写和默认端口，不做 DNS 或 localhost/127.0.0.1 别名等同。解析失败安全拒绝，blob/data/javascript/credentials 不取得开发访问权。

生产 `file://` 与 `maris://app/` 原分支、CSP、sandbox 原样保持。这是兼容保持，不能据此声称生产路径已完整安全验收。main/index、ipc-contract、preload、renderer、settings-hydration 均未修改。`validateIpc` 的 sender/mainFrame 优先检查、参数严格 schema、`ipc_origin_rejected` 保持。

执行方扩展原虚拟 main fixture 的可选开发来源；默认行为保持。测试调用真实 `isTrustedRenderer`、`validateIpc` 和 main/companion 注册 handler，没有 mock 掉被测谓词或接口。反例保持同 sender、同 mainFrame 对象，只换 URL。main 同源 getter 返回精确三字段，错误来源不会保存设置、恢复 Host、改 outbox 或开窗口；包含写 handler 业务执行前拒绝。companion 仅信任自身开发来源，另一窗口来源拒绝。副作用采用启动后基准增量核对，保留原断言。

| 产品／测试文件 | SHA-256 |
| --- | --- |
| apps/desktop/electron/main/security.ts | `467082c0923a963aaf3f93c87a42cdeb6722325dc3ad29b50f4b57b5f2931fce` |
| apps/desktop/tests/unit/security.test.ts | `3e969d89025192506a20f6b5d07e268bab27d44cefb3a474f7873c024b41a97c` |
| apps/desktop/tests/unit/ipc.test.ts | `4d6382f2ec663245d6b077c62f11cf579d2406bf07f8cad7c87eaecc9d2cdc4c` |
| apps/desktop/tests/unit/settings-snapshot.test.ts | `3a07e47ac17600b371e82cb757107011fbbf042a6083d59b49fda9d48b91f59f` |

## 执行方开发验证

以下均为已有实际运行结果，恢复交付时没有重跑。执行根为新副本 `workspace/apps/desktop`，固定 `tools/node/node.exe` 调用 `evidence/tools/run-dev.cjs`，真实子进程参数、开始/结束时间、退出码和标准输出分别在 `evidence/tests/<phase>-exit.json` 及相邻日志。

| 阶段／phase | 范围 | 结果 |
| --- | --- | --- |
| 修复前 `red1` | 三文件，名称过滤 `R9 original counterexample` | **3 failed、0 passed**，exit 1；79 个节点未被名称过滤选中，JSON status 为 skipped／顶层 pending，不是新增 skip/xfail |
| 修复后 `directed1` | security、ipc、settings-snapshot、未改 settings-hydration | **109 passed、0 failed、0 skipped/pending/todo**，exit 0；4 文件、109 个唯一节点 |
| `typecheck1` | 既有 TypeScript `tsc --noEmit` | exit 0，stderr 空 |
| `lint1` | 既有 `apps/desktop/scripts/lint.mjs` | exit 0，stderr 空 |

| 定向文件 | 原节点 | 新增节点 | 最终通过 |
| --- | ---: | ---: | ---: |
| security.test.ts | 3 | 42 | 45 |
| ipc.test.ts | 3 | 9 | 12 |
| settings-snapshot.test.ts | 21 | 4 | 25 |
| settings-hydration.test.tsx（未修改） | 27 | 0 | 27 |
| 合计 | **54** | **55** | **109** |

三条红灯分别落在生产谓词、真实 validateIpc、实际 main getter，均先通过同源正对照，再观察不同端口被错误接受。红灯原始 JSON、日志、退出回执及修复前七个相关源码保留于 `tests/red1*` 和 `red-source/`。红灯与绿灯重复节点不相加为唯一用例；未运行旧完整 217 项、模块、冷入口、退出、H1/W1/S1/S2 或独立集合。

来源覆盖包括配置有／无尾斜杠、同源 path/query/hash、5173/51730 双向边界、协议和主机变化、后缀欺骗、credentials、非法／相对／空地址、data/javascript/blob、默认 HTTP/HTTPS 端口和主机大小写、file/maris 生产邻接、身份优先级与严格参数。所有测试和 package stderr 均为空，最终没有测试 warning、失败或 skip。

`development-nodes.json` 是原报告的事后唯一节点索引。旧通用 driver 的每阶段 `*-source.sha256` 未收录 security.ts、security.test.ts、ipc.test.ts，不能把该局部清单称为完整执行输入。完整修复前源码由 `red-source/` 保留，最终代码由打包前 1,432 项构建冻结及七项 `development-inputs.sha256` 绑定；后者明确是事后索引，未回填运行时间或改写首次记录。仓库与实际构建副本的这七项字节一致。

## 唯一新 package 和静态产物

开发门禁后冻结 `evidence/static/workspace-source.sha256`，**1,432 项**，SHA-256 `492e1a1e9d3c9885a7e7f486c8d6a9c4dc57d83981ef5c053548072d599a3a1a`。这是实际构建输入；最终包含交付说明的 1,433 项仓库 source 是另一清单。构建副本中的 executor 保持打包前版本，未拿最终日志冒充构建时输入。

复用既有 wrapper `workspace/apps/desktop/scripts/package-desktop.mjs`，任务局部 Node/pnpm 和 LOCALZIP 通过真实 Forge pnpm 解析前置检查。`actual-forge-env.jsonl` 记录实际 Forge 子进程入口及局部 PATH。原 wrapper/Forge/依赖/lock 均未修改。

- package **1/1**：2026-11-01 **20:53:10.216～20:53:15.853（Asia/Shanghai）**，**5,637 ms，exit 0，signal null**。唯一启动哨兵 `package-started.json` 和 `package-result.json` 保留。
- 原七静态门禁 **7/7**：package 根、EXE、app.asar、production fuses、Python 资源、污染、staging。fuse wire v1 前六冻结位全部匹配；out **140 文件**、Python **67/67** 精确匹配、asar **11 文件／0 links／0 unpacked**；污染命中 0、staging 和 transition 残留 0。
- 新包：`C:/MarisIpcR9/R9-20261101-161412/workspace/apps/desktop/out/Maris-win32-x64`。
- `Maris.exe`：246,032,896 bytes，SHA-256 `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b`。
- `resources/app.asar`：763,591 bytes，SHA-256 `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2`。

**新 EXE 和 asar 与旧 R8 字节相同。** 固定 Forge Vite 插件在生产 build 将 main/companion 开发服务器地址定义为 undefined，开启 minify，现有配置不生成 sourcemap，开发条件分支因此裁剪。本任务修复进入冻结源码和实际构建，但不能声称新比较逻辑在 production 包中执行，也不能仅凭 EXE hash 证明修复。

额外静态来源绑定由 `static/origin-bundle-binding.json` 给出：实际 asar `.vite/build/main.js` 与本次生成文件逐字节相同，主 bundle SHA-256 `cb4a633125acd1c690ccf18827373555755bc45fb50c5a4bb4a8deee11d228ce`。记录冻结 `main.ts → index.ts → ipc-contract.ts → security.ts` import 链和编译器摘要；AST 定位实际 validator `gt`、生产谓词 `nu`、main 注册包装及 companion 两个真实校验调用，合计三处；getter 映射到 main 注册包装。最终谓词保留原 file/maris 分支，开发参数在调用中已被消除。工具仅解析实际 bundle，没有执行 bundle 或正式动态入口。此证据为构建／调用映射，不是原生运行通过。

本轮 **EXE／Electron 应用 0、原生 helper 0、开发服务器 0**；新包动态 `not_run`。旧 R8 系列 package 1/1、EXE 3/3 和 Tester 产品 2/8、helper 3/6 保持；旧 S1/S2 仅为历史执行方证据，不移作本包动态结论。

## 首次错误、warning 和过程限制

1. 三条修复前产品反例失败按原样保留；之后定向全绿不覆盖红灯。
2. 一次只读路径推测寻找 pnpm.cmd 未找到；真实固定入口是 pnpm.exe，打包前已经核验，未因此启动 package 或安装依赖。
3. 首次只读 asar 提取使用 Unix 分隔符，报 `.vite/build/main.js was not found in this archive`，exit 1。首错 `static/origin-binding-first-error.json` 及首版 `inputs/origin-bundle-binding-v1.mjs` 保留；按既有读取器使用 Windows native 分隔符后通过，未重打包或修改产物。
4. 最终文档／清单写入曾因自动审批服务额度不足未执行；该返回明确是审批无法完成而非不安全裁定。没有绕过审批，2026-11-02 用户继续后通过原审批路径完成收尾。中断期不报告连续观察或心跳；无新测试／打包预算消耗。
5. 续接首次只读 Python 默认 GBK 解码清单失败；明确 UTF-8 后复算通过。失败命令无写入。只读 Git 出现全局 ignore 权限提示，以及五个工作文件 LF→CRLF 提示；`git diff --check` 退出 0，暂存区为空，没有改变 Git 设置或状态。

内部只读执行辅助用于计数与差异核对，未启动 Tester、技术顾问或独立验收。早先两个内部子任务因额度／会话中断未交成果，由父执行方接回并完成测试；后续静态辅助没有产品修改权限，父执行方统一集成结果。

## 清单、资源收口与交接

最终索引为 [closeout.json](C:/MarisIpcR9/R9-20261101-161412/evidence/closeout.json)。其中各清单记录实际基准根、条目数、格式和清单自身 SHA-256，不在报告内递归包含自身摘要。

| 清单 | 条目／用途 |
| --- | --- |
| `apps/desktop/b7-r9-ipc-origin-source.sha256` | **1,433**；由固定起点更新获准路径、加入本说明，排除 source 自身 |
| `evidence/delivery-seven.sha256` | **7**；全部仓库交付逐文件 SHA-256，包含本说明、本人日志与 source |
| `evidence/static/workspace-source.sha256` | **1,432**；打包前实际输入，已冻结不改 |
| `evidence/development-inputs.sha256` | **7**；最终相关代码事后摘要索引，基准为实际 workspace |
| `evidence/tools.sha256` | **7**；开发／package／静态工具；首版错误工具另外在 inputs 中保留 |
| `evidence/runtime-tools.sha256` | **3**；任务局部 Node 与两个普通 pnpm 二进制副本 |
| `evidence/static/out-manifest-v4.tsv` | **140**；完整包文件的路径、字节数、SHA-256 |
| `evidence/static/python-resources-v4.tsv` | **67**；Python 资源路径、字节数、SHA-256 |
| `evidence/static/asar-manifest-v4.tsv` | **11**；归档文件路径、字节数、SHA-256、unpacked 标记 |
| `evidence/evidence-manifest.tsv` | **75**；正式证据，总摘要在 closeout；排除自身、delivery-seven、closeout 及测试 cache/tmp |

两列清单按路径 ordinal 排序，行是 `path<TAB>lowercase SHA-256<LF>`，UTF-8 无 BOM。复算先按清单记录的 base 逐文件计算原字节 SHA-256，再计算清单文件本身 SHA-256；三列产物清单另核对字节数，asar 四列按归档内部文件核对。不要将仓库终点 source 与构建时输入混用。完整七文件摘要和可复算总摘要在 delivery-seven 与 closeout 交叉绑定。

`end-input-audit.json` 已核对旧 R8 构建 1,365／out 140／resources 67、tools 14／lifecycle 63／evidence 108，旧 R8-R2 tools 6／inputs 4／evidence 255，以及 R10 50／8／29，均匹配。`resume-audit.json` 再核对本轮起点授权变化和 1,432 实际构建输入，无额外漂移。

2026-11-01 `resource-closeout.json` 和 2026-11-02 `resource-resume-closeout.json` 查询成功，本轮新根标记的 Node/pnpm/Maris/Electron 当前进程均为 **0**；无强制结束、无资源删除，保留新包、工具与全部证据。本轮没有启动产品，窗口／监听及完整历史后代未作全系统枚举，不据此作超出查询范围的保证。只读查询和摘要计算进程随命令自然结束。

执行方到此停止，交付 **review / finished**。总控决定下一次独立复验及 Windows 剩余条件；本任务不关闭缺陷、不修改矩阵、不继续 R8/R10、P4-C 或其他任务。真实前端阶段的参考图、方案和模型策略提醒保持。
