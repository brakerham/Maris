# P4-B7-R1-E5-LOCALZIP 本地官方 ZIP 与最终产品门禁运行说明

## 结论

- 任务：`P4-B7-R1-E5-LOCALZIP`
- 执行方状态：`review / finished`
- package：`1/1`，exit 0，没有重跑
- 最终 EXE：`1/1`，exit 0，没有重跑
- 结果：本地官方 Electron ZIP 的 fail-closed 校验、Forge `electronZipDir` 接线、定向自测、真实 package、静态产物和最终 EXE 黑盒门禁全部通过。
- 边界：这是执行方开发与产品门禁证据，不宣布 P4-B complete，不启动 P4-C12、测试智能体或高保真前端。

总控接受了 E5-PKG-FINAL 已建立的普通 node_modules、离线安装、Electron dist、TypeScript 和旧 22 项定向测试。本任务没有重装依赖、重建 cache、联网补装、修改代理/TUN/系统配置，也没有重复旧 22 项模块测试。旧 package 的 `fetch failed` 仍没有可验证 URL/代理根因；本轮只通过明确的本地 ZIP 路径关闭构建缺口。

## 起点与复用环境

- 最新 control：`2026-10-01T11:49:13+08:00`，SHA-256 `e76637cf255e17c88882dfe38428e3d76c1f1bf7f89db020abbbbfed5ee35a2d`。
- 起点 snapshot：270/270 matched，0 missing/mismatch；manifest SHA-256 `d5eda74cd1e1eb25f2daf774a8a2aae4604380479a84e2e2704bf40dbccc4edf`。
- Git index staged paths：起点、package 前、最终 EXE 前和收口均为 0。
- 复用根：`C:\MarisE5Final\E5-PKG-FINAL-20260929-1732`。
- 旧 evidence：58/58 matched，manifest SHA-256 `072127d72a6d444452b1bbb52f72a33613387954aa8e561c1fa7506b83d6ec4a`。
- node_modules：普通目录；12,443 files、570,582,052 bytes；逐行复算与冻结 manifest 0 差异。
- Electron dist：73 files、385,243,397 bytes；逐行复算 0 差异。
- lock SHA-256：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- 官方 ZIP：`electron-v44.4.5-win32-x64.zip`，158,184,819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- 起点任务根进程和监听均为 0；旧 evidence、旧 manifest、旧依赖和旧 profile 全部保持只读。

新 evidence 按 create-new 建立在 `localzip-resume-1`。同步产品文件之前保存了 Forge 与 wrapper 原件及普通摘要；只有本任务授权的五个构建/测试文件同步到隔离 workspace。

## 实现

### 生产校验入口

新增 `verify-electron-zip.mjs` 和声明文件，固定合同如下：

| 字段 | 固定值 |
| --- | --- |
| version | `44.4.5` |
| platform | `win32` |
| arch | `x64` |
| filename | `electron-v44.4.5-win32-x64.zip` |
| bytes | `158184819` |
| SHA-256 | `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |

生产入口区分“变量未设置”和“设置为无效值”。未设置时返回原常规构建路径；一旦显式设置，空值、首尾空白、NUL、非绝对路径、缺失/不可读目录、非普通目录、固定文件缺失、非普通文件、长度错误或 SHA-256 错误都会明确失败。摘要使用 Node 标准库流式计算，production 期望值不能由环境变量覆盖；测试只能通过函数参数注入小型 fixture 合同。

### Forge 与 wrapper

- Forge 用 `MARIS_ELECTRON_ZIP_DIR` 设置 `packagerConfig.electronZipDir`。
- 本地模式存在时不设置 `download`，因此不依赖 `download.cacheRoot`；变量未设置时保留既有 `MARIS_ELECTRON_CACHE` 行为。
- wrapper 在 `stagePythonResources()` 和 Forge spawn 之前完成完整 ZIP 验证；失败不会进入 staging 或网络 fallback。
- Forge 子进程显式继承当前 build-process environment。
- 没有加入 `unsafelyDisableChecksums`、第三方镜像、inspect/no-sandbox、版本 fallback 或新依赖。

实际安装的 `@electron/packager` 源码和类型已只读核对：`electronZipDir` 分支直接解析固定文件名并返回本地 ZIP；只有未设置该选项时才调用下载逻辑。生产 helper 对真实 ZIP 的验证退出 0；Forge 自身 config loader 得到完全相同的目录，最终 `download` 未设置。

## package 前验证

| 检查 | 结果 |
| --- | --- |
| Node 脚本语法 | exit 0 |
| TypeScript | 首次 4 个 TS18048；修正新测试的可选字段收窄后复验 exit 0 |
| lint | exit 0，`desktop lint checks passed` |
| ZIP + package-resources + toolchain | 3 files、30 passed、0 failed/skip |
| 真实 ZIP production helper | exit 0，长度/摘要/版本/平台/架构全匹配 |
| Forge 实际 config loader | `electronZipDir` 匹配，`download` 未设置 |
| node_modules / dist / lock | 12,443 / 73 / 固定 lock，0 drift |
| C 盘 workspace source | 266 基线中 264 unchanged、仅 Forge/wrapper 2 changed；另 3 个授权文件新增 |
| package 前资源 | out/staging/transition/task processes 均 0 |

没有运行完整 desktop、Python、独立测试或未修改的 22 项模块测试。

## 唯一 package 1/1

- 开始：`2026-10-01T12:40:48.1205062+08:00`
- 结束：`2026-10-01T12:41:00.8217153+08:00`
- 时长：12,701 ms
- 退出码：0
- 工具：task-local Node 24.21.0、pnpm 12.7.0 和 PATH。
- build-only environment：`MARIS_ELECTRON_ZIP_DIR` 指向官方 ZIP 所在目录；`DEBUG=electron-packager,@electron/get:*`。

原始 stdout 第一条是生产 `electron_zip_verified` 记录。Packager DEBUG 的最终选项包含 `electronZipDir`、`electronVersion=44.4.5`、`platform=win32`、`arch=x64`，不含 `download`；日志明确记录从固定本地 ZIP 解压。`Copying files`、native dependencies 和 finalize 全部通过，旧任务的 fetch failure 没有出现。

## 静态产物

| 对象 | 结果 |
| --- | --- |
| out | 140 files、386,491,523 bytes |
| `Maris.exe` | 246,032,896 bytes；SHA-256 `f5cf7ad3b4d89a02cca925152ec8d7b5554ccba6ebff025bf04eb24195405641` |
| `resources/app.asar` | 758,341 bytes；SHA-256 `bcdf6f889a5be95d7270fb249db8eff45b1421a5fdd7879d2342cb333d7f1274` |
| production fuses | V1；前六项 48/49/48/48/49/49 全匹配 |
| Python resources | 67/67；missing/extra/mismatch/forbidden 均 0 |
| app.asar | 18 listed entries；11 files、0 links、0 unpacked |
| Profile 字面量 | canonical `daily_finance.assistant@1` 命中 2；两个旧/错误别名均 0 |
| 污染扫描 | 个人路径、秘密/凭据样式、任务 evidence、pyc/pyo/pyd、egg-info、测试/cache 均 0 |
| staging | `.maris-staging` 不存在，transition artifact 0 |

package 后再次证明 lock、12,443 项 node_modules、73 项 dist、269 项隔离 workspace source 和产物无漂移，任务进程、监听和 Git staged paths 为 0。

## 最终 EXE 1/1

使用总控此前接受的 640 行 Node runner 作为基础，只更新本次任务根、manifest/产物摘要，并收紧冻结断言：modules 必须恰好一项、为 enabled `daily_finance`，其 `profile_ids` 必须包含 `daily_finance.assistant@1`；runtime/recover 必须为 `mode=managed`。任务 runner SHA-256 为 `8839f9d324cd7eca1243a09fe69ce0a5829406994e6c9384cf28bc4f580f1e30`，语法 exit 0；direct spawn、connectOverCDP、recover 调用点各 1，Playwright `_electron` 0。

- 动态预算：1/1，无重跑。
- 启动：固定 `Maris.exe`，Node `spawn()`、`shell:false`，仅两个 remote-debugging 参数。
- profile/数据：全新隔离 profile、虚拟数据库、随机 owner marker、项目 Python 3.14.7、动态 loopback 端口。
- 开始：`2026-10-01T12:49:08.814+08:00`。
- 结束：`2026-10-01T12:49:43.610+08:00`。
- 时长：34,796 ms，低于 120 秒硬上限。
- 退出：产品现有 30 秒 bounded shutdown；exit 0、signal null、无超时、无 forced cleanup。

动态结果：

| 门禁 | 结果 |
| --- | --- |
| 直接根与 owned set | direct spawn PID/executable/creation window 精确匹配；owned count 11 |
| CDP | 动态非零端口、仅 IPv4 loopback、DevToolsActivePort 属于本运行 |
| 窗口 | 主窗口 `Maris` 1 个、毛毛窗口 1 个；用户也实际看到前端弹出 |
| bridge | 主 bridge 和毛毛 bridge 均冻结、键集合精确匹配 |
| renderer 隔离 | `require/process/Buffer/global/module/exports` 和内部文件名全不可用；越权 bridge 不存在 |
| runtime before | online / managed / authenticated / errorCode null |
| modules before | 唯一 enabled `daily_finance`；`profile_ids=[daily_finance.assistant@1]` |
| 毛毛 before | state idle、appearanceId daily_finance |
| openMain | accepted true，未新增窗口 |
| recover | 精确 1 次；online / managed / authenticated / errorCode null |
| runtime/modules/毛毛 after | 与恢复前合同一致 |
| 隐私 | DOM/storage/bridge/log 未命中秘密、个人路径或运行身份；storage keys 为空 |
| console/page/crash | 0 / 0 / 0 |
| Windows Application/Code Integrity | 0 / 0；forbidden 0 |
| owner/database | 隔离 owner session 与虚拟数据库均形成 |
| 自然退出与收口 | exit 0；产品/sidecar/监听/窗口/Tray 推断均 0 |
| 产物前后 | EXE、app.asar、269 source、73 dist、67 resources、140 out、fuses 全匹配 |

stderr 只包含预期的受限 CDP 调试端点文本，因此通用路径/运行身份检测为 true；它没有秘密，原文只保存在外部 evidence，runner 的 logs/privacy gate 均为 true。

## Warning、失败与 skip

1. 新测试首次 TypeScript 因 Forge 类型允许 `packagerConfig` 为空产生 4 个 TS18048。只增加测试内显式存在断言与非空引用后，TypeScript 复验通过；产品逻辑没有改变。
2. package 前 source evidence v1 错把旧最终 manifest 当作 C workspace 内文件；v2 又使用了包含旧任务最终执行日志的仓库 manifest，因此分别保留为编排 warning。v3 使用旧 evidence 的 `workspace-copy.sha256` 后准确得到 264 unchanged、2 authorized changed、0 missing。
3. 只读 Git 状态命令多次提示无法读取用户级 `.config/git/ignore`；命令仍返回 staged paths 0，未改变 Git 状态。
4. 最终 runner 的 raw result schema/task 字段沿用已接受的 `P4-B7-R1-E5-FINAL` runner 元数据；本轮 prelaunch、runner map 和 closeout 明确归属 `P4-B7-R1-E5-LOCALZIP`。这是派生证据标签 warning，不改变唯一动态运行或产品结果，没有重启产品。

最终 failed=0、skip=0。以上三项 package 前问题和一项离线标签问题均有原始记录；没有隐藏、覆盖或把它们写成产品失败。

## 文件边界、证据和停止状态

仓库相对 270 项固定起点只有 3 个允许的既有文件变化：Forge、package wrapper、本执行角色日志；新增 ZIP helper、声明、专属测试、本运行说明和 source manifest。其他起点文件无 missing/mismatch；`.claude/` 与 `.pnpm-store/` 是任务前已有未跟踪目录，保持原样。Git staged paths 最终仍为 0，没有执行任何 Git 写操作。

仓库 source manifest 为 `apps/desktop/b7-r1-e5-localzip-source.sha256`，排除自身以避免自引用。外部 `localzip-resume-1/evidence-manifest.sha256` 逐项记录其余 evidence 的相对路径、bytes 和 SHA-256；`repository-delivery.sha256` 记录全部仓库交付。最终条目数、各文件摘要和可复算总摘要以这些不可变 manifest 及交付消息为准。

没有启动 P4-C12、测试智能体、技术顾问、高保真前端开发、Docker、OpenClaw、微信或 DeepSeek；没有读取真实密钥、真实账户或真实个人数据。执行智能体在 `review / finished` 停止，等待总控复算和决定是否派发 P4-C12。
