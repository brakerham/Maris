# P4-B7-R1-E4-R1 pnpm 路径恢复与最终门禁运行说明

## 1. 结论

- 任务状态：`blocked / finished`。
- R0 硬预检没有通过；失败发生在任务外控制脚本的参数转发层，尚未得到有效的 `where pnpm`、pnpm version/config 或 Forge `spawnPackageManager` 结果。
- R1 package 预算保持 `0/1`。package 后静态门禁 R2、P1 packaged app.asar 和 P2 最终 `Maris.exe` 均为 `not_run`。
- 本轮没有形成产品、Forge、wrapper、staging、依赖或 Electron 运行缺陷证据。缺陷 `P4-E4-R1-R0-DRIVER-ARGS-001` 只属于任务 evidence driver。
- 任务卡规定 R0 任一项失败或同一 cell 需要第二次执行时立即停止，因此没有改正 driver 后重跑 R0，也没有消耗新 package 预算。

## 2. 起点与保留现场门禁

最新 control 为 `2026-09-28T15:25:00+08:00`，只授权既有执行智能体执行 E4-R1；技术顾问、测试智能体和 P4-C12 保持停止。

| 核对项 | 结果 |
| --- | --- |
| R1 仓库起点 | 219 matched、0 mismatch、0 missing；manifest SHA-256 `88538b00a627deeecb90f05f65c08a38ab4e6abe8a2da9cc03e569d0d1370fee` |
| E4 仓库 source | 198 matched、0 mismatch、0 missing；manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| E4 原始 evidence | 26 matched、0 mismatch、0 missing；manifest SHA-256 `5958703ccea01cd0b8ef3bd72b681dfbdb7b5b398c7b8c7bc5ee7cd2fb1ba2d1` |
| C 盘 source copy | 198 matched、0 mismatch、0 missing；manifest SHA-256 `4a4a73508d400ddb557de2a3235d6c6cf39c4fecdac01c854c2aea0dc9656ce2` |
| Electron dist | 73 matched、0 mismatch、0 missing；manifest SHA-256 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| 污染前置 | 9 matched、0 mismatch、0 missing；manifest SHA-256 `b239e272480bdb33b6aa23f380c1a1f1e0c36f7590bc9784e3d32d40799605f8` |
| workspace lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| package 前资源 | `out=false`、staging=false、transition artifacts=0、owned process=0 |

固定工具继续匹配：Node executable SHA-256 `ba4e6d110e8c1592a1ecd390f6b05f3da124b13871a5be62b341a07a853c6c32`；pnpm native 为 53,373,952 bytes、SHA-256 `3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce`；Electron executable SHA-256 `bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e`。版本文件仍为 Electron 44.4.5、Playwright 1.63.0 和 Forge 8.0.0-alpha.10。

完整 `node_modules` 起点为 12,451 files、570,581,590 bytes。按相对路径、字节数和单文件 SHA-256 排序，并用 LF 连接后的摘要为：

```text
f06ce306456134f7f78176e64d3f9a7e54133607d3e9202ff6bb1a9fcbf800c7
```

`.modules.yaml` SHA-256 为 `68dd21a69c44908e3436b47c0ee40be328cfab4b9e7d0f89728fd809e7b317e1`。

E4 阶段 A 只作为已经由 E4 和总控固定的输入，本轮没有重复执行，也没有把 E4 的历史通过计作 R1 实际结果。

## 3. R0 task-owned shim 与单一环境设计

在 `<task-root>/r1-pnpm-resume` 新建了独立 evidence 现场，没有覆盖 E4 原始 evidence。task-owned shim 只调用固定的 `pnpm-native.exe`，原样传递参数并返回原退出码：

| 文件 | bytes | SHA-256 |
| --- | ---: | --- |
| `forge-pnpm-bin/pnpm.cmd` | 101 | `57785cc51fff3a94b68815e46f48a400f1cb016f9edc82d2cb9606cbdb088bdf` |
| `r0-forge-preflight.mjs` | 942 | `0578d5b1cb708635bcefeddeb45a66d13d4c500a46ee7b68d49f4589c75de5cd` |
| `verify-state.ps1` | 4,687 | `b3ca61ae68c60b33f658a4f490db7424508c9fe707d9febd19822f54bea0100a` |
| `r1-controller.ps1` | 9,253 | `65ce91fa661ca43432d14afd8e0fff31a2127b1a8af96b375c956709ea980505` |

控制脚本只构造一次进程级 PATH：第一项是 R1 shim，第二项是固定 Node，之后原 PATH 保持原顺序；同一控制会话原计划在 R0 通过后停在 `0/1`，经本角色复核和 control 重读后，再直接让正式 wrapper 继承同一个 PATH。用户 PATH、系统 PATH、系统 pnpm 和永久环境均不在写入范围。

## 4. R0 实际失败

预期顺序是：

1. `where.exe pnpm` 得到 task-owned shim 为第一项；
2. 裸 pnpm 得到 version 12.7.0 和三个 config 结果；
3. 固定 Node 调用 Forge 实际安装的 `spawnPackageManager`，再次得到精确 version/config；
4. 复算源码、lock、node_modules、Electron dist、污染标记和零 out/staging；
5. 只有全部通过才产生 `R0_READY`。

实际失败来自控制脚本的 `Run-Captured` 函数把命令参数命名为 `$Args`。`$Args` 是 PowerShell 自动变量，函数体最终取得空数组：

- `where.exe` 实际没有收到 `pnpm` pattern，原始输出是 where 的无参数帮助；
- 四个 pnpm 调用实际没有收到 version/config 参数，原始输出都是 pnpm 的无子命令帮助；
- 固定 Node 实际没有收到预检 `.mjs` 路径和参数，进入交互等待；
- `06-forge-spawn-package-manager.log` 和 `r0-result.json` 均未生成；
- 控制会话没有输出 `R0_READY_PACKAGE_0_OF_1`。

本角色识别到该状态后只中断本任务拥有的控制会话，没有按进程名清理其他程序。由于改名后再次运行会构成同一 R0 cell 的第二次执行，本轮没有修正并重跑。

缺陷记录：

| 字段 | 内容 |
| --- | --- |
| ID | `P4-E4-R1-R0-DRIVER-ARGS-001` |
| 分类 | 任务 evidence driver 编排缺陷；不是产品缺陷 |
| 预期 | 命令参数完整传递，六项 R0 输出可验证 |
| 实际 | 参数数组与 PowerShell 自动变量冲突，R0 没有形成有效结果 |
| 影响 | 当前任务不能合法进入 package；package 预算仍未消耗 |
| 建议 | 总控若继续，应新立 R0-only 恢复任务，保留本失败 evidence，把外部 driver 参数名改为非自动变量，并从新的单一持续会话重新开始；预检全部存在前仍不得授权 package |

## 5. 失败后不变性与 warning

失败后重新复算得到：

- source copy 198/198、Electron dist 73/73、污染 marker 9/9；
- lock、Electron executable 和 pnpm native 摘要不变；
- `node_modules` 仍为 12,451 files、570,581,590 bytes；使用起点相同的 LF 算法得到 `f06ce306...00c7`，与起点一致；
- `out=false`、staging=false、transition artifacts=0；
- R1-owned process=0；
- 用户 PATH 与系统 PATH 的前后摘要相同；没有永久环境变化。

有两条任务编排 warning：

1. 初次普通权限读取虚拟 `.pytest_cache` marker 被 Windows 拒绝；随后只用提升后的只读复算确认九项全部匹配，没有改变 ACL 或内容。
2. `verify-state.ps1` 的诊断摘要使用 CRLF 连接，得到 `a2c286b5...6d30`，与起点 LF 摘要不同。文件数、总字节和所有其他清单均未变化；按起点 LF 算法重算后精确恢复 `f06ce306...00c7`，确认这是摘要换行算法差异，不是 node_modules 内容漂移。

## 6. package、R2、P1 与 P2

| 阶段 | 本轮状态 | 次数 |
| --- | --- | ---: |
| R0 | `failed`，未达到 ready marker | 1 次控制会话；不重跑 |
| package | `not_run` | 0/1 |
| R2 package 后静态门禁 | `not_run` | 0 |
| P1 packaged app.asar | `not_run` | 0/1 |
| P2 最终 `Maris.exe` | `not_run` | 0/1 |

因此没有本轮 package、app.asar、Maris.exe、production fuses、最终 resources、Host/owner/modules/recover、动态 CDP 或 Windows 事件结果；这些均不能计为通过。

## 7. 资源、隐私与 evidence

最终资源状态：

- R1 package/P1/P2 evidence files 均为 0；
- `out=false`、staging=false、transition artifacts=0；
- task-owned Node 等待进程已中断，最终 owned process=0；
- 没有创建动态端口、Electron/Maris 窗口、Tray 或隔离 profile；
- E4 和 R1 evidence 均完整保留；
- 没有启动 P4-C12、技术顾问、测试智能体、Docker/PostgreSQL、OpenClaw、微信或 DeepSeek；
- 没有读取真实账户、真实财务数据、真实 profile 或密钥，也没有修改用户/系统环境。

R1 `evidence/final-evidence.sha256` 覆盖其自身之外 14 个文件，最终复算为 14 matched、0 mismatch、0 missing，manifest SHA-256：

```text
8c4ee01f59d70400b5d2003c761ccb8236ac3a27d425f80516c12806aef941a9
```

`final-summary.json` SHA-256 为 `7609f321e28acfc2907abf8ccac65c9cabc90988c07a63b5322422ee22f03abc`；R0 `failure-summary.json` SHA-256 为 `14b02ff0698f0ccb7bbf68671040da847f84525b147f2de49e93657ae5f14c1d`。

## 8. 仓库交付与停止边界

仓库只交付：

- 本运行说明；
- `apps/desktop/b7-r1-e4-r1-source.sha256`；
- 执行智能体角色日志更新。

E4-R1 source manifest 与 E4 的 198 文件 source manifest 内容一致，复算为 198 matched、0 mismatch、0 missing，自身 SHA-256：

```text
04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1
```

产品、测试、Forge、wrapper、staging、依赖、lock、独立材料、control、overview 和其他角色文件均未由本任务修改。未执行任何 Git 写操作。

执行智能体已停止，不自动修复 driver、重跑 R0、运行 package 或创建 P4-C12。后续由头脑风暴总控复算失败 evidence，并决定是否发布新的最小 R0-only 恢复任务。
