# P4-B7-R1-E2-R1 阻塞总控核对

## 结论

- 总控接受 `P4-B7-R1-E2-R1` 的 `blocked / finished` 结论。任务按“不受控 Windows 弹窗立即停止”的硬门禁安全收口，没有重复启动 app.asar、Maris.exe 或 package。
- R1 起点 200/200 与 E2 source 194/194 均匹配；产品、依赖、Forge、脚本和测试文件零变化。新增内容只有 R1 报告、R1 source manifest，并更新执行智能体自己的状态文件。
- R1 已把问题缩小到不含 Maris 产品代码、Python Host、数据库和真实 profile 的最小 Electron fixture。P4-B7 产品实现暂时不是本轮 crash 的解释对象。
- 当前不得再次把相同 fixture 直接派给执行智能体。新的技术路线涉及运行盘符、Windows 25H2 GPU sandbox、诊断开关和版本策略，按协作规则先交 `P4-D13` 技术顾问只读裁定。
- package resource allowlist 是独立、仍未实现的问题；D13 需要判断它是否应从 Electron 环境诊断中拆出，先作为不启动 Electron的执行切片完成。

## R1 有效证据

| 项目 | 证据 |
| --- | --- |
| 最小范围 | fixture 只创建隐藏的 sandboxed BrowserWindow，不加载 Maris、Host、sidecar、真实数据库或用户 profile |
| Playwright | 未传 `executablePath`；使用项目 Electron 与官方 loader；Node debugger 和 renderer CDP 均连接成功 |
| 首个底层失败 | GPU child `exit_code=-1073741515` |
| 后续表现 | Playwright `_CRSession._onMessage` assertion；Windows 弹窗 `0x80000003` |
| 安全收口 | Electron、Maris、Python/Pythonw 均为 0；node_modules、工具/cache、fixture/profile/log、out/test-results 已清理 |
| 产品变化 | 0 |
| R1 source | 194 matched、0 mismatch、0 missing；与 E2 source 内容相同，SHA-256 `d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715` |

## Windows 状态码链

`-1073741515` 的无符号十六进制值是 `0xC0000135`。Microsoft 将它定义为 `STATUS_DLL_NOT_FOUND`；`0x80000003` 是 `STATUS_BREAKPOINT`。[Microsoft NTSTATUS 表](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)

Electron 旧的官方 issue 有与本轮组合非常接近的崩溃栈：GPU child 以 `0xC0000135` 断开后，browser 因 GPU process 不可用而走故意 breakpoint 终止，最终显示 `0x80000003`。这解释了为什么执行日志中的 GPU exit code 与 Windows 弹窗异常码不同；它们可能是同一失败链的两个阶段，而不是两次无关故障。[electron/electron#36324](https://github.com/electron/electron/issues/36324)

这仍没有指出“缺少的具体 DLL”。原始日志已按任务卡清理，Windows Application/WER 没有留下可直接命名 DLL 的 Electron 事件，所以后续若要继续，需要先设计能保留脱敏 loader/Code Integrity 证据的一次性诊断，而不是猜测并安装运行库。

## 与本机环境的上游匹配

总控只读取得：

- Windows 11 25H2，Build `26200.9168`；
- NVIDIA RTX 4060 Laptop GPU `32.0.16.1656`；
- Intel UHD Graphics `32.0.101.5972`；
- 项目及本轮 Electron dist 位于 D 盘；
- x64 VC++ runtime 已安装，版本 `14.51.36247.00`；系统 `d3dcompiler_47.dll`、`d3d12.dll`、`dxgi.dll`、`vcruntime140.dll`、`vcruntime140_1.dll`、`msvcp140.dll` 均存在。

与这些事实对应的官方/上游证据：

1. Electron 官方 issue 记录 Windows 11 build `26200` 上 sandboxed GPU/renderer 以 `0x80000003` 崩溃，并包含混合显卡环境；关闭 GPU sandbox 会改变故障，但该 issue 没有给出可直接用于生产的安全修复。[electron/electron#52098](https://github.com/electron/electron/issues/52098)
2. GitHub Desktop 官方 issue 同样记录 Windows 11 `26200/26300` 上 Electron GPU sandbox 启动崩溃。[desktop/desktop#22306](https://github.com/desktop/desktop/issues/22306)
3. Electron 官方旧 issue 记录 GPU child `-1073741515` 在 D 盘运行时反复崩溃、复制到 C 盘后恢复，并提到双显卡环境；该 issue 很旧且已关闭，不能单独证明本机根因，但使“同字节 C/D 路径 A/B”成为优先级较高、风险较低的验证。[electron/electron#37862](https://github.com/electron/electron/issues/37862)
4. Electron 官方说明 `app.disableHardwareAcceleration()` 只关闭硬件加速；Chromium 仍可能保留独立 GPU process，因此 R1 已使用 `--disable-gpu` 仍看到 GPU child，不构成反证。[Electron app API](https://www.electronjs.org/docs/latest/api/app)、[electron/electron#28164](https://github.com/electron/electron/issues/28164)

Electron `44.4.5` 是当前最新 stable，包含 Chromium 152；Electron 45 仍是 alpha。因此当前不能简单解释为“项目锁在明显过时版本”，也不应未经裁定就升到 prerelease。[Electron 44 发布说明](https://www.electronjs.org/blog/electron-44-0)、[Electron Releases](https://github.com/electron/electron/releases)

## Code Integrity 限制证据

在 R1 时间窗内，Windows Code Integrity Operational 日志共有 68 个 3033 与 68 个配对 3089 事件，全部属于 Google Chrome 对自身 `libLiteRtWebGpuAccelerator.dll`、`vulkan-1.dll` 或 `vk_swiftshader.dll` 的加载拒绝；没有一条命中 Electron、Maris 或项目路径。Defender 与 AppLocker 日志也没有 Electron 命中。

这些事件说明本机正在执行 Microsoft signing level 约束，但不能作为 Electron crash 的直接因果证据。D13 必须把它列为环境信号和待验证分支，不得写成“已经确认安全软件拦截 Electron”。

## 当前冻结边界

- 不再次运行相同 D 盘 Playwright fixture。
- 不使用 `--no-sandbox`，不修改 renderer sandbox、production fuse、安全软件、系统 Code Integrity、TUN、代理或驱动。
- 不安装/修复 VC++ runtime；现有常见 runtime 文件和注册状态已经存在，缺少具体 DLL 尚未证实。
- 不升级/降级 Electron、Playwright、Forge，不修改 lock，不 patch/fork 第三方包。
- 不把 `--disable-gpu-sandbox` 当成产品修复。D13 可以评估它是否有资格成为一次性诊断分支，但不得实际运行。
- 不启动 P4-C12。

下一步为 [P4-D13 技术顾问任务卡](coordination/prompts/p4-d13-electron-windows-crash-technical-adviser.md)。
