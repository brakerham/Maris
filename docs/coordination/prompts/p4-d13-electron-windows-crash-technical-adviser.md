# P4-D13 技术顾问任务卡：Windows 25H2 Electron GPU 启动崩溃裁定

你是技术顾问，唯一负责 `P4-D13`。本任务只读分析 `P4-B7-R1-E2-R1` 的最小 Electron fixture 崩溃，提出安全、可执行、能区分假设的下一阶段路线。你不得启动 Electron/Maris、不得安装工具、不得修改产品、依赖、lock 或系统设置。

## 必读输入

开始前依次读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. 最新 `docs/coordination/control.md`
6. `docs/coordination/agents/technical-adviser.md`
7. `docs/phase-4-interface-freeze-003.md`
8. `docs/phase-4-interface-freeze-004.md`
9. `docs/p4-b7-r1-e2-blocked-coordinator-review.md`
10. `docs/b7-r1-e2-r1-windows-shell-running.md`
11. `docs/p4-b7-r1-e2-r1-blocked-coordinator-review.md`
12. `docs/p4-b7-electron-windows-environment-evidence.md`
13. `apps/desktop/b7-r1-e2-r1-source.sha256`
14. `docs/coordination/snapshots/p4-d13-start.sha256`
15. 本任务卡

开始时先逐行复算 D13 固定输入；登记接单、当前步骤、下一检查点和心跳。最新 control 与任务卡冲突时以 control 为准。

## 固定事实

- R1 最小 fixture 不加载 Maris、Host、sidecar、数据库或真实 profile。
- Playwright default Electron loader、Node inspector 和 renderer CDP 已成功连接。
- 首个底层错误是 GPU child `-1073741515 = 0xC0000135 = STATUS_DLL_NOT_FOUND`。
- 后续 browser/Playwright 以 `0x80000003 = STATUS_BREAKPOINT`、assertion 和 Windows 弹窗停止。
- Windows 为 25H2 build `26200.9168`，Intel UHD + NVIDIA RTX 4060 Laptop 混合显卡，项目与 Electron dist 位于 D 盘。
- 常见 x64 VC++ runtime 和列出的 DirectX DLL 存在；具体缺失/拒绝加载的 DLL 未知。
- R1 时间窗内 Code Integrity 有 Chrome DLL 拒绝事件，但没有 Electron/Maris/项目路径命中；不能据此直接归因。
- Electron `44.4.5` 是当前 stable line；Electron 45 仍为 alpha。
- E2 的产品/Host/package 实现继续保留；R1 没有修改产品。
- 最终 package 的 `.pyc`/`.egg-info` hygiene 缺口仍未修复，但与最小 fixture crash 是两个问题。

## 必须回答的技术问题

### 1. 失败链与假设排序

分别评估并按证据强度排序：

- D 盘/非系统卷下 GPU child DLL 搜索或 sandbox 可见性；
- Windows 25H2 build 26200 与 Chromium/Electron GPU sandbox 兼容；
- 混合显卡/驱动初始化；
- Code Integrity、WDAC、DLL 签名级别或外部注入；
- Playwright launcher 的 inspector/CDP 作用；
- Electron 发行文件缺失/损坏；
- VC++/DirectX runtime；
- 其他有证据支持的分支。

明确区分：已确认事实、高可信推断、待 A/B 验证、当前缺乏证据。不得把相似 GitHub issue 当成本机结论。

### 2. 最小动态 A/B 矩阵

设计下一执行任务的严格顺序，每一步都必须说明：

- 只改变哪个变量；
- 使用 D 盘还是 C 盘任务临时目录；
- 直接 Electron fixture、Playwright fixture、app.asar 或 Maris.exe 中的哪一个；
- 是否保持 GPU/renderer sandbox；
- 期望观察到什么，结果分别支持/排除什么；
- 最多运行次数、弹窗停止条件和进程清理；
- 必须保留哪些脱敏日志，怎样避免再次删除唯一根因证据。

优先评价这条候选顺序：

1. 不重复 D 盘基线；把完全相同且摘要匹配的官方 Electron dist 与最小 fixture复制到 C 盘任务临时目录；
2. 先不经过 Playwright直接启动一次 sandbox-on fixture，区分 Electron/Windows 与 Playwright；
3. 只有 direct C 成功才在 C 盘运行一次 Playwright fixture；
4. 只有 C 盘 app/Playwright 稳定后才恢复 app.asar 和最终 EXE；
5. D/C 均失败时再决定是否需要官方诊断工具或版本对照。

你可以修改、拒绝或补充该矩阵，但必须给出理由。

### 3. 安全边界

裁定以下开关是否可以仅作为一次性诊断使用，以及它能证明什么、不能证明什么：

- `--disable-gpu-sandbox`
- `--in-process-gpu`
- `--use-angle=d3d11-warp`
- `--no-sandbox`

默认冻结：`--no-sandbox` 禁止；renderer sandbox、production fuses、安全软件、Code Integrity、系统 mitigation 和驱动不允许修改。若你认为某个诊断开关也不应使用，明确写入后续冻结。

### 4. 精确 DLL/拦截取证

在不猜测安装运行库的前提下，比较：

- Windows Event Log/Code Integrity/WER；
- Process Monitor（仅限 Microsoft Sysinternals 官方来源）；
- Process Explorer/ListDLLs/Sigcheck；
- Windows loader snaps、WinDbg 或其他 Microsoft 官方工具；
- Electron `--enable-logging`/Chromium verbose flags。

推荐最小必要工具和过滤条件，说明是否需要管理员权限、是否会修改系统、日志中如何去除用户名/路径/秘密。不得在本任务中实际下载或运行。

### 5. 版本与发布策略

基于 Electron 44 当前 stable、43 仍受支持、45 仍是 alpha，说明：

- 是否应做只读/隔离的版本对照；
- 哪个版本对照最能区分 Chromium regression；
- 何种证据才足以修改冻结版本和 lock；
- 不应采用哪些“能启动但降低生产安全”的长期 workaround。

### 6. package hygiene 是否拆分

裁定 `.pyc`/`.egg-info` resource allowlist 能否在 Electron 环境诊断之前，作为不启动 Electron 的独立执行任务先完成。若可以，给出文件边界、静态测试和“不可把未运行 package 当通过”的报告口径。

## 资料要求

使用 Microsoft、Electron、Chromium、Playwright、GitHub Desktop 或 Microsoft Sysinternals 的官方文档/官方 issue 为主要依据。每项关键建议附近放直接链接。若使用社区材料，只能作为补充并清楚标注。

至少核对：

- Microsoft NTSTATUS 对 `0xC0000135` 与 `0x80000003` 的定义；
- Electron sandbox 与 GPU process 说明；
- Electron `#36324`、`#37862`、`#52098`；
- GitHub Desktop `#22306`；
- Electron 当前 release/schedule；
- `app.disableHardwareAcceleration()` 与 GPU process 仍可能存在的边界。

## 文件边界

只允许修改：

- `docs/phase-4-d13-electron-windows-crash-advice.md`；
- `docs/coordination/agents/technical-adviser.md`。

禁止修改/运行：

- 任何产品代码、测试、依赖、lock、Forge、manifest 和 snapshot；
- `docs/coordination/control.md`、overview、矩阵、报告和其他角色文件；
- Electron、Maris、Python sidecar、Docker、OpenClaw、微信、DeepSeek；
- C/D 盘动态 A/B、系统日志清理、驱动/Windows/运行库安装或修复；
- Git 写操作。

## 交付要求

在 `docs/phase-4-d13-electron-windows-crash-advice.md` 交付：

1. 一页结论与证据等级；
2. 失败链图；
3. 假设排序表；
4. 精确 A/B 矩阵；
5. 诊断工具与日志保留方案；
6. 安全开关裁定；
7. 版本策略；
8. package hygiene 拆分建议；
9. 后续任务拆分、文件边界、停止条件和验收口径；
10. `P4-D13-F01...` 推荐冻结项与仍需总控决定的问题。

完成后提交 `review / finished` 并停止。不得自行创建后续执行 Prompt、接口冻结或 P4-C12，不得启动任何动态诊断。最终路线由头脑风暴总控审阅后冻结。
