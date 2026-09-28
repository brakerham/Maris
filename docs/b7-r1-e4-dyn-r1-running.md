# P4-B7-R1-E4-DYN-R1 运行说明

- 任务：`P4-B7-R1-E4-DYN-R1`
- 执行角色：执行智能体
- 状态：`blocked / finished`
- 动态结论：P1 已使用唯一一次预算，但没有完成全部验证；P2 依冻结顺序为 `not_run`
- 性质：执行方动态门禁，不是 P4-C12 独立验收，不构成 P4-B complete

## 1. 范围和边界

本任务只复用总控已接受的不可变 package。没有安装依赖，没有运行测试、build、package、migration 或独立验收，没有修改产品、测试、依赖、lock、Forge、fuse、系统策略或真实用户数据，也没有执行 Git 写操作。

仓库内只新增本运行说明和 198 项 source manifest，并更新执行智能体自己的角色日志。动态 runner、原始日志、隔离 profile、虚拟数据库、随机 owner marker、进程与事件证据只保存在任务专属的受限外部 evidence 中。

## 2. 起点和共同前置

### 2.1 仓库起点

- 固定起点：246 unique、246 matched、0 missing、0 mismatch。
- 起点 manifest SHA-256：`28bc1658df1608164952ffe2369536979e0faaef530fd8c899891d1f7259c58f`。
- 起点清单路径本身不是 Ordinal 顺序；任务卡只把 missing/mismatch 定义为起点失败条件，因此未修改冻结清单。
- P1 启动前重读 control：版本 `2026-09-29T02:10:00+08:00`，SHA-256 `58a29c4488ef04531e9da63812140605bd2cbdbed6f19563df5dbb273cb951bb`，任务负责人、P1→P2 顺序和停止条件未变化。

### 2.2 固定 package 复算

| 门禁 | 结果 |
| --- | --- |
| PKG-R2 evidence | 40/40 matched，manifest SHA-256 `a082d25481adc94c61a50a0c96cc08cbfd141175c0adad85798e9157f274c01f` |
| source | 198/198 matched，manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| Electron dist | 73/73 matched，manifest SHA-256 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| Python resources | 67/67 matched，manifest SHA-256 `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |
| package out | 140/140 matched，manifest SHA-256 `97d72746ecfa2fd7ff3257cd183b5b033745e1e4b6519053264ab1cc400a15e6` |
| 最终 EXE | 246,032,896 bytes；SHA-256 `149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199` |
| app.asar | 758,263 bytes；SHA-256 `c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6` |
| production fuses | version 1；前六项 `48/49/48/48/49/49`，匹配冻结值；其余观察值 `48/49/49` |
| 默认 Electron loader | 未传 `executablePath`；默认 executable SHA-256 `bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e`，匹配固定 dist |
| 项目 Python | 启动检查 exit 0、stderr 0；Python 3.14.7 |
| 启动前资源 | 旧任务产品进程、Maris/毛毛窗口、关联监听和 Tray 所属进程均为 0 |

新动态 evidence 使用 create-new 建立。P1 使用新的绝对隔离 profile，由产品在该 profile 内创建虚拟 SQLite 数据库；managed sidecar 自行绑定动态非零 loopback。随机 owner 数据和 owner marker 没有进入仓库文档。

## 3. P1 packaged app.asar

### 3.1 唯一启动

- 动态预算：`1/1`，没有重跑。
- 时间：2026-09-29 01:58:27 至 01:58:32，Asia/Shanghai；记录时长 5,010 ms，没有触发 90 秒硬超时。
- launcher：C 盘 frozen install 的 Playwright `_electron.launch()` 默认 Electron loader。
- `executablePath`：未传。
- application argument：最终 package 的 `resources/app.asar`。
- 安全环境：`MARIS_E2E=1`、新的隔离 profile、最终 resources、已验证项目 Python、动态 loopback、虚拟数据库；保留 `--disable-gpu` 测试边界；清除了 `ELECTRON_RUN_AS_NODE` 和 `NODE_OPTIONS`。

### 3.2 首个失败与准确分类

P1 首个失败是 evidence runner 的 `root_identity_mismatch`。Playwright 返回的启动 PID在 runner 查询时已经退出，而实际 Electron browser 仍是该 PID 的直接子进程，使用固定 Electron executable，并处于同一本轮启动时间窗。runner 把“返回 PID 必须仍是 browser root”写成硬条件，因此在窗口与 preload API 断言开始前停止。

后续只读分类固定为：

- code：`p1_harness_root_identity_assumption`；
- dynamic rerun：`false`；
- product result：`unverified`。

这不是产品通过证据，也没有足够信息把它归为产品 crash。根据“一次动态 cell 不重跑”规则，P1 保持失败交付。

### 3.3 P1 各项实际状态

| 项目 | 状态 | 证据边界 |
| --- | --- | --- |
| 预期主窗口和毛毛窗口 | `unverified` | runner 在窗口断言前停止 |
| renderer sandbox / context isolation / Node isolation | `unverified` | preload 安全断言未执行 |
| runtime online/authenticated | `unverified` | API 轮询未执行 |
| renderer 无 token | `unverified` | DOM/bridge 检查未执行 |
| 隔离 owner session | `partial evidence only` | 收口后静态确认加密 owner session 文件存在，235 bytes；不能替代 renderer/API 验证 |
| `daily_finance` | `unverified` | modules API 未调用 |
| `runtime.recover()` | `0/1` | 未调用，不满足 P1 成功条件 |
| 虚拟数据库 | `partial evidence only` | 隔离 profile 内数据库存在，737,280 bytes；没有读取或复制正文 |
| Electron 日志 | `pass within captured log` | 127 bytes，SHA-256 `fefc7616cb691bc9142a36ec214113b14e92968314e8c25700803747a0692581`；0 个冻结 crash/assertion 字符串，0 个秘密模式 |
| Windows 事件 | `pass within captured query window` | Application 0、Code Integrity 0、冻结异常 0 |
| 固定产物 | `pass` | 终点复算全部不变 |

日志包含一条 GPU overlay 信息级错误，但没有 `0xC0000135`、`0x80000003`、`STATUS_DLL_NOT_FOUND`、`STATUS_BREAKPOINT`、`child-process-gone`、`render-process-gone`、`Target crashed` 或 assertion。因为 runner 过早停止，不能用这条日志证明完整应用生命周期通过。

## 4. P1 资源收口

runner 的初始结果错误地把已知进程集合记为 0；动态会话结束后的独立只读查询发现实际 browser 子树仍存活。没有把该错误摘要当作收口证据。

精确清理前重新读取 control，版本和摘要未变化。清理对象同时满足：

1. 是 Playwright 返回 PID 的直接子进程；
2. executable path 等于固定 Electron executable；
3. 启动时间落在本轮窗口；
4. 本轮 owner marker receipt 存在。

只对该根执行一次带子树的定向清理；清理前共 6 个本轮进程，命令 exit 0，清理后这 6 个 PID 全部为 0。随后原 runner 会话以 exit 4 结束。

v2 静态读取器终点复算：

- 产品进程 0；
- Maris/毛毛窗口 0；
- task-owned listener 0；
- owned Electron 进程树为 0，因此 Tray 推断为 0；
- EXE、app.asar、198 项 source、73 项 dist、67 项 resources、140 项 out 和 production fuses 全部匹配；
- 隔离 profile 共 63 个文件、3,694,697 bytes；所有本轮运行数据保留在受限 evidence，没有写入仓库或真实 profile。

## 5. 静态读取器更正

动态 P1 没有重跑。P1 结束后只发生两次静态读取器层面的可追溯问题：

1. v1 的空 listener 集合 PowerShell 管道语法错误，exit 1；原读取器 SHA、stderr 摘要和失败分类均保留，未启动产品。
2. 生成 v2 时第一次 literal replacement 没有命中，在写 v2 前停止；失败记录保留，未启动产品。

随后按固定行替换生成 v2，只读复算成功。v2 没有覆盖 P1 原始 result，也没有把静态 owner/database 文件存在改写成动态 API 通过。

## 6. P2 最终 EXE

- 状态：`not_run`。
- 动态预算：`0/1`。
- 原因：P1 没有通过全部 gate，冻结顺序禁止进入 P2。
- 未启动最终 `Maris.exe`，未分配 CDP 端口，未调用 `connectOverCDP()`，未调用 P2 `runtime.recover()`，未使用 `MARIS_E2E_EXIT_MS`。

## 7. 隐私与安全

- 没有读取真实 AppData、真实凭据、真实账户或真实财务数据。
- 没有把 token、refresh token、nonce、HMAC key、动态端口、PID、用户名、个人绝对路径、完整数据库正文或原始私密日志写入仓库文档。
- 原始 profile、PID/端口/路径、随机 owner marker 和 Windows 事件仅在受限外部 evidence 中。
- 没有按进程名广泛结束 Electron、Maris、Node 或 Python。

## 8. Warnings、失败和未验证项

- P1：1 次启动，evidence runner root PID 假设失败；产品行为保持 `unverified`。
- P1：统一正常退出未被观察；残留子树最终由任务所有权联合门禁定向清理。
- P1：窗口、安全隔离、runtime、modules 和 recover 均未取得动态通过证据。
- P2：`not_run`。
- 测试、build、package、P4-C12：全部 `not_run`。
- skip：无测试运行，因此没有测试 skip 统计。
- warning：Electron 日志有 1 条 GPU overlay 信息级错误；不含冻结 crash code。

## 9. 交付和证据摘要

仓库交付：

1. `docs/b7-r1-e4-dyn-r1-running.md`；
2. `apps/desktop/b7-r1-e4-dyn-r1-source.sha256`；
3. `docs/coordination/agents/executor.md`。

source manifest 为 198 entries，SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`，与 PKG-R2 source manifest 字节一致。

受限外部 `runtime-evidence.sha256` 含 84 个有序条目，manifest SHA-256 `db316ae191e295793edcded01f85ba81e54809d3696a61e364f11b372c6db8bf`；manifest 自身为第 85 个文件。它覆盖 preflight、run manifest、P1 原始 result、owner marker receipt、隔离 profile、日志、Windows 事件、定向清理、静态读取器失败与 v2 复算，以及 P2 `not_run` 记录。仓库三文件的最终逐文件摘要另存于外部 `repository-delivery.sha256`，不纳入上述运行证据清单，以避免交付摘要自引用。

本任务停在 `blocked / finished`，等待头脑风暴总控决定是否建立新的、具有新动态预算的受限恢复任务。当前不得自行重跑 P1、进入 P2 或启动 P4-C12。
