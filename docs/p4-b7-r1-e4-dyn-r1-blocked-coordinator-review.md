# P4-B7-R1-E4-DYN-R1 总控核对：P1 进程根识别假设阻塞

核对时间：2026-09-29，Asia/Shanghai

核对角色：头脑风暴总控

结论：接受 `P4-B7-R1-E4-DYN-R1` 的 `blocked / finished` 事实和资源收口；本轮阻塞来自任务外 evidence runner 的 root PID 假设，产品保持 `unverified`，没有形成 Electron crash 或 Maris 产品缺陷证据；允许创建一次有明确提升规则的新 P1 动态预算

## 1. 失败分类

P1 通过 Playwright 默认 Electron loader 启动最终 app.asar。`ElectronApplication.process()` 返回 PID `26924`，该短生命周期进程在 runner 查询时已经退出；仍在运行的实际 Electron browser PID `22792` 是它的直接子进程，并同时满足：

- executable path 精确等于冻结 Electron executable；
- 创建时间属于本轮启动窗口；
- 与返回 PID 存在直接父子关系；
- 本轮 owner marker receipt 已存在。

runner 把“Playwright 返回 PID 必须仍然存活且本身就是 browser root”作为硬条件，因此在窗口、sandbox、preload API、runtime、modules 和 recover 验证前抛出 `root_identity_mismatch`。这个条件不是产品合同，也不是 Playwright/Electron 成功的必要条件。

本轮产品结果保持 `unverified`：隔离 profile 已产生加密 owner session 和虚拟数据库，Electron 日志没有冻结的 crash/assertion 模式，但这些旁证不能替代未执行的 preload API 验证。

## 2. 证据与收口

- DYN-R1 起点 246/246 matched；终点 245 unchanged、1 个授权角色日志变化、2 个授权新增交付、0 missing、0 越界修改。
- `runtime-evidence.sha256` 含 84 个唯一有序条目；总控复算 84/84 长度与 SHA-256 匹配，manifest SHA-256 为 `db316ae191e295793edcded01f85ba81e54809d3696a61e364f11b372c6db8bf`。
- P1 实际启动 1/1，用时约 5 秒，没有超时；P2 为 0/1、`not_run`。
- 日志没有 `0xC0000135`、`0x80000003`、`STATUS_DLL_NOT_FOUND`、`STATUS_BREAKPOINT`、child/render process gone、Target crashed 或 assertion。
- 后置检查从真实 browser root 精确识别 6 个本轮进程并定向清理；清理后 6/6 PID 消失，窗口、listener 与 owned process 为 0。
- EXE、app.asar、source 198 项、Electron dist 73 项、Python resources 67 项、package out 140 项和 production fuses 前后不变。

执行方交付摘要与实际文件一致：

- `apps/desktop/b7-r1-e4-dyn-r1-source.sha256`：`04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`
- `docs/b7-r1-e4-dyn-r1-running.md`：`9ef7634e4b0bf20882de16d2de394eaa9b19b4ded8c0f4c9c719013bec5dca4c`
- `docs/coordination/agents/executor.md`：`01bfae638823d6f80f5c924fdd4fef6e8496a943f9c6950956b6fa565bf018b6`

总控接管工作区时发现 `.pnpm-store/**`、DYN-R1 两份交付和执行角色日志处于 staged 状态，这与报告中的 `Git 写操作：false` 不一致。现有证据不能确认是哪一个进程或操作者改变了 index，因此来源登记为 `unverified`，不直接归因。总控只撤销了这些路径的暂存状态，没有删除或改动缓存、交付文件或产品内容；`.pnpm-store/` 继续作为未跟踪本地缓存排除在提交之外。后续任务必须把“开始与结束均无 staged paths”列为 Git 边界证据。

## 3. 恢复裁定

下一任务为 `P4-B7-R1-E4-DYN-R2`。它不修改产品，不重跑 package，也不重复旧 P1。新 P1 使用新的 evidence、profile、虚拟数据库和 1/1 动态预算。

新的所有权规则固定为：

1. Playwright 返回 PID 记为 `launchPid`，不得假定它在验证时仍存活；
2. 若 `launchPid` 仍存活且 executable path 匹配，则它是 browser root；
3. 若 `launchPid` 已退出，只允许在其已记录的直接后代中选择 executable path 匹配、创建时间匹配、owner marker 匹配的存活 Electron browser；
4. 候选必须恰好一个；零个或多个都在调用产品 API 前停止；
5. 唯一候选提升为 `browserRootPid`，其后代闭包构成本轮 owned process set；
6. 不限制 Electron/Chromium/console host 的精确进程数量；
7. 清理只从提升后的 browser root 开始，并继续使用路径、时间、祖先关系和 marker 联合验证。

任务外 runner 在启动前必须完成静态语法检查，并把这七条规则映射到明确代码位置。不得新增 synthetic 进程测试、Job Object 或进程预算。新 P1 若再次因 root ownership 识别停止，总控不再创建同类 DYN-R3，而是终止当前自动动态路线并重新裁定验收方式。

P1 全部通过后才允许原计划的一次 P2 最终 EXE 黑盒门禁。P4-C12 继续停止。
