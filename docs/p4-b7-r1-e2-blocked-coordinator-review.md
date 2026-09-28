# P4-B7-R1-E2 阻塞总控核对

## 结论

- 总控接受 `P4-B7-R1-E2` 的 `blocked / finished` 结论；这不是 P4-B7 完成，也不是独立验收。
- E2 已完成的供应链、Host 组合、managed sidecar、执行方回归和 Forge package 证据继续有效，不从头重做。
- E2 的 194 文件 source manifest 已由总控逐行复算：`194 matched`、`0 mismatch`、`0 missing`；manifest SHA-256 为 `d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715`。
- 当前阻塞拆成两个独立问题：Electron/Playwright 启动合同，以及 package 中 Python 构建副产物的确定性排除。两者都可在不改业务架构、不降低生产安全熔断的前提下做窄范围恢复。
- P4-C12 继续保持 `not_started`；技术顾问和测试智能体现在不接任务。

## 已接受的 E2 证据

| 范围 | 总控结论 |
| --- | --- |
| 官方 Electron | `44.4.5` Windows x64 ZIP 为 158,184,819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |
| lock | 安装前、安装后和最终清理后均为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| 静态门禁 | OpenAPI drift、TypeScript、lint 通过；Vitest 11 files、22 tests 通过 |
| Python/Host | 55 项执行方回归通过；managed sidecar 的握手、readiness、owner、modules 和收口 smoke 通过 |
| package | Forge package 成功；`Maris.exe` 和 `app.asar` 均有摘要；生产 fuses 保持安全配置 |
| 阻塞 | app.asar Playwright 启动连续两个检查点均为 assertion/target crash；真实 EXE 未运行 |
| 资源 | Electron、Maris、sidecar、窗口、Tray 和测试 profile 均无任务残留 |

## 启动阻塞的静态诊断

当前 [shell.spec.ts](../apps/desktop/tests/e2e/shell.spec.ts) 对 app.asar 和真实 EXE 都强制传入 `executablePath`，再用 Playwright `_electron.launch()` 启动。这个测试设计混合了两种本应分离的对象：

1. app.asar 集成测试需要 Playwright 控制 Electron main/renderer；
2. 最终 `Maris.exe` 已通过 fuse 禁用 Node CLI inspect，应该作为安全成品做黑盒启动，不能再要求 Playwright Electron launcher 注入 main-process inspector。

Playwright 官方 Electron 文档明确提示：Electron launch 失败时应确认 `EnableNodeCliInspectArguments` 没有被关闭；而本项目最终包有意将它设为 `false`。Playwright `1.63.0` 的官方源码还显示 launcher 会注入 `--inspect=0` 和 `--remote-debugging-port=0`，并且传入 `executablePath` 时不会走其默认 Electron loader 路径。因此，对最终 fused EXE 继续使用 `_electron.launch()` 与生产安全配置存在结构性冲突。

参考：

- [Playwright Electron API](https://playwright.dev/docs/api/class-electron)
- [Electron Fuses 官方说明](https://github.com/electron/electron/blob/main/docs/tutorial/fuses.md)
- [Playwright 1.63.0 Electron launcher 源码](https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/src/server/electron/electron.ts)

这仍是基于源码和现有错误序列形成的高可信诊断，不把它写成已经动态证明的唯一根因。`P4-B7-R1-E2-R1` 必须先做一次最小兼容性探针：app.asar 模式不传 `executablePath`，让 Playwright 使用已校验的项目 Electron；最终 EXE 不走 Playwright Electron launcher。若最小探针仍在 Electron `44.4.5` 与 Playwright `1.63.0` 的上游参数兼容处失败，则立即带精确启动证据返回总控，不能靠改 fuse、降版本、patch Playwright 或无限重试绕过。

## package hygiene 诊断

当前 Forge `extraResource` 直接复制根目录的 `migrations` 与 `src`。`.gitignore` 只影响 Git，不会过滤 Electron Packager 复制，因此 Python smoke 生成的 `.pyc` 和 `*.egg-info` 会进入最终 resources。E2 实际发现 11 个 `.pyc` 和 6 个 `.egg-info`，这个缺口成立。

R1 应建立确定性的 runtime resource staging/allowlist：只复制运行所需的 `alembic.ini`、migration Python 文件和 `src/wife_system` Python 源文件，并让 package 对 staging 目录取资源；最终包对 `__pycache__`、`*.py[cod]`、`*.egg-info`、测试、工具缓存和个人路径必须为零命中。不能仅在本机临时删除副产物后重新打包，因为那不能证明下一次构建仍然干净。

## 冻结的恢复路线

1. 复算固定输入与 E2 source manifest，恢复精确 Node/pnpm/Electron 工具，不重复供应链选型和历史审计。
2. 先做最小 Electron/Playwright 兼容性探针并记录脱敏 launch evidence。
3. app.asar E2E 使用项目已校验的默认 Electron，不显式传 `executablePath`。
4. 最终 `Maris.exe` 保持生产 fuses 不变，使用外部进程与 loopback CDP/renderer 黑盒方式核对 startup、owner、modules、recover；`MARIS_E2E_EXIT_MS` 只在隔离 profile 下触发与 Tray 共用的 `requestQuit → app.quit → bounded shutdown` 路径。真实 Tray 点击仍留给 P4-C12 的 Windows 人工门禁。
5. 用确定性的资源 staging/allowlist 修复 package hygiene，并在故意存在 Python cache/metadata 的前置条件下打包验证。
6. 只有 app.asar、真实 EXE、资源扫描和进程收口全部通过，执行方才可进入 `review / finished`；随后总控才生成 P4-C12 任务卡。

## 明确禁止

- 不修改 `EnableNodeCliInspectArguments=false`、`RunAsNode=false` 或其他生产安全 fuse。
- 不新增长期 remote-debugging 开关、常驻调试端口或 renderer 中的 Node 能力。
- 不降级 Electron/Playwright/Forge，不修改 lock，不 patch/fork 第三方包。
- 不启动 Docker、PostgreSQL、OpenClaw、微信或 DeepSeek。
- 不修改/运行 `tests/independent/**`，不提前启动 P4-C12。
- 不执行 Git 写操作。

下一任务为 [P4-B7-R1-E2-R1 执行智能体 Prompt](coordination/prompts/p4-b7-r1-e2-r1-electron-launch-package-executor.md)。
