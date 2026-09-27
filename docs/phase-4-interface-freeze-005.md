# P4-IF-005：Electron Windows 诊断与 package resource 补充冻结

状态：`frozen`
冻结时间：2026-09-28，Asia/Shanghai
输入：[P4-IF-003](phase-4-interface-freeze-003.md)、[P4-IF-004](phase-4-interface-freeze-004.md)、[E2-R1 阻塞核对](p4-b7-r1-e2-r1-blocked-coordinator-review.md)、[P4-D13 技术裁定](phase-4-d13-electron-windows-crash-advice.md)、[D13 总控审阅](p4-d13-coordinator-review.md)
适用任务：`P4-B7-R1-H1`、后续 `P4-B7-R1-E3` 及恢复后的 P4-C12

本文件补充 P4-IF-003 与 P4-IF-004。未明确改变的既有安全、依赖、Host、IPC、owner、Supervisor、fuse 和测试条款继续有效。

## 1. 失败事实与归因边界

### P4-IF-005-F01：第一故障

固定本机已知事实为：最小 Electron fixture 中 GPU child 首先以 `0xC0000135 STATUS_DLL_NOT_FOUND` 退出；具体 DLL 和失败机制未知。

### P4-IF-005-F02：下游现象

browser `0x80000003 STATUS_BREAKPOINT` 与 Playwright assertion 视为上述失败链的下游现象，除非新的 stack 或 dump 证明存在独立先发故障。

### P4-IF-005-F03：不得过度归因

不得把相似 Electron/GitHub Desktop issue、D 盘、Windows build 26200、混合显卡、Chrome Code Integrity 事件、Playwright 或某个运行库直接写成本机根因。所有结论必须区分观察、支持的假设、不能证明的内容和下一单变量验证。

## 2. 动态环境诊断

### P4-IF-005-F04：不重跑 D 基线

既有 D 盘 Playwright 最小 fixture 只作为固定失败证据，不再启动。

### P4-IF-005-F05：A1

后续第一个动态 cell 必须使用相同摘要的 Electron `44.4.5` 和相同 fixture，复制到 C 盘短 ASCII 任务目录，以 direct 方式、GPU sandbox on、renderer sandbox on 启动，最多一次。保留 `app.disableHardwareAcceleration()`、`--disable-gpu`、隔离 profile 和文件日志。

### P4-IF-005-F06：A2/F1 分支

A1 成功后才允许同目录、同内容的 Playwright A2，最多一次。A1 同码失败时跳过 A2并停止在总控检查点；Procmon F1 必须由新的总控任务明确授权，不能由执行智能体自动进入。

### P4-IF-005-F07：三角验证措辞

A1 同时改变执行位置和 launcher，不是纯 D/C A/B。只有 A2 与既有 D baseline 构成同 launcher 对照。即使 C 恢复，初始结论也只能写“执行位置、继承 ACL、ADS 或路径元数据相关”。

### P4-IF-005-F08：运行预算和停止

每个 cell 最多一次、硬超时 60 秒，同配置不重试。任何 Windows 弹窗、新异常码、日志失败、证据泄露、unowned process 或 owned process 清理失败，立即停止整个动态任务。

### P4-IF-005-F09：进程所有权

清理只按 run PID、descendant、executable path、start time 和 owner marker 共同确认；禁止按进程名广泛终止 Electron、Maris、Node 或 Python。

### P4-IF-005-F10：证据

动态任务在启动前生成 run manifest，记录 source/dist 摘要、参数、安全状态、ACL/ADS 元数据和日志位置。原始日志、PML、EVTX 与截图先计算 SHA-256 并受限保留；项目文档只写脱敏结论和摘要。

## 3. 诊断工具与安全开关

### P4-IF-005-F11：Procmon

Process Monitor 只允许在 A1 同码失败后由总控另立 F1 任务，从 Microsoft 官方来源取得，以 bounded backing PML 运行一次。单个 `NAME NOT FOUND` 或 `ACCESS DENIED` 不构成根因；必须确认退出前未被后续 `SUCCESS` 满足的搜索或拒绝链。

### P4-IF-005-F12：命名 DLL 后的顺序

一旦命名候选 DLL，先核验存在性、bitness、hash、签名、ACL、ADS 与官方 archive manifest。禁止猜测安装 runtime、从第三方 DLL 网站下载文件、关闭安全软件或修改系统 mitigation。

### P4-IF-005-F13：诊断开关

- `--disable-gpu-sandbox` 只可在 F1 原始证据已保存且仍支持 sandbox 假设时，由总控批准一次 C direct 诊断；不得进入生产。
- WARP 只可在证据仍明确指向驱动或 ANGLE 时，由总控批准一次 sandbox-on 诊断。
- 两者不得组合或由执行方自由遍历。
- `--in-process-gpu` 不进入最小矩阵。
- `--no-sandbox` 在诊断和生产中均禁止。

### P4-IF-005-F14：保持的边界

renderer sandbox、context isolation、production fuses、安全软件、Code Integrity/WDAC、Windows mitigation、显卡驱动和操作系统版本保持不变。

## 4. Electron 版本

### P4-IF-005-F15：当前冻结

Electron `44.4.5` 和现有 lock 继续冻结。首个动态任务不得改 `package.json`、lock、Playwright、Forge 或 Electron 版本。

### P4-IF-005-F16：条件版本对照

只有 A1/F1 后仍有明确版本假设时，总控才可另行批准官方独立 Electron `43.7.4` archive 的单次 C direct 对照。Electron 45 alpha 默认不运行。单次对照成功不足以修改 lock、生产版本或发布基线。

## 5. Python package resource staging

### P4-IF-005-F17：独立 H1 切片

package hygiene 拆为 `P4-B7-R1-H1`，先于新 Electron 动态任务执行。H1 不启动 Electron、Forge package、app.asar、Maris.exe、sidecar 或数据库，不运行 P4-C12。

### P4-IF-005-F18：staging 根与原子性

staging 根固定为被忽略的 `apps/desktop/.maris-staging/python-runtime`。每次先在同一父目录创建新的 task-owned sibling，完整验证后原子替换目标；失败不得保留半成品或旧文件。目录及其内容不得进入 Git、source manifest 或最终 package 之外的交付物。

### P4-IF-005-F19：source allowlist

staging 只允许：

```text
alembic.ini
migrations/env.py
migrations/versions/*.py
src/wife_system/**/*.py
```

`migrations/README` 和 `migrations/script.py.mako` 默认不进入 runtime staging。若真实 runtime 证据证明必要，必须回到总控扩展冻结，不能回退为复制整个目录。

### P4-IF-005-F20：拒绝项

显式拒绝：

```text
**/__pycache__/**
**/*.py[cod]
**/*.egg-info/**
tests/**
.pytest_cache/**
build/**
dist/**
scratch/**
任意 symlink、junction、reparse point
任意绝对路径、.. 越界或源根外目标
任意未在 allowlist 中的文件类型
```

### P4-IF-005-F21：manifest

staging manifest 只包含排序稳定的相对路径、字节数和 SHA-256。它不得包含个人绝对路径。每个 staged 文件的摘要必须等于对应 source 文件，且路径集合必须精确等于 allowlist 展开结果。

### P4-IF-005-F22：Forge 接线

Forge `extraResource` 只引用 staging 中的 `alembic.ini`、`migrations` 和 `src` 三个已知入口，并保持最终 runtime 相对布局。H1 可以实现和静态核对接线，但不得实际运行 Forge package。

### P4-IF-005-F23：H1 验证口径

H1 必须通过专属 Vitest/static tests，覆盖污染源排除、旧文件清除、原子替换、路径集合/hash、symlink/reparse/越界拒绝和必要 runtime 文件完整性。Electron/Forge package、最终 resources 扫描、app.asar、fuses、EXE 和 sidecar 必须明确为 `not_run`。

### P4-IF-005-F24：最终 package gate

环境恢复后，真正的 package gate 必须在 source tree 故意存在 cache/metadata 的前置条件下运行 Forge package。最终 resources 对 `__pycache__`、`*.py[cod]`、`*.egg-info`、tests、工具缓存和个人路径均为零命中，并核对 staging manifest、migration 与 sidecar runtime。静态 H1 通过不能代替此 gate。

## 6. 顺序与结论权限

### P4-IF-005-F25：任务顺序

顺序固定为 H1 静态实现 → 总控核对 → E3 A1/A2 或停止分支 → app.asar/package/EXE 恢复门禁 → P4-C12。并行任务不得修改相同桌面配置、脚本或测试文件。

### P4-IF-005-F26：P4-C12

P4-C12 在环境、package 与最终 EXE 的执行方动态证据被总控接受前保持 `not_started`。执行方任务只能提交 `review / finished` 或准确的 `blocked / finished`，不得宣布 P4-B complete。
