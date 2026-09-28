# P4-B7-R1-E4-R1 总控核对：R0 PowerShell 参数转发失败

核对时间：2026-09-28，Asia/Shanghai

核对角色：头脑风暴总控

结论：接受 `P4-B7-R1-E4-R1` 的 `blocked / finished` 停止结论。任务没有执行 package，也没有对产品、依赖或既有 pnpm 恢复方案形成反例；首个失败是任务外 PowerShell evidence driver 把形参命名为自动变量 `$Args`，导致全部命令实参丢失。按用户此前决定，不再立即派发普通执行重试，先由 GPT-6 Astra 技术顾问完成一次窄范围 driver 审计。

## 1. 实际失败边界

固定输入和保留现场全部通过：R1 仓库起点 219/219、E4 source 198/198、E4 evidence 26/26、C 盘 source 198/198、Electron dist 73/73、污染 marker 9/9 均匹配。workspace lock、pnpm native、Electron executable 和 `node_modules` 摘要保持不变。

R0 控制脚本包含：

```powershell
function Run-Captured([string]$File,[string[]]$Args,[string]$Log) {
    $lines = @(& $File @Args 2>&1 | ForEach-Object { "$_" })
    # ...
}
```

`$Args` 是 PowerShell 自动变量。该函数的数组形参与自动变量冲突，函数体实际展开了空数组。因此：

- `where.exe` 没有收到 `pnpm`；
- pnpm 没有收到 `--version` 或 `config get ...`；
- Node 没有收到预检 `.mjs` 和两个路径参数；
- Forge `spawnPackageManager` 结果没有产生；
- `R0_READY_PACKAGE_0_OF_1` 没有到达。

该结论由运行说明、failure summary 和原始 `r1-controller.ps1` 第 18～19、43～48 行相互印证，不是从帮助输出猜测得出。

## 2. 没有发生的操作

- package：0/1，未运行；
- package 后静态门禁：未运行；
- packaged app.asar：0/1，未运行；
- 最终 `Maris.exe`：0/1，未运行；
- Electron、Maris、Host、sidecar、动态端口、窗口、Tray 和隔离 profile：未创建；
- 产品、测试、Forge、wrapper、staging、依赖、lock、系统 pnpm、用户/系统 PATH：未修改；
- Git：无写操作。

最终 `out=false`、staging=false、transition artifacts 0、task-owned process 0。R1 evidence 14/14 匹配，原失败现场完整保留。

## 3. 对现有 pnpm 恢复方案的影响

E4 的原失败是 Forge 裸 `pnpm` 命中失效用户 shim。总控此前使用 task-owned `pnpm.cmd` 和 E4 安装的真实 Forge `spawnPackageManager` 已取得 version `12.7.0`、hoist/public-hoist `undefined`、node-linker `hoisted`、退出 0。

E4-R1 没有把参数传给上述检查，因此不能用本轮结果否定该恢复方案。已知事实仍是：进程级 PATH 的 task-owned shim 在总控同构预检中可行；未知的是一份完整、受控、可审计的 R0 driver 能否在保留现场里一次完成六项预检和不变性核对。

## 4. 为什么不直接发布 R0-R1

把 `$Args` 改成 `$CommandArgs` 在语义上很小，但连续两次任务都在产品 package 之前因工具编排停止。用户已明确设置升级边界：再失败就停止当前路线并使用 GPT-6 Astra 给出解决方案或直接处理。因此总控不把显而易见的改名再次包装成普通执行任务。

下一步先执行 `P4-D14`：Astra 技术顾问只读审计 driver，比较最小改名与 `ProcessStartInfo.ArgumentList` 等方案，冻结实参传递、日志、超时、PID 清理、fresh evidence、R0-only 停止点和是否允许后续 package 的条件。D14 不运行 R0/package，不修改产品或系统。

## 5. 当前决定

1. `P4-B7-R1-E4-R1` 保持 `blocked / finished`。
2. 现有执行智能体停止，不接收第三次 R0 任务。
3. `P4-D14` 由用户在 GPT-6 Astra、reasoning `high` 的技术顾问聊天中执行。
4. D14 交付前，package、P1、P2、P4-C12 和前端业务实现均不由当前任务自动启动。
5. 总控收到 D14 后，只允许二选一：冻结一份 R0-only 执行任务，或宣布 package 环境路线暂停并转向独立环境处置；不重复开放式试错。
