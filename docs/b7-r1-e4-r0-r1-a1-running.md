# P4-B7-R1-E4-R0-R1-A1：唯一标准流修正与停止交付

- 角色：本项目既有执行智能体。
- 状态：`blocked / finished`；执行方交付，不是独立验收或项目 complete。
- 控制输入：`2026-09-28T20:18:00+08:00`；已完整读取 A1 任务卡、协调文件、上一轮报告、总控核对和 D14 方案。
- 起点核对：2026-09-28 23:26 Asia/Shanghai；唯一动态 controller 启动于 23:34:17，首次 combined 于 23:34:23 失败并立即停止；资源收口复算证据时间为 23:37:40。
- 首个失败：`P4-E4-R0-R1-A1-HARNESS-PROCESS-001 / process_budget_exceeded`，combined 再出现额外 conhost。
- 修正预算：1/1 已使用；不存在 attempt-2。timeout、Q1～Q6、package、P1、P2、P4-C12 全部未运行。
- `R0_READY_PACKAGE_0_OF_1` 不存在；仅保存 `R0_FAILED_PACKAGE_NOT_RUN`。

## 1. 起点、授权与文件边界

[本轮起点](coordination/snapshots/p4-b7-r1-e4-r0-r1-a1-start.sha256)为 230 个唯一、有序路径，修改自己的角色日志之前逐文件复算为 **230 matched、0 mismatch、0 missing**。manifest SHA-256：

`74dfb034b57356684f2dd45522e7805da8401dd0ad6687c53b2fb4a8f02de6d7`

最新 control SHA-256：

`949e68d5a2b5aa15047d4088aa6bbd31b7cc43908572763189c1eb3b7bda8ba0`

启动前及失败后交付时版本和摘要未变。PowerShell 为 7.6.5 Core / x64，executable SHA-256 为：

`362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139`

个人运行时绝对路径只在外部 controller-owner.json 保留，不写入仓库报告。

本轮仓库仅更新 [executor.md](coordination/agents/executor.md)，新增本说明和 [A1 source 清单](../apps/desktop/b7-r1-e4-r0-r1-a1-source.sha256)。相对 230 文件起点，最终为 229 unchanged、1 changed（仅自己角色文件）、0 missing，另有两份新增交付。source 清单 198 个唯一、有序路径，逐文件 198/198 匹配，按字节复制上一轮已冻结清单，SHA-256：

`04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`

外部仅 create-new 创建此前不存在的：

`C:\MarisE4\E4-20260928-1255\r0-driver-recovery-r1\attempt-1`

没有覆盖或修改 attempt-0、旧根级 closeout/classification/manifest，以及任何 E4/E4-R1 文件。没有修改产品、测试、Forge 配置、wrapper、staging、依赖、lock、.npmrc、其他角色或永久环境；没有 Git 写操作。既有 .claude/、.pnpm-store/ 保持原样。只读 Git diff 检查退出 0，出现 executor.md 将由 Git 在以后把 LF 转为 CRLF 的提示；本轮未执行该转换或 Git 写入。

## 2. 原样复制与唯一修正

先在 attempt-1/source-copy 保存 9 个原支持文件，包括 8 份源码及 1 份 shim，复制前后 SHA-256 全部一致；copy-proof.json 记录各原始摘要和复制摘要。再以 create-new 在 attempt-1 根生成本轮最终源码，没有改写原样复制文件。六份 PowerShell 源码在首次动态执行前静态解析，语法错误为 0；support.sha256 在执行前冻结，之后未修改。

运行逻辑修正仅涉及三条标准流和对应有界 pump：

- worker 为 native 显式设置 UseShellExecute=false、CreateNoWindow=true、stdin/stdout/stderr 三重定向。启动后立即关闭 stdin，两条 BaseStream 分别 CopyToAsync 到 worker 的 Console.OpenStandardOutput()/OpenStandardError()。取得真实 native exit 后，两个 pump 最多等待 5 秒；正常结束应产生单独的 native-pump-result.json，保留真实 exit、pump 状态、drain 时限与 worker exit 的区别。
- synthetic parent/child 创建下一层 pwsh 时同样三重定向和无窗口；立即关闭子 stdin，stdout/stderr 分别异步 drain 到 Stream.Null，并应写入独立 child-streams receipt。
- controller 增加与上述 pump/child-streams receipt 对应的验证，保留预期值、2/4 单元预算、6/24/31 总预算、固定 Q 顺序和各项时限。任务/control 标识及历史累计报告字段同步为 A1。
- verify 仅把任务输入绑定为本轮 230 文件起点。capture、Job、pnpm adapter、Forge probe 和 shim 保持同字节，没有修正其他行为或产品功能。

正式 Run-Captured allowlist 仍只含 where-pnpm、pnpm、forge-probe。原生参数继续用一维 ArgumentList；pnpm adapter 仍仅允许四个固定查询。没有忽略或过滤 conhost，没有 breakaway，没有增加预算，没有第二次修正。

| 文件 | attempt-0 SHA-256 | attempt-1 SHA-256 / 差异 |
| --- | --- | --- |
| capture.ps1 | 27e38b09ac24326b7b8c7eb45d887501484daa3d57c75524fbd80cc09e5483b9 | 同字节 |
| controller.ps1 | 62767e79a8e6ae39419026f467c0b0b789c9d523b26f00ded2f73a5491e81868 | 1c5f4512de1ed3df97fc0a4ec49cf212ad4a8cd8e2de81b4a76fa81ebc3bd36d |
| forge-pnpm-bin/pnpm.cmd | 57785cc51fff3a94b68815e46f48a400f1cb016f9edc82d2cb9606cbdb088bdf | 同字节 |
| forge-probe.mjs | 2809939cded9888f6516dbfeaed332d3acdf0654bb0d89a5ecbc3200168bd9ad | 同字节 |
| job.cs | 33319cde7e68d9bb1b373fd2bada86b48a67d657b3cb12d595229fe9f1dab8bf | 同字节 |
| pnpm-adapter.ps1 | f9b3a04b78549f2b924e6959dabce6bfb556171144523a8cab8b16d741d1879f | 同字节 |
| synthetic.ps1 | 6ec0aae01f7480bf640dcb4f23ed777ad4d90ca83bb39a9eeae9ded53eeb9aa7 | 9561b0ee29b3cb3b3b85ad31a2dc861dabdf1fb97c72a7a36f086f7b29520635 |
| verify.ps1 | 4b7b2671d0acf5783322bb898bc681be9e1d07c9f0841b3e2d525ddfa39d91e9 | ea7da7f5234704268b3c15e1d0153fceae41379a2af43e26e9c6dce70661d6c9 |
| worker.ps1 | a302ac55c1c9d9ac7a0653d02dad36efabb5548744628b405fd570d67676b1e0 | af17a4a5d5e9b570d4b0c47ae1f582eaa99955df6d6523ebc7bfed181b5b8d88 |

本轮 support.sha256 9 个文件，SHA-256：

`d1b609b3d46411cf7af9a9ebbdab0e7fa2da8ca7a3269706a267ad4546bf4823`

## 3. combined 的唯一实际运行与首失败

controller 仅启动一次，工具 session 16638 已退出 1。worker 先加入任务专属、无 breakaway 的 Windows Job，然后才接收 GO payload 并启动 native fixture。Job 关联和成员 ledger 成功，本轮记录：

| PID | 用途 / image | parent PID | 所属 |
| --- | --- | --- | --- |
| 23664 | R0-only controller / pwsh.exe | 不在本证据中推断 | controller |
| 32040 | 门闩 worker / pwsh.exe | 23664 | combined Job |
| 7932 | synthetic fixture / pwsh.exe | 32040 | 同一 Job |
| 10136 | 额外 conhost.exe | 7932 | 同一 Job |

Job ID：`f16f276bb83b4edd9015e4dd9994baa4`。combined MaxActive/MaxTotal 均为 2，实际 Job total=3，三个唯一 PID 与 accounting 一致。首次预算失败后立即终止整个 Job；没有过滤 image 或把第三个进程从统计中移除。

| 实测字段 | 值 |
| --- | --- |
| synthetic argumentCount / commandTokenCount | 13 / 14；不是任何 Q 的计数 |
| deadline / 实际耗时 | 15 s / 521 ms，因预算提前失败 |
| 首个 failureCode | process_budget_exceeded |
| native exitCode | null，没有取得正常退出值 |
| workerExitCode | 124，Job 强制终止后的 supervisor 值 |
| timedOut / forcedCleanup | false / true |
| captureComplete / cleanupComplete | true / true |
| cleanup / outer drain | 4 ms / 4 ms，均小于 5 s |
| Job total / active / ledger unique PID | 3 / 0 / 3 |
| stdout / stderr | 各 0 bytes；原始 bin 已保留 |
| native-result / native-pump-result / combined-receipt | 未产生，不能声称正常 pump 或 native exit 已通过 |
| transportOk | false |

三条标准流配置可从冻结源码核对，native-start receipt 和 Job 事件证明 fixture 已实际启动。但它随后被整体终止，没有形成正常 pump completion 或 helper payload receipt。因此报告不把“源码已重定向”写成“正常三流验证已通过”，也不把空输出写成双流压力通过。

四类 synthetic 的准确状态：

| 类别 | 结果 |
| --- | --- |
| 空格/中文参数保持 | combined 已启动，但 fixture receipt 缺失；未验证通过 |
| 512 KiB stdout + 512 KiB stderr 并发完整性 | 实际各 0 bytes；未验证通过 |
| 真实 native exit 37 | native exit 为 null；未验证通过 |
| timeout parent/child/grandchild 收口 | not_run；不存在 timeout 目录或其回执 |

四类通过数为 0/4。本次异常路径确有 Job 全收口证据，但不能替代未运行的专用 timeout 自测。

summary.json 外层 failureCode 为 controller_runtime_failure，原因是预算强制收口后 combined fixture receipt 不存在，随后读取引发次生错误。首失败由 synthetic-combined/result.json 的 process_budget_exceeded 定义。另建 failure-classification.json 说明两者，不覆盖原 result、summary 或日志。

观察结论仅为：本轮明确三流重定向修正后，combined 仍出现 conhost 并失败；尚不能证明 Windows/pwsh 派生该进程的充分根因。没有 pnpm、Forge、package、Electron 或 Maris 产品缺陷结论。严格执行 A1 的“再次出现 conhost 或任何新缺陷即停止”；不修改源码，不运行 timeout、Q 或 attempt-2。

## 4. 预算与后续 not_run

| 尝试 | controller | observed harness Job 成员 | Q targets | 总计 |
| --- | --- | --- | --- | --- |
| attempt-0 不可变历史 | 1 | 3 | 0 | 4 |
| attempt-1 本轮唯一运行 | 1 | 3 | 0 | 4 |
| 跨尝试累计 | 2 | 6 | 0 | 8 / 35 |

attempt-1 live 总预算仍为 31，harness 总预算 6、Q targets 24；本轮实际为 4/31、harness 3/6、Q 0/24。combined 单元已出现 3 > 2，整体尚有预算不允许越过该门禁。timeout 的上限 4 没有消费。历史累计 8/35 与本轮 live 分开披露，不用历史额度扩容本轮。

| Q | 冻结参数语义 | argumentCount / commandTokenCount | deadline | 实际 |
| --- | --- | --- | --- | --- |
| Q1 | where.exe pnpm | 1 / 2 | 10 s | not_run |
| Q2 | pnpm --version | 1 / 2 | 15 s | not_run |
| Q3 | pnpm config get hoist-pattern | 3 / 4 | 15 s | not_run |
| Q4 | pnpm config get public-hoist-pattern | 3 / 4 | 15 s | not_run |
| Q5 | pnpm config get node-linker | 3 / 4 | 15 s | not_run |
| Q6 | Node + probe / installed package-manager / desktop-root | 3 / 4 | 60 s | not_run |

表中参数、预期结果和时限是冻结合同，不是实测。Q dispatch 为 0；没有 Q 的 stdout、stderr、native exit、PID、Job、probe argv receipt 或四项 Forge 内部查询证据。package/P1/P2/P4-C12 均 not_run，package 使用 0 次。

## 5. 不变性和资源关闭

开工先逐文件核对 230 文件和旧 26 文件证据，再只读复算完整现场；支持组件执行前及失败收口后均通过：

| 固定项目 | 核对结果 |
| --- | --- |
| E4 source copy / repo frozen source | 198/198 / 198/198 matched |
| Electron dist | 73/73 matched |
| 虚拟污染 marker | 9/9 matched |
| E4 / E4-R1 旧 evidence | 26/26 / 14/14 matched |
| attempt-0 旧根 delivery 清单 | 26/26 matched，27 份原文件保持不变 |
| node_modules | 12,451 files，570,581,590 bytes |
| out / .maris-staging | false / false |
| transition artifacts / 自有 Electron、Maris、Node、Python | 0 / 0 |
| 本轮 controller + Job 四个记录 PID 仍存活 | 0 |
| attempt-2 / ready marker | 不存在 / 不存在 |

node_modules 仍按 LF、UTF-8 无 BOM 的原算法得到：

`f06ce306456134f7f78176e64d3f9a7e54133607d3e9202ff6bb1a9fcbf800c7`

workspace lock：

`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`

.modules.yaml：

`68dd21a69c44908e3436b47c0ee40be328cfab4b9e7d0f89728fd809e7b317e1`

固定 Node、pnpm native、Electron executable 和 PowerShell 摘要全部匹配起点。关闭证据为 closeout-state.json、closeout-processes.json。本轮未设置 PATH 配方和 ELECTRON_CACHE：combined 在该分支前失败；controller 完整环境前后摘要比较为 environmentRestored=true。未修改用户/系统 PATH、系统 pnpm、注册表、代理、安全软件、ACL 或 Docker 全局设置。没有启动外部服务或集成，没有读取真实财务数据。

## 6. 固定证据、逐文件摘要与复算算法

attempt-1 共 **40 文件**；delivery-evidence.sha256 为 39 条唯一、有序记录，加清单自身。覆盖 source-copy 原样文件、最终支持源码、复制证明、修正差异、静态解析、执行原始输出、Job/PID、原运行清单、关闭证明、故障分类和失败标记。旧根级清单没有更新。

| 清单 / 证据 | 文件或记录数 | SHA-256 |
| --- | --- | --- |
| 旧根 delivery-evidence.sha256 | 26 条，27 旧文件 | aef1d227edea8b12058bd0323eecbd96cf87e3e50dc22642492c61ae1d2ddcbb |
| attempt-1/support.sha256 | 9 支持文件 | d1b609b3d46411cf7af9a9ebbdab0e7fa2da8ca7a3269706a267ad4546bf4823 |
| attempt-1/final-evidence.sha256 | 34 条首次运行记录，34/34 matched | fd993d8dec84ada6b7a0595c07805e71e13fde024c5d20b2d637187c814df4b2 |
| attempt-1/failure-classification.json | 1 文件 | 419eec125f30125709a2f6c2ef3f1a38350fbbbf0fcac7a8ba23e7a975280d4d |
| attempt-1/delivery-evidence.sha256 | 39 条记录，目录共 40 文件 | ac0da66b9f5e9626bca0d491c675ee4276876ddc248859c739c9cfa89343e87a |

外部 evidence 算法：相对路径使用 /，按路径排序，每行 `path<TAB>bytes<TAB>lowercase-sha256<LF>`，UTF-8 无 BOM、末尾一个 LF；清单排除自身。逐文件核对长度和 SHA，再对清单原始字节计算 SHA。support/source 两列清单使用 path<TAB>sha，198 source 及所有支持文件均可逐项复算。source-differences.json 保存九项前后摘要，copy-proof.json 保存九项原样复制证据；没有以不同换行算法代替冻结的 node_modules 聚合摘要。

最终停在 `blocked / finished`。唯一修正已消耗，等待头脑风暴总控核对重复 conhost/预算失败；后续需要新的裁定，本执行方不创建新任务或继续启动任何动态检查。

