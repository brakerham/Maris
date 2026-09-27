# P4-B7 Electron Windows 环境证据

记录时间：2026-09-27 23:34～23:44，Asia/Shanghai

记录角色：头脑风暴总控

操作性质：只读；未启动 Electron、Maris、Python sidecar、服务或安装程序

## 系统与显卡

| 项目 | 值 |
| --- | --- |
| Windows | Windows 11 25H2 |
| Build | `26200.9168` |
| 架构 | x64 |
| 独立显卡 | NVIDIA GeForce RTX 4060 Laptop GPU |
| NVIDIA driver | `32.0.16.1656`，2026-08-20 |
| 核显 | Intel UHD Graphics |
| Intel driver | `32.0.101.5972`，2024-08-19；扩展 driver `32.0.101.6556` |
| 项目盘 | D 盘 |
| Windows 盘 | C 盘 |

## 常见运行时与图形 DLL

| 对象 | 只读结果 |
| --- | --- |
| VC++ x64 runtime | Installed=1，`14.51.36247.00` |
| `vcruntime140.dll` | 存在 |
| `vcruntime140_1.dll` | 存在 |
| `msvcp140.dll` | 存在 |
| `d3dcompiler_47.dll` | 存在，`10.0.26100.9168` |
| `d3d12.dll` | 存在，`10.0.26100.8972` |
| `dxgi.dll` | 存在，`10.0.26100.9168` |

以上只排除了一组常见缺失项，不能证明 Electron GPU child 的全部 DLL 依赖都满足。

## 状态码

| 观测值 | 转换/定义 |
| --- | --- |
| GPU exit `-1073741515` | `0xC0000135`，Microsoft `STATUS_DLL_NOT_FOUND` |
| Windows 弹窗 `0x80000003` | Microsoft `STATUS_BREAKPOINT` |

参考：[Microsoft NTSTATUS Values](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)

## Windows 事件日志

- Application 日志在 `2026-09-27 23:24:42` 记录 Application Popup 事件 26：`maris-electron-fixture: electron.exe`、`0x80000003`、位置 `0x00007FF634E1BD39`。
- 同一时间窗没有 Windows Error Reporting 或 Application Error 提供缺失 DLL 名称。
- Code Integrity Operational 时间窗共 136 条：68 个 3033 和 68 个配对 3089。
- 136 条全部是 Google Chrome 尝试加载其安装目录内的 `libLiteRtWebGpuAccelerator.dll`、`vulkan-1.dll` 或 `vk_swiftshader.dll`，没有 Electron、Maris、`D:\CodeX_gap` 或项目 node_modules 命中。
- Defender 与 AppLocker 时间窗没有项目/Electron 命中。

因此 Code Integrity 事件只登记为环境信号，不能归因给 R1 Electron crash。

## 上游匹配线索

- [electron/electron#36324](https://github.com/electron/electron/issues/36324)：GPU child `0xC0000135` 后 browser 因 unusable GPU 故意 breakpoint，解释两种状态码可能出现在同一失败链。
- [electron/electron#37862](https://github.com/electron/electron/issues/37862)：D 盘上 GPU child `-1073741515`，复制 Electron dist 到 C 盘后恢复；双显卡 Windows 11。
- [electron/electron#52098](https://github.com/electron/electron/issues/52098)：Windows 11 build 26200、混合显卡、sandboxed child `0x80000003`。
- [desktop/desktop#22306](https://github.com/desktop/desktop/issues/22306)：Windows 11 26200/26300 的 Electron sandbox GPU crash。
- [Electron 44](https://www.electronjs.org/blog/electron-44-0)：Electron 44 使用 Chromium 152；本项目 `44.4.5` 是当前 stable line。

这些是相似性证据，不是已经完成的本机 A/B 证明。

## 未执行

- 没有再次运行 D 盘 fixture。
- 没有把同一 Electron dist 复制到 C 盘启动。
- 没有使用 `--disable-gpu-sandbox`、`--no-sandbox` 或 `--in-process-gpu`。
- 没有下载 Sysinternals/调试器或其他诊断工具。
- 没有更新/回滚显卡驱动、Windows、Electron、Playwright 或 Forge。
- 没有修改系统 mitigation、Code Integrity、安全软件或注册表。

后续动态诊断必须由新任务绑定明确的单次矩阵、数据保留、弹窗停止和资源收口规则。
