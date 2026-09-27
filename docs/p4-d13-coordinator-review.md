# P4-D13 总控审阅：Electron Windows 启动崩溃与 package hygiene 拆分

审阅时间：2026-09-28，Asia/Shanghai
审阅角色：头脑风暴总控
结论：`P4-D13 complete`；接受为 `P4-IF-005`、`P4-B7-R1-H1` 与后续有限环境诊断的正式输入

## 1. 审阅结论

总控接受 [P4-D13 技术裁定](phase-4-d13-electron-windows-crash-advice.md)的证据分级、失败链、最小动态矩阵、26 条冻结建议和任务拆分。

目前唯一可以作为本机事实写入结论的是：不含 Maris 产品、Python Host、数据库和真实用户 profile 的最小 Electron fixture 中，GPU child 首先以 `0xC0000135 STATUS_DLL_NOT_FOUND` 退出；browser `0x80000003 STATUS_BREAKPOINT` 和 Playwright assertion 随后发生。缺失、不可见或被拒绝装载的具体 DLL 仍未知。D 盘、Playwright、Windows 25H2、混合显卡、GPU sandbox、驱动、Code Integrity 和运行库目前都是需要区分的假设，不能选一个直接当根因。

D13 没有启动 Electron、Maris 或 sidecar，没有运行 C/D 盘实验，没有安装诊断工具，也没有修改产品、依赖、lock、Forge、测试、系统设置或 Git 状态。技术顾问完成的是安全可执行的技术裁定，不是动态修复证据。

## 2. 总控对八个未决问题的裁定

### 2.1 动态顺序与运行预算

接受 `A1 → A2/F1` 分支顺序：

1. 不再运行既有 D 盘 Playwright baseline。
2. 第一个动态 cell 是同摘要 Electron `44.4.5` 与同 fixture 在 C 盘短 ASCII 任务目录中的 direct、sandbox-on 启动，最多一次。
3. A1 成功后才允许同目录 C Playwright A2，最多一次。
4. A1 同码失败时跳过 A2；后续是否运行 Procmon F1 由总控根据 A1 脱敏证据另行发布任务，当前 H1 不预先授权。
5. 每个 cell 最多一次、硬超时 60 秒；首个环境诊断检查点前最多四次进程启动。Windows 弹窗、新异常、日志失败、证据泄露或 owned process 收口失败立即结束整个动态任务。

A1 同时改变执行位置和 launcher，只是三角验证入口。只有 A2 与既有 D 盘 Playwright baseline 形成同 launcher 对照后，才能支持“执行位置、继承 ACL、ADS 或路径元数据相关”；即使恢复，也不能直接写成“D 盘是根因”。

### 2.2 Procmon、管理员权限和证据保留

本轮不把 Procmon、管理员权限或 EULA 接受打包进 H1。若 A1 同码失败，总控先核对 Electron 文件日志、退出码、ACL/ADS 和进程收口，再发布单独 F1 任务。F1 只能使用 Microsoft 官方 Sysinternals Process Monitor，采用 bounded backing PML，并在任务卡中写明来源、权限、过滤、保留和清理责任。

原始 PML、EVTX、日志和截图只能进入任务专属受限证据目录，先计算摘要，再生成脱敏报告。总控接受结论前不得覆盖或删除；接受后由该动态任务的唯一执行负责人清理原始证据，并在角色日志中记录清理结果。任何项目文档和 Git 候选文件只保存脱敏结论与摘要，不保存个人路径、token、命令行秘密或原始私人日志。

### 2.3 S1、G1 与版本对照

执行智能体不得自由遍历诊断开关：

- F1 仍无法命名 DLL，且证据指向 GPU sandbox 边界时，总控才可能另行批准一次 `--disable-gpu-sandbox` 的 C direct 诊断；renderer sandbox 保持开启，该开关永不进入生产配置。
- 只有证据明确指向硬件驱动或 ANGLE 时，才可能另行批准一次 sandbox-on 的 WARP 诊断。
- S1 与 G1 不组合，也不在同一任务中自动顺序尝试。
- `--in-process-gpu` 不进入最小矩阵；`--no-sandbox` 在诊断和生产中均禁止。

Electron `44.4.5` 与当前 lock 继续冻结。若 A1/F1 之后仍只剩版本假设，总控可另行批准官方独立 Electron `43.7.4` archive 的单次 C direct 对照；Electron 45 alpha 保持不运行。任何单次启动成功都不足以修改 lock 或生产版本。

### 2.4 package hygiene 的先行切片

批准先派发不启动 Electron 的 `P4-B7-R1-H1`。这是一个确定性 Python runtime resource staging 切片，只修复 `.pyc`、`.egg-info`、cache、测试和未知文件可能进入 package 的问题。

staging 根冻结为仓库内被忽略的 `apps/desktop/.maris-staging/python-runtime`。选择仓库内专用目录是为了让 Forge 配置、Windows 路径、测试和清理行为可复现；构建时使用同目录临时 sibling 完成后再原子替换。该目录不得进入 source manifest、Git 或最终文档中的绝对路径。

H1 只允许 source allowlist 实现与静态/单元测试；Electron、Forge package、app.asar、最终 EXE、sidecar、数据库和 P4-C12 全部为 `not_run`。H1 通过不会解除 P4-B 的环境阻塞。

### 2.5 C 盘后续门禁与最终产品路线

若未来 A1 与 A2 都成功，后续 app.asar 和 package/EXE gate 固定在 C 盘短 ASCII 任务目录执行，不再为“学术纯度”重复 D 盘弹窗。报告仍只能归纳为执行位置类差异。只有产品安装路径设计需要明确支持其他卷时，才另立 path/ACL/ADS 兼容任务。

若后续证据确认 Electron 44/Chromium 152 回归，执行智能体不得自行降级或等候任意版本。总控将基于官方 issue、修复提交、支持周期和安全门禁，在“受支持的 43 临时候选”“等待 44 patch”“向 Electron 提交脱敏最小复现”之间重新裁定。

## 3. D13 证据核对

| 项目 | 总控结果 |
| --- | --- |
| D13 文档 | 442 行，SHA-256 `07ad30b2e9c996e53b2940bca8b6e7835cd23a6e1612c36f6081dcb115d411ca` |
| 技术顾问状态 | `review / finished`；任务日志记录只修改 D13 文档与本角色状态 |
| 冻结建议 | `P4-D13-F01～F26` 共 26 项，编号唯一 |
| 动态矩阵 | A0/A1/A2/F1/S1/G1/V1/P1/P2，含前置、解释边界与最多启动次数 |
| 安全边界 | 禁止 `--no-sandbox`；renderer sandbox、fuses、CI/WDAC、安全软件、mitigation、驱动和 Windows 不改 |
| package hygiene | 明确可拆为不启动 Electron 的 allowlist/staging 切片 |
| Git/产品 | D13 未修改产品、测试、依赖、lock、Forge 或 Git 状态 |

## 4. 后续顺序

固定顺序为：

1. `P4-B7-R1-H1` 完成 source allowlist、staging、manifest 和静态测试，不启动 Electron。
2. 总控复算 H1 快照并核对 staging 行为；H1 最多进入 `review / finished`。
3. 总控基于 H1 终点另行生成 `P4-B7-R1-E3` 动态环境诊断任务，只执行 A1 及其被结果授权的 A2 或停止分支。
4. A1 失败时先回总控；Procmon、诊断开关和版本对照都不由 E3 自动展开。
5. A1/A2 稳定后，才恢复 app.asar、Forge package、最终资源扫描和 `Maris.exe` 黑盒门禁。
6. 上述执行方门禁和稳定快照通过后，才创建 P4-C12 独立验收任务。

这套顺序让项目在 Electron 环境问题尚未解决时仍完成一个确定、无弹窗的工程缺口，同时避免把静态 hygiene 通过误报为桌面应用已经可运行。

## 5. Git 与验收状态

D13 是已接受的技术裁定，H1 尚未实现，Electron 环境也尚未恢复。当前不提交受阻的 P4-B 产品为完成单元，不推送远端，不启动 P4-C12。P4-B 继续是开发中且受环境门禁阻塞的阶段。
