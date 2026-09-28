# P4-B7-R1-E4-DYN-R2 运行说明

- 任务：`P4-B7-R1-E4-DYN-R2`
- 执行角色：执行智能体
- 状态：`blocked / finished`
- 动态结论：P1 已使用唯一一次预算并在产品 API 调用前由 browser root 所有权门禁停止；P2 依冻结顺序为 `not_run`
- 路线结论：`automation_route_exhausted=true`；不得创建或建议同类 DYN-R3
- 性质：执行方动态门禁，不是 P4-C12 独立验收，不构成 P4-B complete

## 1. 范围和边界

本任务只修正位于任务专属外部 evidence 中的 browser root promotion runner，没有修改产品、测试、依赖、lock、Forge、package、fuse、migration、staging 或系统设置。没有安装依赖，没有运行测试、build、package、P4-C12、Docker、OpenClaw、微信或 DeepSeek，也没有执行 Git 写操作。

仓库内只新增本运行说明和 198 项 DYN-R2 source manifest，并更新执行智能体自己的角色日志。原始进程、动态端口、隔离 profile、虚拟数据库和随机 owner marker 只保存在受限外部 evidence 中。

## 2. 起点、控制面和固定产物

- DYN-R2 原始起点清单：250 entries、250 unique、250 matched、0 missing、0 mismatch，manifest SHA-256 `565f91ccca3557c2aa1f955760d31a71c866c45ce6b0604c2de6378c1a5021b8`。
- 起点时 Git index staged paths 为 0；既有 `.pnpm-store/` 和 `.claude/` 未删除、清理、暂存或纳入任务摘要。
- 启动前最终 control：版本 `2026-09-29T02:30:54+08:00`，SHA-256 `649198fcc7baa7592d1980409e59d6724d08258b84dabd822b80d8a5eafffe5a`。该版本明确接受已经完成的 250 项门禁，并说明总控并发修改只涉及协调文档和刷新快照，没有改变产品、package 或外部 evidence；允许 DYN-R2 继续且不得重复动态预算。

启动前和 P1 终点的固定检查结果：

| 门禁 | 结果 |
| --- | --- |
| DYN-R1 evidence | 84/84 matched；manifest SHA-256 `db316ae191e295793edcded01f85ba81e54809d3696a61e364f11b372c6db8bf` |
| frozen source | 198/198 matched；manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| Electron dist | 73/73 matched；manifest SHA-256 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| Python resources | 67/67 matched；manifest SHA-256 `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |
| package out | 140/140 matched；manifest SHA-256 `97d72746ecfa2fd7ff3257cd183b5b033745e1e4b6519053264ab1cc400a15e6` |
| 最终 EXE | SHA-256 `149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199`；终点不变 |
| app.asar | SHA-256 `c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6`；终点不变 |
| production fuses | version 1；观察值 `48/49/48/48/49/49/48/49/49`，匹配冻结值 |
| 启动前现场 | 固定产品进程 0、产品窗口 0、Git staged paths 0 |

新 evidence 按 create-new 建立，没有复制或复用 DYN-R1 的 profile、owner session、数据库、PID、端口或运行结果。

## 3. Runner root promotion

P1 runner 共 265 行，SHA-256 `fa223794f2f92f1974fd70a20c5bbde603843142ad28626f6b5f7e50eefea02b`，Node 静态语法检查退出 0。规则位置如下：

| 冻结规则 | Runner 位置 | 实现摘要 |
| --- | --- | --- |
| 1 | 第 49 行 | `ElectronApplication.process()` 的 PID 只记录为 `launchPid` |
| 2 | 第 54～57 行 | 存活的 `launchPid` 仅在 executable path 精确匹配时成为 root |
| 3 | 第 51、59～63 行 | 仅当 `launchPid` 已退出时，按直接后代、路径、时间、ancestry 和 marker receipt 提升 |
| 4 | 第 59～63 行 | 候选必须恰好一个 |
| 5 | 第 65～70、170～173 行 | 从 root 建立后代闭包和非空 known-owned 集合 |
| 6 | 第 169 行 | 不设置精确进程数量预算，也不要求 launch PID 持续存活 |
| 7 | 第 82～96 行 | 定向 cleanup 前重新核对路径、时间、ancestry 和 marker |
| 8 | 第 65～70、170～173 行 | 生成零残留结论前必须先建立 initial known-owned 集合 |

静态扫描没有 synthetic self-test、Job Object、controller/worker、固定 PID、进程名广杀、第二次发现尝试、`executablePath` 启动选项、`--no-sandbox` 或新的动态预检 cell。Runner 清除了传入应用环境中的 `NODE_OPTIONS` 和 `ELECTRON_RUN_AS_NODE`。

## 4. P1：唯一 app.asar 动态预算

### 4.1 启动事实

- 动态预算：`1/1`，没有重跑。
- 时间：2026-09-29 02:37:24 至 02:37:28，Asia/Shanghai；记录时长 3,593 ms，没有触发 90 秒硬超时。
- launcher：Playwright `_electron.launch()` 默认 Electron loader；未传 `executablePath`；最终 `resources/app.asar` 为 application argument。
- 隔离：新的绝对 profile、新的虚拟数据库、新的动态 loopback 和新的 owner marker；没有读取真实凭据、账户或财务数据。
- 结果：`success=false`、`automation_route_exhausted=true`、`recoverCalls=0`。

### 4.2 首个失败和准确分类

`ElectronApplication.process()` 返回的 `launchPid` 在唯一启动后快照中仍存活，但其 executable 是命令包装进程，不是冻结 Electron executable。快照同时观察到它的一个直接 Electron 子进程，该子进程路径和本轮启动时间匹配。

冻结规则 2 不允许把路径不匹配的存活 `launchPid` 作为 browser root；冻结规则 3 又只允许在 `launchPid` 已退出时执行子进程提升。因此 runner 必须以 `browser_root_launch_identity_mismatch` 停止，不能利用本轮观察到的直接子进程继续调用产品 API。分类为：

- browser root：未建立；
- initial known-owned：未建立；
- 产品结果：`unverified`；
- 动态重跑：`false`；
- 自动动态路线：`automation_route_exhausted=true`。

这不是产品通过证据，也没有证据把它分类为产品 crash。按照任务卡，P1 不得修改后重跑，也不得建议或建立 DYN-R3。

### 4.3 P1 各项状态

| 项目 | 状态 | 证据边界 |
| --- | --- | --- |
| 主窗口与毛毛窗口 | `unverified` | browser root 门禁先失败，窗口断言未执行 |
| sandbox / context isolation / Node isolation | `unverified` | preload 安全断言未执行 |
| runtime online/authenticated | `unverified` | `window.maris` runtime API 未调用 |
| owner token 隔离 | `unverified` | renderer 隐私断言未执行 |
| `daily_finance` | `unverified` | modules API 未调用 |
| `runtime.recover()` | `0/1` | 未调用，不满足成功条件 |
| 隔离 owner session | `partial evidence only` | 隔离 profile 内加密文件存在，不能替代 API 验证 |
| 虚拟数据库 | `partial evidence only` | 隔离 profile 内数据库存在，未读取或复制正文 |
| 固定产物 | `pass` | EXE、app.asar、source、dist、resources、out 和 fuses 终点匹配 |

## 5. 进程、端口、窗口和 Tray 收口

Runner 通过 Playwright application close 路径结束；由于 browser root 从未建立，`browserExitedNaturally` 不能取得通过证据，不能声称完整正常产品退出已验证。原始 result 和独立终点读取共同确认：

- 固定 Electron/Maris 产品进程 0；
- 关联监听 0；
- 产品窗口 0；
- 固定产品 executable 全部不存在于运行进程中，因此 Tray 所属进程推断为 0；
- 没有按进程名广泛结束 Electron、Maris、Node 或 Python；
- 没有残留需要额外清理，未执行第二次动态发现或重跑。

Runner 的 `naturalResidualProcesses`、`finalRemainingProcesses`、`remainingListeners` 和 `remainingWindows` 均为 0。由于初始 known-owned 集合未建立，这些零值只用于说明最终现场已收口，不被写成所有权门禁或完整生命周期通过。

## 6. 日志和 Windows 事件

- Electron 日志：127 bytes，SHA-256 `a42335d8ddf7f0a289e6d10a4031034e33c038ab66298b14bb6ad764c05c8722`。包含一条 GPU overlay 获取失败信息，没有冻结 crash/assertion 关键字，也没有秘密模式。
- stderr：145 bytes，SHA-256 `cb64edccbe5d9014719673ba2a8da95b3051521e9e72249db9fe9954a8d6c12c`。内容是调试端点结束提示；动态地址和标识只保存在受限 evidence，未写入仓库正文。
- console、page error 和 crash event：均为 0；窗口/API 验证尚未开始，因此该空值不证明产品完整生命周期通过。
- Windows Application 事件：0；Code Integrity 事件：0；冻结异常计数 0。

## 7. P2：最终 EXE

- 状态：`not_run`。
- 动态预算：`0/1`。
- 原因：P1 没有通过 ownership、窗口、安全、runtime、module、recover 和自然退出的全部 gate；冻结顺序禁止进入 P2。
- 未启动最终 `Maris.exe`，未分配 P2 CDP 端口，未调用 `connectOverCDP()`，未调用 P2 `runtime.recover()`，未使用 `MARIS_E2E_EXIT_MS`。

## 8. 未运行项、失败和 warning

- P1：唯一一次启动在 browser root ownership gate 失败；没有产品 API 调用，产品保持 `unverified`。
- P2：`not_run`。
- tests、build、package、migration、P4-C12：全部 `not_run`。
- skip：没有运行测试，因此无测试 skip 统计。
- warning：Electron 日志有一条 GPU overlay 信息；stderr 有一条调试端点结束提示。二者均不含冻结 crash code，但不能替代尚未执行的产品 gate。
- 最终只读现场复核第一次在受限沙箱内查询 `Win32_Process` 时被系统拒绝访问；没有采用该次空结果。随后使用同一只读查询在获准环境中复核，产品进程、窗口和监听均为 0，没有启动或修改产品。

## 9. 隐私和安全

- 没有读取真实 AppData、密钥、token、真实账户或真实财务数据。
- 仓库正文不含 PID、动态端口、owner marker、nonce、HMAC key、真实用户名、个人绝对路径、数据库正文或原始私密日志。
- 隔离 profile、原始进程快照、端口和 marker 仅保存在任务专属受限 evidence 中。
- 没有修改系统 PATH、安全软件、代理、Docker 或任何全局设置。

## 10. 交付和摘要

仓库交付：

1. `docs/b7-r1-e4-dyn-r2-running.md`；
2. `apps/desktop/b7-r1-e4-dyn-r2-source.sha256`；
3. `docs/coordination/agents/executor.md`。

DYN-R2 source manifest 为 198 entries、198 unique、198 matched、0 missing/mismatch，SHA-256 `5e3b788c6ec2f8e125dd345a6e833beb530cd8790de12817f9342711373ea228`。它相对 DYN-R1 source manifest 仅更新一项总控授权的并发阶段协调文档摘要；产品、测试、依赖和 package 项没有变化。

受限外部 `runtime-evidence.sha256` 含 79 个有序条目，79/79 复算匹配，manifest SHA-256 `8872b541c2505e0a8b11df65c178ee0c7b3ca6d8ac6a66d277a31e48554e3aff`；manifest 自身为第 80 个文件。它覆盖 runner 与规则映射、preflight、P1 原始 result、失败分类、隔离 profile、owner marker receipt、日志、Windows 事件、终点资源状态、P2 `not_run` 和运行总表。仓库三文件的最终摘要将在角色日志完成后写入外部 `repository-delivery.sha256`，不纳入运行证据清单以避免自引用。

本任务停在 `blocked / finished`。P4-C12、测试智能体和技术顾问继续停止；后续验收方式由头脑风暴总控重新裁定。
