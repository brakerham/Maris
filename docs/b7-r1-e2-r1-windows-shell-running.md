# P4-B7-R1-E2-R1 Electron 启动分层与 package hygiene 运行说明

## 1. 结论

- 任务状态：`blocked / finished`。
- 阻塞点：阶段 1 的最小隔离 fixture 在使用 Playwright 默认 Electron、且不传 `executablePath` 时，已经成功建立 Node inspector 与 renderer CDP 连接，随后 Electron GPU 子进程以 `-1073741515` 退出，Playwright 在 `_CRSession._onMessage` 抛出 `Assertion error`，Windows 同时显示 `unknown software exception (0x80000003)`。
- 该弹窗属于任务拥有的 `maris-electron-fixture: electron.exe`。任务卡把“不受控 Windows 弹窗”列为立即停止条件，因此没有执行相邻重试、app.asar、真实 EXE、package staging 或重打包。
- E2 的源码、运行说明和历史 package 证据均保留；本任务没有修改产品、package 配置、测试或依赖版本。
- 本报告是执行方阻塞证据，不是独立验收；P4-C12、测试智能体和技术顾问均未启动。

## 2. 起点与边界

| 项目 | 结果 |
| --- | --- |
| control | `2026-09-27T23:04:00+08:00`；执行智能体为 E2-R1 唯一负责人 |
| R1 起点 | 200 matched、0 mismatch、0 missing；清单 SHA-256 `b7d975664915a3aaac773dc17d0c3bed5f5fb184a85fe77aa3cceb0baf899674` |
| E2 source | 194 matched、0 mismatch、0 missing；manifest SHA-256 `d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715` |
| 起点相关进程 | Electron、Maris、Python、Pythonw 均为 0 |
| 起点构建残留 | `out=false`、`node_modules=false`、E2/E2-R1 工具目录均不存在 |
| Git | 未执行任何写操作 |
| 禁止范围 | 未修改 Python、migration、根依赖/lock、冻结、control、overview、其他角色、独立测试或 `.claude/**`；未启动 Docker/PostgreSQL、OpenClaw、微信或 DeepSeek |

## 3. 精确工具与官方资产恢复

- Node `24.21.0` 官方 ZIP SHA-256：`158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`，与官方 `SHASUMS256.txt` 匹配。
- pnpm `12.7.0` registry 包 integrity：`sha512-3p5QdoIi1oNH+1U6/SH0h6jdF02xMGXoDhBYkwcqSqYsjGJmYBpsZf17T87QE1kzLuUwA0f0IA0vUYCxQEj0aA==`，下载值与 metadata 一致。
- clean frozen install：275 packages；实际 lifecycle 只有允许的 `esbuild postinstall`。
- `pnpm-lock.yaml` 安装前后均为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- Electron `44.4.5` Windows x64 官方 ZIP：158,184,819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`；`electron.exe` file/product version 均为 `44.4.5`。
- 没有使用第三方 mirror、旧 binary、全局包、未知 cache、代理修改或安全软件例外。

工具恢复期间的非产品异常均已保留：首次 PowerShell `Invoke-WebRequest` 因当前执行沙箱 TLS authentication 失败，没有形成下载文件；经授权改用系统 `curl.exe` 访问相同官方 URL 后摘要通过。一次 pnpm 下载记录了 `openapi-fetch` 与 `chai` 低于 50 KiB/s 的速度 warning。首次 Electron 安装误用了不被当前 `install.js` 读取的 `ELECTRON_CACHE` 环境名，安装本身成功但任务 cache 中没有归档；读取本地官方安装脚本后改用其实际支持的 `electron_config_cache`，只重建任务拥有的 `node_modules/electron`，得到完整官方 ZIP 和准确摘要。

## 4. Playwright 1.63 Electron launcher 根因证据

本地已安装的 `playwright-core/lib/coreBundle.js` 显示：

1. `_electron.launch()` 总是在用户参数之前注入 `--inspect=0` 与 `--remote-debugging-port=0`。
2. 传入 `executablePath` 时，Playwright 直接使用该路径，不加载 Electron loader。
3. 不传 `executablePath` 时，Playwright 通过 `require("electron/index.js")` 解析项目 Electron，并在参数最前加入 `-r playwright-core/lib/server/electron/loader.js`。
4. Windows 路线把 command 与参数拼为 shell command，实际子进程参数数组为空。
5. loader 从 `process.argv` 删除 `--remote-debugging-port=0`，再用 Electron `app.commandLine.appendSwitch()` 写入 Playwright Chromium switches，并接管 Electron ready 时序。

这解释了 E2 的启动模式混用：显式 `executablePath` 会绕过 Playwright 为 Electron application 设计的 loader；最终 fused `Maris.exe` 又禁止 Node CLI inspect，因此本来就不能由 `_electron.launch()` 驱动。本任务按冻结要求改用“不传 `executablePath`”的最小 fixture 先验证默认路线。

## 5. Fuse 核对

冻结 Forge 配置和 E2 最后成功 package 的 fuse 状态一致：

| Fuse | 值 |
| --- | --- |
| RunAsNode | Disabled |
| EnableCookieEncryption | Enabled |
| EnableNodeOptionsEnvironmentVariable | Disabled |
| EnableNodeCliInspectArguments | Disabled |
| EnableEmbeddedAsarIntegrityValidation | Enabled |
| OnlyLoadAppFromAsar | Enabled |

本任务没有生成新 package，也没有修改、临时开启或绕过任何 production fuse。

## 6. 最小 fixture 检查点

fixture 只创建一个隐藏的 sandboxed BrowserWindow，设置绝对隔离 userData，并在 Electron ready 前禁用硬件加速。driver 使用 Playwright `_electron.launch()`，不传 `executablePath`，参数仅为 `--disable-gpu` 和 fixture 目录，并启用 `DEBUG=pw:browser`。fixture 不加载 Maris 产品代码、Host、sidecar 或真实 profile。

脱敏事件顺序：

1. Playwright 启动项目 Electron，并加载其 Electron loader；参数含 `--inspect=0`、`--remote-debugging-port=0` 和 `--disable-gpu`。
2. Electron 主进程启动；Node debugger 在动态 loopback endpoint 监听并成功 attached。
3. Chromium DevTools 在动态 loopback endpoint 监听；Playwright 成功建立 renderer CDP 连接。
4. GPU 子进程随后报告 `GPU process exited unexpectedly: exit_code=-1073741515`；隔离 profile 的 DawnGraphite cache 同时记录一次 Windows sharing violation `0x20`。
5. Playwright 请求终止主进程，系统 `taskkill` 返回 access denied；Playwright `_CRSession._onMessage` 随即抛出 `Assertion error`。
6. Windows 显示标题为 `maris-electron-fixture: electron.exe - 应用程序错误` 的不受控弹窗，异常为 `0x80000003`，用户截图位置为 `0x00007FF634E1BD39`。

原始 stderr 只保存在任务工具目录中用于本检查点，SHA-256 为 `0191e8d98a6250307d325eeb419a59d749dd6b9c9d22a53be4b31520a35efb78`；stdout 为空，SHA-256 为 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

Playwright driver 退出 1。首次收口检查观察到 3 个相关进程；主进程退出后仍有 2 个项目内 `node_modules/electron/dist/electron.exe` 子进程存活。执行方按可执行路径精确终止这 2 个 owned 子进程，最终为 0。没有终止系统或其他应用的 Electron 进程。

## 7. 停止条件与未验证范围

不受控 Windows 弹窗直接命中任务卡 P0 停止条件。虽然最小 fixture 提供了比 E2 更精确的新证据，但该条件要求立即停止，因此没有做相邻 checkpoint，也没有尝试改 fuse、改 Electron/Playwright 版本、patch 第三方包、私有 fork或系统设置。

以下范围均为 `not_run`：

- app.asar Playwright E2E；
- 最终 `Maris.exe` CDP 黑盒 smoke；
- package staging/allowlist 实现与对应 unit test；
- 本轮 OpenAPI、TypeScript、lint、Vitest；
- 本轮 Forge package、fuse 读取和 package hygiene 扫描；
- startup、owner、modules、recover、统一自动退出和 sidecar cleanup 的真实 package 门禁。

E2 的 OpenAPI、TypeScript、lint、22 项 Vitest、55 项 Python、managed sidecar smoke 和最后一次 package 结果只作为历史输入引用，没有冒充本轮实际运行。

## 8. 变更与 source manifest

- 产品、配置、脚本、测试和依赖变化：0。
- 本任务只新增本运行说明、R1 source manifest，并更新执行智能体角色日志。
- [R1 source manifest](../apps/desktop/b7-r1-e2-r1-source.sha256)：194 entries；内容与 E2 source manifest 完全相同，清理后已完成最终复算。
- manifest SHA-256：`d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715`。
- 最终复算：194 matched、0 mismatch、0 missing。相对 200 文件起点只有允许的 executor 角色日志发生变化，0 missing；新增文件只有本报告和 R1 manifest。
- manifest 排除自身、角色日志、本报告、`node_modules`、任务工具/cache、fixture、profile、trace、package/out、临时日志和 `.claude/**`。

## 9. 资源收口

执行方已删除任务拥有的 `node_modules`、`.b7-e2-r1-tools`、fixture、profile、官方下载/cache、临时日志以及可能的 package/out/test-results；预存根 `.pnpm-store` 保持不变。最终 Electron、Maris、Python、Pythonw 相关进程为 0；`node_modules=false`、任务工具目录=false、out=false、test-results=false。异常弹窗对应的 owned Electron 子进程已经全部终止，没有窗口或 Tray 残留。

执行智能体已停止实现，等待头脑风暴总控核对本机 Electron 44 / Playwright 1.63 / GPU 子进程的最小复现并裁定新的恢复路径。
