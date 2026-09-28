# P4-B7-R1-E4 package、app.asar 与最终 EXE 恢复门禁运行说明

## 1. 结论

- 任务状态：`blocked / finished`。
- 阶段 A 全部通过：OpenAPI generated drift、TypeScript、lint、desktop 完整 Vitest、H1 package resource/toolchain 专项、六文件 Python 定向、Python compile 与 `pip check` 均为退出码 0。
- 阶段 B 的九类虚拟污染前置已建立并在 package 时保持存在。
- 唯一一次正式 package attempt 1/1 失败。Forge 在 `Checking package manager version` 阶段运行裸 `pnpm config get hoist-pattern` 时解析到失效的用户级 pnpm shim，尚未进入 Packager、Vite build、app.asar 或 fuse 阶段。
- package 失败后没有重跑。`out` 不存在，wrapper 的 `finally` 已清除 `.maris-staging`，lock 未变，任务进程为 0。
- P1 packaged app.asar 与 P2 最终 `Maris.exe` 均为 `not_run`。没有把 E2/E3 的历史通过写成本轮结果，也没有宣称 package、resources、fuses、app.asar、最终 EXE 或 P4-B 已通过。

## 2. 起点门禁与边界

| 门禁 | 结果 |
| --- | --- |
| 最新 control | `2026-09-28T12:30:00+08:00`；执行智能体为 E4 唯一负责人，技术顾问、测试智能体和 P4-C12 停止 |
| E4 起点 | 215 matched、0 mismatch、0 missing；manifest SHA-256 `6b51e836d87bf94f10a5bb0daeedee05e8c2c26d44c542f65cac6490162cafcc` |
| E3 source | 198 matched、0 mismatch、0 missing；manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| E3 报告 | SHA-256 `f03fc8304bdfa0413a4bba5a3737b99082ebdd137e39c1edf7378f0d5ddec1cb` |
| E3 总控核对 | SHA-256 `4b65296e2ebbcaee9babda4b84fcd25714ecdb184e0d304e776a3c9180561d80` |
| E3 外部证据 | 39 matched、0 mismatch、0 missing；manifest SHA-256 `4b21b569e21a529a4743c53e115d1f035a6c51e75bd916948a2d37ccaac85b46` |
| workspace lock | SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| 旧任务进程 | Electron、Maris、项目 sidecar 相关进程为 0 |
| 新任务根 | `C:\MarisE4\E4-20260928-1255`；创建前不存在，短 ASCII、无空格 |
| Git | 未执行任何 Git 写操作 |

E3 原始现场保持只读。E4 只从中复制并重新核验官方 Node/Electron/pnpm 归档及 frozen package cache，没有修改、补写或清理 E3，也没有复用 E3 package/out、fixture 结果或产品二进制。

仓库内没有修改产品、Forge 配置、staging 脚本、测试、依赖、lock、migration、Python 业务代码、独立测试、矩阵、既有报告、冻结文档、control、overview、其他角色或 `.claude/**`。

## 3. C 盘固定源码与工具

按 E3 source manifest 的 198 个相对路径逐文件复制到 C 盘同形 workspace。每个目标文件的路径、字节数和 SHA-256 均与仓库源文件匹配；没有复制 `.git`、`.claude`、仓库 store、`node_modules`、旧 out、`.vite`、`.maris-staging`、测试结果、日志或 profile。

带 bytes 的 C 盘 source-copy manifest 含 198 entries，SHA-256 为：

```text
4a4a73508d400ddb557de2a3235d6c6cf39c4fecdac01c854c2aea0dc9656ce2
```

固定工具与内容核验：

| 项目 | 结果 |
| --- | --- |
| Node | 24.21.0；官方 ZIP SHA-256 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541` |
| pnpm | 12.7.0；官方 registry tarball SHA-256 `1a7fe4b36abead79ee13e2f2c2089ddd37fee016179b9fe56a85a44ef72aaf7f` |
| Electron archive | 44.4.5 Windows x64，158,184,819 bytes；SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |
| clean frozen install | 275 packages；274 resolved/reused、downloaded 0；退出 0 |
| Electron package / Playwright | 44.4.5 / 1.63.0 |
| Electron dist | 73 files；manifest SHA-256 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`，与 E3 完全相同 |
| `electron.exe` | 246,032,896 bytes；SHA-256 `bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e` |
| lock | 安装前、安装后、阶段 A 后和 package 失败后均为冻结摘要 |

工具准备有一条 warning：官方 pnpm registry tarball 没有预期的根级 `pnpm-native.exe`。第一次版本探针因此失败；随后改用包内官方 `bin/pnpm.mjs`，它从 pnpm 官方发布通道取得同版本 Windows binary并确认版本 12.7.0。该问题发生在 install 前，没有改变源码或 lock。

## 4. 阶段 A：有限静态与执行方门禁

| 组别 | 本轮实际结果 |
| --- | --- |
| OpenAPI generated drift | 通过；重新导出的 schema 和 TypeScript 与 checked-in artifacts 相同 |
| TypeScript | `tsc --noEmit` 退出 0 |
| desktop lint | 退出 0；`desktop lint checks passed` |
| desktop 完整 Vitest | 12 files、36 passed、0 failed、0 skipped |
| H1 package resource + toolchain | 2 files、16 passed、0 failed、0 skipped |
| Python 定向 | desktop runtime、sidecar、production、auth、registry、Host API 六文件；55 passed、0 failed、0 skipped |
| Python compile | `src/wife_system/api` compile 退出 0 |
| pip check | `No broken requirements found.` |

Python 3.14.7 定向回归只有一条既有 Starlette/AnyIO `BlockingPortal` alias deprecation warning，没有产品 warning、skip 或 xfail。

证据编排发生一次允许的基础设施修正：第一次 `compileall -q` 实际退出 0且输出为空，通用 helper 因空 pipeline 没有创建日志文件，导致摘要步骤报错并使 pip check 尚未运行。保留前六组原始证据后，只将 evidence helper 改为即使输出为空也创建零字节日志；随后重跑 compile 并首次运行 pip check。没有修改产品、测试、参数语义，也没有重跑前六组。

## 5. 阶段 B 污染前置

在 C 盘源码副本中创建 9 个纯虚拟、不可执行、不含个人数据或凭据样式的 marker，覆盖：

- `src/wife_system/**/__pycache__/*.pyc`；
- `src/**/*.pyo`；
- `.egg-info/PKG-INFO`；
- tests；
- `.pytest_cache`；
- build；
- dist；
- scratch；
- allowlist 外未知扩展。

九项在 package 启动前均存在，manifest SHA-256 为：

```text
b239e272480bdb33b6aa23f380c1a1f1e0c36f7590bc9784e3d32d40799605f8
```

package 失败后九项仍保留在 C 盘现场供总控复核。没有通过删除污染再打包。

## 6. 唯一 package 失败

| 项目 | 结果 |
| --- | --- |
| attempt | 1/1；已消耗，不重跑 |
| 本地时间窗 | `2026-09-28T14:02:31.9158526+08:00` 至 `2026-09-28T14:02:45.6141289+08:00` |
| 入口 | 正式 `apps/desktop/scripts/package-desktop.mjs` wrapper；没有直接绕过 wrapper 调 Forge |
| 预期顺序 | `stagePythonResources → Forge package → finally cleanupPythonResources` |
| 实际停止点 | Forge `Checking package manager version` |
| 失败命令类别 | Forge 内部执行裸 `pnpm config get hoist-pattern` |
| 失败机制 | 裸 `pnpm` 解析到用户级 pnpm shim；shim 内部目标命令不能由 `cmd.exe` 识别 |
| package exit | 1 |
| raw log SHA-256 | `e9c841c4d23cbf93a41e62680aaaf493db9ff2764323b4fe41155680afb3b0d6` |
| out | 不存在；没有产出 app.asar 或 Maris.exe |
| staging | `.maris-staging` 不存在；temp/backup/lock transition artifacts 为 0 |
| lock | 未变化 |
| owned process | 0 |

原始失败日志含用户级工具路径，只保留在 C 盘受限 evidence。仓库报告只保留上面的路径类别和错误机制。

缺陷/阻塞记录：

| 字段 | 内容 |
| --- | --- |
| ID | `P4-E4-PACKAGE-PNPM-PATH-001` |
| 级别 | P0；阻断 package、P1 和 P2 |
| 最小复现 | 在新的 C 盘固定源码与 clean frozen install 上，通过任务内绝对 pnpm 12.7.0 入口调用正式 package wrapper |
| 预期 | Forge 的 package-manager check 使用同一固定 pnpm 12.7.0，随后进入唯一 package |
| 实际 | Forge 子进程的裸 `pnpm` 命中失效用户级 shim，在 package-manager check 退出 1 |
| 影响范围 | package 工具编排；尚无证据表明产品、Forge 配置、staging 内容或业务代码本身失败 |
| 最小建议 | 新任务只固定任务专属 pnpm 命令解析/PATH，并重新授予一次 package 预算；优先零仓库产品变更。若需持久修复，只定向评审 `apps/desktop/scripts/package-desktop.mjs` 的子进程环境传播，不修改依赖、lock、测试或系统级 pnpm |

任务卡明确禁止用第二次 package 覆盖第一次失败，因此本轮没有修 PATH 后重跑。

## 7. package 后门禁、P1 与 P2

以下 package 后门禁均为 `not_run`，不能计为通过：

- 最终 package 内容拓扑；
- app.asar 完整列举与 main/preload/renderer 入口；
- production fuses；
- packaged Python 与 H1 staging manifest 的路径、字节、摘要比较；
- migration、sidecar 和 production factory 必需文件；
- 最终 resources 污染、个人路径、凭据样式、更新器 URL、旧依赖名与 task cache 扫描；
- Maris.exe、app.asar 和 packaged resources 摘要。

P1 packaged app.asar：`not_run`。没有启动 Playwright/Electron、Host、owner 会话、modules 或 recover。

P2 最终 Maris.exe：`not_run`。没有启动 EXE、动态 CDP、renderer 黑盒检查或自动退出路径。真实 Tray 菜单点击继续保留给未来 P4-C12 人工门禁。

没有 Windows 动态时间窗，因此没有本轮 P1/P2 Application/Code Integrity 事件；这应解释为 `not_run`，不能解释为事件门禁通过。

## 8. 资源、进程与隐私收口

最终状态：

- 任务根 `C:\MarisE4\E4-20260928-1255` 完整保留；
- `out=false`；
- `.maris-staging=false`，transition artifacts 为 0；
- P1 evidence files = 0，P2 evidence files = 0；
- E4 任务根下 Electron、Maris、Node、Python 等 owned process = 0；
- package 未进入产品启动阶段，任务自有动态端口、窗口、Tray 和隔离 profile 均未创建，最终计数为 0；
- 九个虚拟污染 marker 保留 9/9；
- source、node_modules、官方 cache、日志和 manifests 保留，等待总控只读复算；
- 没有启动 Docker、PostgreSQL、OpenClaw、微信、DeepSeek、技术顾问、测试智能体或 P4-C12；
- 没有读取真实 AppData、真实账户、凭据、真实财务数据或个人数据库。

C 盘 `evidence/final-evidence.sha256` 覆盖其自身以外的 26 个 evidence 文件，manifest SHA-256 为：

```text
5958703ccea01cd0b8ef3bd72b681dfbdb7b5b398c7b8c7bc5ee7cd2fb1ba2d1
```

最终逐项复算为 26 matched、0 mismatch、0 missing，且同时核对清单中的文件字节数。

`final-summary.json` SHA-256 为 `a98c72add2372fa9369cb2b9a3611a6699deabc9ca2cf0e70b419537ffb31c3c`。

## 9. 仓库交付与解释边界

仓库只交付：

- 本运行说明；
- `apps/desktop/b7-r1-e4-source.sha256`；
- 执行智能体角色日志更新。

[E4 source manifest](../apps/desktop/b7-r1-e4-source.sha256)严格复用 E3 的 198 个 source 路径，最终为 198 matched、0 mismatch、0 missing；内容与 E3 manifest 逐字节相同，自身 SHA-256 为：

```text
04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1
```

最终只读边界审计相对 215 文件起点为 214 unchanged、1 changed、0 missing；唯一 changed 是授权更新的 `docs/coordination/agents/executor.md`，本运行说明和 E4 source manifest 是任务允许的两个新增文件。`git status` 还显示任务开始前已有且本轮未触碰的未跟踪 `.claude/` 与 `.pnpm-store/`。未执行任何 Git 写操作；`git diff --check` 退出 0。只读 Git 检查产生两条环境 warning：用户级 ignore 文件不可访问，以及 Git 提示未来可能把角色日志的 LF 转为 CRLF；两者均未改变仓库文件、测试结果或上述边界结论。三个授权交付文件的脱敏关键字扫描与行尾空白扫描均为 0 命中。

本轮证明固定源码、固定依赖、Electron dist 和阶段 A 在新的 C 盘副本稳定；也证明 H1 wrapper 在 Forge 早期失败后能通过 `finally` 收口 staging。它没有证明 Forge package、H1 最终 resources hygiene、production fuses、app.asar 或最终 EXE。

执行智能体已停止，不自动创建返修、技术评审或 P4-C12。下一步应由头脑风暴总控核对失败证据，并在保持产品、测试和 lock 不变的前提下决定是否发布最小 pnpm command-resolution 恢复任务。
