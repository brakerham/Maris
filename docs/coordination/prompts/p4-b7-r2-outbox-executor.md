# P4-B7-R2-OUTBOX：修复未经确认的老化消息删除

## 负责人、目标和停止点

你是既有执行智能体，唯一负责本任务。C12 已独立确认 P1 数据丢失缺陷 `P4-C12-OUTBOX-001`：超过 30 天的 draft/queued 在启动清理后持久化 2→0，没有用户删除确认。

修复生命周期保留与原生确认，完成开发自测及新版本 package/EXE 门禁。全部通过停在 `review / finished`，不要宣布缺陷独立关闭或 P4-B complete。发生产品 P0/P1、不可安全清理、失控异常弹窗或同一阻塞两个检查点无新证据时停在 `blocked / finished`。

不要运行/修改独立测试，不启动测试智能体、技术顾问、C12-R1 或高保真前端。用户自己派发后续角色。

## 必读与接单

按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、本角色状态和本任务卡，然后读取：

- `docs/p4-c12-outbox-blocked-coordinator-review.md`
- `docs/testing/phase-4-c12-windows-shell-report.md`（只读）
- `docs/phase-4-interface-freeze-003.md` §10 和现有 main/preload 安全边界
- IF-004/005，以及 LOCALZIP 总控审阅/运行说明
- `docs/coordination/snapshots/p4-b7-r2-outbox-start.sha256`

复算固定清单，记录条目数和摘要、接单、步骤/心跳/下个检查点；Git 暂存必须为零。外部操作前重读 control。修复前只读利用已确认首次失败，毋须重新运行独立失败节点。

## 唯一允许实现范围

- `apps/desktop/electron/main/outbox.ts`
- `apps/desktop/electron/main/index.ts`：只改 retention 提示接线及必要 import
- 可新增 `apps/desktop/electron/main/outbox-retention.ts`：可注入 dialog 的窄确认控制器
- `apps/desktop/tests/unit/supervisor-outbox.test.ts`：保留原断言，只补相关覆盖
- 可新增 `apps/desktop/tests/unit/outbox-retention.test.ts`
- `docs/b7-r2-outbox-running.md`
- `apps/desktop/b7-r2-outbox-source.sha256`：最终有序逐文件 source 清单，排除自身
- `docs/coordination/agents/executor.md`

禁止修改 renderer、preload、IPC/shared contract、其他产品、财务/Host/Agent/Python、migration、依赖、lock、Forge、构建/staging/helper、其他执行方测试、全部 `tests/independent/**`、测试报告/矩阵、control/overview/快照及其他角色文件。需要扩大范围先停止该部分并报总控，不自行设计新 API。

## 冻结的修复行为

1. **自动 cleanup**：terminal 保留 24 小时边界，严格超过才清理；所有非 terminal 不因年龄删除。load/start/shutdown 不丢正文、digest、原 client_event_id。
2. **待确认集合**：只取严格超过创建时间 30 天且当前 state 为 draft/queued 的条目。恰好 30 天不提示；sending 不进入删除集合。时钟注入支持确定性测试。
3. **提示**：使用现有 main 的原生 `dialog.showMessageBox`，文案显示待处理数量及会删除未发送内容，按钮为保留/明确删除；defaultId、cancelId 均保留。不上报正文/ID、不读取真实数据、不新增 renderer 删除能力。
4. **生命周期**：每次启动最多提示一次；窗口已就绪后安排，不阻塞 composition.start/Host readiness；退出/窗口销毁期间不提示或不继续删除。取消、关闭、dialog rejection 均不删除；错误以现有安全模式处理，不输出秘密或正文。
5. **确认范围**：只删除该次已提示并显式确认的候选；新条目、仍新鲜条目、内容/状态/时间字段已经变化的条目、sending 条目全部保留。采用当时不可变快照/指纹或等价方案，不提供“清空全部”能力。
6. **保存与并发**：窄范围串行化或等价方式防止 prepare/setState/cleanup/确认删除覆盖彼此；对存储失败只发布已成功持久化的状态。不能因删除失败使内存列表与重启后数据矛盾。不要引入新存储格式/依赖或重写整个 outbox。
7. **原合同保持**：20 条容量满仍明确拒绝、不自动腾位置；重放和重启 ID 不变；发送后修改内容的新 ID 语义保持；不调用 provider、不执行真实写账。

“停止自动删除”只解决丢失部分；须同时完成可测试的原生确认与 main 接线，不能把提示留到 P4-C。该确认属于 Shell 数据生命周期修复，不是财务驾驶舱界面设计。

## 开发自测与最小回归

仅写运行执行方测试。保留首次失败/修正记录，不降低原断言，不增加 skip/xfail。

- draft、queued、sending 在 30 天边界、30 天+1ms、远超期限经历 load→cleanup→重新读取均保留；模拟退出同样保留。
- 无过期项不提示；有过期项只提示一次且只传安全数量；保留/关闭/rejection 都不变。
- 明确确认只删除对应过期 draft/queued，新条目和 sending 不删；重新读取证实结果。
- 在 dialog 未决期间 prepare/setState 竞争，旧快照不得删除变化条目或丢新条目；重复确认有界且不扩大删除范围。
- 存储失败无部分删除/内存漂移；后续操作可以恢复，不遗留拒绝 Promise 阻塞队列。
- terminal 24 小时边界与 >24小时清理保持；20 条溢出仍拒绝；原 ID/密文/重启规则保持。
- main 生命周期接线、关闭/退出不弹窗、Host 不被等待 dialog 阻塞有可定位执行方测试；不要靠字符串存在替代公开行为。

TypeScript、lint、脚本差异检查后，执行修改测试和相关 main/composition/IPC/session 的必要回归。产品 main 接线变化，允许一次完整 desktop 执行方单元回归；不运行 Python/P0～P3/Host 全量。所有执行方结果与独立验收明确分开。

## 环境、新 package 与最终 EXE

已验证工具/普通依赖来自 `C:\MarisE5Final\E5-PKG-FINAL-20260929-1732`；旧 LOCALZIP evidence/profile/out 不修改、不删除、不复用个人状态。E4/E5-R1/E5-R2 依赖树不使用。无需重新安装或联网下载。

在新专属 `C:\MarisOutboxR2\R2-<时间戳>` 创建 evidence/profile 和普通工作副本；先验证绝对路径在该根内，工具审批按当前权限处理。只物化复制已接受源码、普通 node_modules 和必要固定工具，禁止 Junction/symlink 指向旧依赖来形成新 workspace。复制不修改旧树；逐文件核对源/副本、lock 和 Electron dist，不把旧 node_modules 的 `.bin` 残留当作可接受新 shim。

若工作副本命令解析需要任务局部 PATH/shim，只使用已接受的固定 Node/pnpm、核实版本/目标和实际 Forge 子进程环境，不修改系统/用户 PATH 或 pnpm。不重造复杂 R0/Job/精确进程数框架。

使用冻结官方 ZIP 和现有 LOCALZIP 校验/接线，设置 `MARIS_ELECTRON_ZIP_DIR` 为已验证 ZIP 所在普通目录：

- 文件 `electron-v44.4.5-win32-x64.zip`
- 长度 158184819
- SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`

固定 lock SHA-256：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。不改网络/TUN/代理、安全软件、依赖版本、production fuses 或校验规则。

在自测通过后授权新 package **1/1**，静态核对新 EXE/asar、67 Python resources、fuses、零污染及 staging 收口。新摘要不能套旧 LOCALZIP 的 EXE/asar 值；完整记录本轮输入、产物和路径。

静态全过后授权新 EXE **1/1**：固定 Node `spawn(shell:false)`，Playwright 只附加 loopback CDP，不使用 `_electron.launch()` 或 app.asar loader。全新虚拟 profile、已验证 Python、随机 loopback；按已通过 LOCALZIP 公开门禁检查双窗口、安全隔离、managed/authenticated Host、daily_finance/canonical Profile、毛毛、一次 recover、自然退出和自有资源零残留，硬上限 120 秒。不加载旧 profile 或真实主人/密钥，不触发过期草稿真实对话框来要求用户操作。

这次 native dialog 行为先以注入 adapter 证明，真实 Windows 老化提示的独立设备证据交 C12 后续任务，不冒充 OS 实测。因为 product main/outbox 已改，新产物不可缺；旧 EXE 只保留历史证据。

无目标启动、无副作用的语法/证据映射错误允许本任务内一次定向修正并保留原错误，不虚构新返修任务。产品启动后失败不可重跑覆盖；package/EXE 不追加预算。所有未知状态记 unverified。禁止启动 Docker、PostgreSQL、OpenClaw、微信、DeepSeek、其他角色或真实 provider。

## 交付和停止

超过五分钟操作前记录步骤、会话引用和下一检查点；有控制时至少十分钟心跳。报告正文包含问题原因、修复合同、准确代码位置、每组实际测试/失败/warning、并发/存储失败证据、旧树不变性、新 package/EXE 各一次结果、输入/产物摘要、边界及资源收口。

最终清单复算：所有授权改动逐项列出，起点其余项精确不变；独立测试和首次失败证据不可变化。外部敏感 profile/数据库/session 不进入仓库；保留脱敏证据和清单。只清理专属已验证目录的临时内容，不删除旧卷/依赖/证据。

全部成功交 review/finished 后停止，等待总控核对、新 C12 快照与测试智能体独立复验。不得把自测或真实 smoke 当作独立关闭。不得执行任何 Git 写操作。
