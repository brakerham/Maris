# P4-B7-R1-E2 Electron 下载恢复与真实 Host 组合运行说明

## 1. 结论

- 任务状态：`blocked / finished`。
- 已完成：双重起点门禁、冻结工具恢复、clean frozen install、Electron 官方归档校验、静态门禁、desktop core readiness、managed sidecar、真实 owner/modules 组合、Python smoke、执行方回归和 Forge package。
- 阻塞门禁：最终 `app.asar` 的 Playwright 启动连续两个检查点都在 `electron.launch` 阶段产生 `Assertion error`，随后目标进程崩溃；第二次参数次序修正没有产生新的有效诊断。按任务卡“同一问题连续两个检查点没有有效新输出”停止。
- 真实 `Maris.exe`：`not_run`。任务卡要求任一 app.asar E2E 失败即停止，且不得用 app.asar 代替 EXE，因此没有继续启动真实 EXE。
- P4-C12：未启动。本报告是执行方证据，不是独立验收或项目 `complete`。

## 2. 固定输入与边界

| 项目 | 结果 |
| --- | --- |
| 最新 control | `2026-09-27T21:53:00+08:00`；执行智能体为 E2 唯一负责人 |
| E2 起点 | 192 matched、0 mismatch、0 missing；清单 SHA-256 `6537cc6c7257f793915f0477e0592b47b16e0dae970fc9da61ff3836f67239b6` |
| E1 source | 186 matched、0 mismatch、0 missing；清单 SHA-256 `fd40e4b2d609b998c255c5a33bb172d53d81a043c41c98fc91f01cd5c5afd5fe` |
| Git | 未执行任何写操作 |
| 独立测试 | 未读取、修改或运行 `tests/independent/**` |
| 外部排除范围 | 未启动 Docker/PostgreSQL、OpenClaw、微信或 DeepSeek；未修改 TUN、系统代理、全局 npm/Git、系统 PATH 或安全软件 |
| 数据 | 只使用隔离 profile、随机秘密和虚拟 owner；未读取真实密钥或个人数据 |

## 3. 工具、安装与官方 Electron

- Node `24.21.0` 官方 ZIP SHA-256：`158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`，与官方 SHASUMS 匹配。
- pnpm `12.7.0`：registry tarball 的 SHA-512 integrity 与 metadata 匹配。
- clean frozen install：从无根/desktop `node_modules` 的状态安装 275 packages；观察到的 lifecycle 只有允许的 `esbuild postinstall`。
- `pnpm-lock.yaml` 安装前、安装后和最终清理后 SHA-256 均为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- Electron `44.4.5` Windows x64 官方 ZIP：158,184,819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`，与冻结值匹配。
- `node_modules/electron/dist/electron.exe` 的 Windows file/product version 均为 `44.4.5`。未使用第三方 mirror、旧 binary 或未验证缓存。

## 4. 实现结果

### Python Host

- 通用 `/readyz` 保留 provider readiness，provider 未配置时继续 fail closed。
- 新增 `/api/v1/desktop/readyz`，只在 managed profile、正确 startup nonce、数据库、Alembic head 和非空 compiled module registry 均满足时返回 ready。
- `/healthz` 只表示进程存活。
- managed sidecar 只从继承环境读取 nonce 和秘密；argv 不含秘密；stdout 机器握手只包含协议、instance、loopback port 和 nonce digest；stdin 支持 bounded shutdown。

### Electron main

- `BackendSupervisor` 使用 instance、nonce digest、verified port 和 child handle 识别 ownership；实现 start/recover single-flight、ready 失败清理、恢复预算/退避、健康循环、幂等 bounded stop，并且 external mode 不终止外部进程。
- `OwnerSecretStore`、`OwnerAuthClient` 和 `LocalOwnerSession` 实现首次本地 owner、恢复、refresh single-flight、revoke/repair；access token 只留在 main 内存。
- `HostClient` 使用严格 response schema，401 只 refresh/retry 一次，只向 renderer 暴露稳定错误码。
- `DesktopCompositionRoot` 只创建一套 supervisor、secret store、owner session、Host client 和 runtime publisher；模块列表为 Host 与 compiled registry 的交集。
- IPC 不再返回固定 `stopped`/空模块；preload/renderer 合同不包含 token、nonce、PID、port、路径、HTTP client、Node 或文件系统能力。
- Tray quit、app quit 与 Windows session end 进入同一 bounded shutdown；隐藏窗口不停止 Host。
- E2E profile 在创建 store 前调用 `app.setPath("userData", isolatedProfile)`；E2E 启用硬件加速禁用和普通 companion fallback，避免读取真实 AppData profile。

## 5. 执行方验证

| 组别 | 结果 |
| --- | --- |
| OpenAPI generated drift | 通过 |
| TypeScript | 通过 |
| desktop lint | 通过 |
| 最终 Vitest | 11 files、22 passed、0 failed、0 skipped |
| Python compile | 通过 |
| Python 定向 Host 回归 | 55 passed、0 failed、0 skipped |
| managed sidecar smoke | handshake、nonce digest、healthz、desktop ready、通用 readyz 503、owner initialize/login、`daily_finance` modules、stdin stop 与端口关闭均通过 |

Python 回归唯一 warning 是既有 Starlette `BlockingPortal` alias deprecation。最终静态复跑前，根脚本内部调用工作区 pnpm shim 时出现一次命令层错误：`.pnpm-store` link 中的 pnpm 路径未被 `cmd.exe` 识别；随后使用同一已校验 pnpm 12.7.0 的绝对入口直接运行四个 desktop scripts，全部通过。该错误不是产品断言失败，也没有改写 lock。

## 6. Forge package 证据

- 第一次 package 的 Vite targets 均构建成功，但 Packager 默认用户 cache 目录被工作区权限以 `EPERM` 拒绝。随后按 Packager 20 的官方 `download.cacheRoot` 接口指向任务内、已验证官方 Electron cache，第二次 package 成功。
- 最后一次成功 package：
  - `Maris.exe`：246,032,896 bytes，SHA-256 `149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199`。
  - `app.asar`：758,263 bytes，SHA-256 `c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6`。
- Fuses：RunAsNode、NodeOptions environment 和 Node CLI inspect 均 Disabled；CookieEncryption、EmbeddedAsarIntegrityValidation 和 OnlyLoadAppFromAsar 均 Enabled。
- resources 包含 `alembic.ini`、全部 migrations 和 `src/wife_system/api/desktop_sidecar.py`。
- 最终 ASAR 解包为 11 files。对 ASAR 与 resources 的个人路径、私钥、credential-like literal、签名 URL、更新器 URL、旧六类脆弱依赖和任务 cache 路径扫描均为 0 命中。
- 最终 package resources 同时发现 11 个 Python `.pyc` 和 6 个 `wife_system.egg-info` 文件。这发生在 Python smoke 之后的重打包，纠正了较早“76 resources、无 bytecode”的阶段性记录。因为 E2E 已触发强制停止，没有继续修改 package 规则或第三次打包；该问题作为额外 package hygiene 缺口保留。

## 7. app.asar E2E 阻塞证据

1. 首次 Playwright 启动报告 `Target crashed`。只读直接诊断发现两项具体问题：旧 CLI 参数位置使 Electron 继续读取外部 AppData profile并触发 `secure_storage_corrupt`；GPU 子进程以 `-1073741515` 反复退出，随后 Electron 报 GPU process unusable。用户看到的 Windows 弹窗来自该任务拥有的 `electron.exe`，内容为 unknown software exception `0x80000003`，位置 `0x00007FF7AF7BBD39`。进程随后退出，残留为 0。
2. 实现隔离 `userData`、禁用硬件加速和普通 companion fallback 后，Playwright 在 `electron.launch` 内改为 `Assertion error`，worker 清理仍报告 `Target crashed`；应用已能在隔离 profile 创建 settings/outbox，但 composition 尚未完成。
3. 根据 Playwright launcher 参数规则，把 Chromium `--disable-gpu` switch 移到 app.asar 路径之前并移除重复 CLI `user-data-dir`；第二个 assertion 检查点仍返回同一 `Assertion error` 和 `Target crashed`，没有新的错误上下文或 Windows Application event。
4. 同一 assertion/crash 连续两个检查点没有有效新输出，命中任务卡 P0 停止条件。没有继续盲重试，没有启动真实 `Maris.exe`，也没有要求用户操作或修改系统设置。

## 8. 失败、未验证项与限制

- `app.asar E2E`：failed/blocking。
- 真实 `Maris.exe` startup、owner、modules、offline/recover、Tray quit 与 owned child cleanup：`not_run`。
- 最终 package hygiene：11 `.pyc` 和 6 `.egg-info` 文件需要后续任务在 package include/exclude 或构建前清理顺序中修复并重新打包验证。
- 因真实 E2E/EXE 门禁未完成，不能把本任务提交为 `review`，不能启动 P4-C12。

## 9. 最终 source manifest 与资源收口

- [E2 source manifest](../apps/desktop/b7-r1-e2-source.sha256)：194 entries；最终复算 194 matched、0 mismatch、0 missing。
- manifest 自身 SHA-256：`d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715`。该文件按路径字典序逐行记录 `relative-path<TAB>sha256`，末尾保留 LF，可直接逐行复算。
- 相对 192 文件起点：19 个既有文件变化、0 missing；新增 8 个产品/执行方测试源文件、本报告和 E2 manifest，共 10 个文件。19 个变化与 10 个新增全部位于任务卡允许范围；control、overview、其他角色、冻结、migration、独立测试和 `.claude/**` 均未修改。
- manifest 排除了自身、角色日志、本报告、`node_modules`、任务工具/cache、package/out、profile、trace、临时日志和 `.claude/**`。
- 最终清理：`node_modules=false`、`.b7-e2-tools=false`、`apps/desktop/out=false`、`test-results=false`、Python `__pycache__=0`；预存根 `.pnpm-store` 保持不变。
- 最终进程：Electron/Maris/Python/Pythonw 共 0；测试 profile 随任务工具目录删除；没有本任务窗口、Tray 或 sidecar 残留。

执行智能体已停止修改，等待头脑风暴总控复核阻塞证据并决定新的、范围明确的恢复任务。
