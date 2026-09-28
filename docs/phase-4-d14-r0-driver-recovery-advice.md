# P4-D14：E4-R1 R0 driver 恢复技术裁定

- 角色：技术顾问；任务：`P4-D14`；证据日期：2026-09-28，Asia/Shanghai。
- 依据控制版本：`2026-09-28T16:20:00+08:00`。
- D14 固定输入：223/223 matched，0 mismatch、0 missing、0 invalid；manifest SHA-256 `98ac61ebe79a58e0fc4b0f5817c4530594079399dfc2ab03367d4812a1f52a2d`。
- E4-R1 source：198/198 matched；manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。
- 本文代码是供后续授权任务使用的建议实现；本次只静态检查，**未执行代码、R0、pnpm、Node probe、package 或产品**。外部 E4/R1 evidence 原样保留。

## 1. 一页结论

**当前阻塞属于 evidence driver，不能据此否定 task-owned pnpm PATH 恢复方案，也没有产生产品缺陷证据。** R1 的 `Run-Captured` 将参数命名为 `$Args`，与 PowerShell 为未声明参数维护的 `$args` 自动变量同名；当前调用没有额外未绑定参数，函数体实际展开空数组。where、pnpm、Node 同时丢参，正好解释帮助输出、交互等待及 Forge 结果缺失。PowerShell 变量名不区分大小写，将 `Args` 改成 `args` 没有用。[Microsoft 自动变量](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-7.5#args)

只改名不够。旧 driver 还有六项独立的可靠性缺口：无硬超时；合并 stdout/stderr；全部启动后才校验；未检查退出码先解析 JSON；摘要连接换行不一致；ready 后仍存在 package 执行路径。下一任务应重建一份 **R0-only driver**，原现场只读，并在每项检查失败时立即结束。

**唯一推荐：`ProcessStartInfo` + `.ArgumentList` + 并发双流落盘 + 有界等待。** 原生 `.exe` 逐项传参；裸 `pnpm` 经过仅允许四个固定查询的 `cmd.exe` adapter；真正的 Forge 同构检查继续调用已安装的 `spawnPackageManager`。不能直接把 `.cmd` 交给 `UseShellExecute=false`，也不能认为 `ArgumentList` 会替任意 shell 文本解决注入和 quoting。[Microsoft ArgumentList](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.argumentlist)、[Microsoft cmd](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd)

为了让超时收口覆盖后代而不是仅覆盖父 PID，本文实现使用一个匿名 Windows Job Object 和一个等待输入的 PowerShell worker：先把 worker 纳入 job，再放行目标命令；不允许 breakaway；退出/超时后查询 job 的 active process count。该辅助机制只属于外部 R0 driver，不进入仓库产品、wrapper 或 package。若当前执行环境不允许建立 job，按 `harness_setup_failure` 停止，不降低收口保证。[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)

**必须先纠正任务卡的一处计数：** `pnpm config get hoist-pattern` 有 **3 个实参**，连 executable token 一共 **4 个 tokens**。另外两个 config 查询相同。任务卡要求“四个参数”与冻结命令、原脚本和 Forge 实际参数数组相矛盾。建议总控冻结 `argumentCount=3, commandTokenCount=4`，不加空参数、不添加新 flag、不改查询语义。

R0-only 六项顺序保持 `where → version → hoist → public-hoist → node-linker → Forge`；每项独立 evidence，前一项精确通过才开始后一项。完成后复算不变性和 owned process，只有全部通过才写 `R0_READY_PACKAGE_0_OF_1` 并退出。没有 `Read-Host GO`，没有 wrapper/package 路径，没有后续执行分支。

R0-ready 可以作为总控另立 package-only 任务的输入，不能自动兑换成 package 授权。新进程不能“继承已经退出的 R0 会话”；必须依据不可变环境配方重新构造进程级 PATH，核对完整环境摘要和固定现场，再由总控明确决定是否复验必要的 pnpm 解析条件。

## 2. 已读取的证据与可信度

| 证据 | 核对结果 | 结论边界 |
| --- | --- | --- |
| [E4 总控核对](p4-b7-r1-e4-blocked-coordinator-review.md) | E4 package 在 Forge 裸 pnpm 系统检查失败；总控同构预检通过 | PATH shim 方案已有一次真实成功证据；不等于 R1 完成 |
| [E4-R1 任务卡](coordination/prompts/p4-b7-r1-e4-r1-pnpm-path-resume-executor.md) | 原任务授权 package，但被最新 control 停止 | 本文不得恢复原 package 分支 |
| [E4-R1 运行说明](b7-r1-e4-r1-pnpm-path-resume-running.md) | package 0/1，R2/P1/P2 not_run；R1 evidence 14/14 的既有记录 | 本次复核四个关键原文件，不冒充重做全部 node_modules/environment 核验 |
| [E4-R1 总控核对](p4-b7-r1-e4-r1-blocked-coordinator-review.md) | 接受 driver 参数缺陷，升级至 D14 | 产品、Forge 和 pnpm 恢复方案未被本轮实际否定 |
| `<r1>/r1-controller.ps1` | SHA-256 `65ce91fa661ca43432d14afd8e0fff31a2127b1a8af96b375c956709ea980505`，匹配 | 只读检查，未修复或运行 |
| `<r1>/r0-forge-preflight.mjs` | SHA-256 `0578d5b1cb708635bcefeddeb45a66d13d4c500a46ee7b68d49f4589c75de5cd`，匹配 | 实际 Node 参数为 probe、module、desktop 三项 |
| `<r1>/forge-pnpm-bin/pnpm.cmd` | 101 bytes；SHA-256 `57785cc51fff3a94b68815e46f48a400f1cb016f9edc82d2cb9606cbdb088bdf`，匹配 | 调用固定 pnpm-native，透传 `%*` 和 errorlevel |
| `<r1>/evidence/r0/failure-summary.json` | SHA-256 `14b02ff0698f0ccb7bbf68671040da847f84525b147f2de49e93657ae5f14c1d`，匹配 | 五个已落盘帮助输出、Node 等待、Forge log 缺失 |
| [package wrapper](../apps/desktop/scripts/package-desktop.mjs) | 只读核对：stage → 当前 Node 启动 Forge CLI → finally cleanup | 继承环境；不负责构造裸 pnpm 的查找顺序 |
| `<workspace>/node_modules/@electron-forge/core-utils/dist/package-manager.js` | 只读核对真实 `spawnPackageManager` | 使用裸 `pnpm`，通过 cross-spawn-promise 调用并 trim stdout |

`F` 表示本机固定文件/证据或官方定义；`I` 表示证据一致的推断；`U` 表示必须由下一授权任务动态验证。原始私有路径只留在外部现场，本文件使用 `<task-root>`、`<r1>`、`<workspace>` 等语义标签。

## 3. PowerShell 根因与第二层风险

### 3.1 `$Args`、`@Args` 与实际调用

原脚本第 18～21 行相当于：

```powershell
function Run-Captured([string]$File, [string[]]$Args, [string]$Log) {
    $lines = @(& $File @Args 2>&1 | ForEach-Object { "$_" })
    $code = $LASTEXITCODE
}
```

`$args` 是 PowerShell 自动维护的“未声明/未绑定参数数组”。不应将它用作业务形参。`@Args` 的语法确实是**数组 splatting**；它将名为 `Args` 的变量当前持有的数组逐项展开，不会按形参声明重新找回被覆盖的原始数组。本案中该名字同时指向自动变量，因此是“对当前自动变量值做数组 splatting”，这两种说法并不互斥。[Automatic Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-7.5#args)、[Splatting](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_splatting?view=powershell-7.5)

调用 `Run-Captured 'where.exe' @('pnpm') <log>` 在当前简单函数中已经使用了 File、参数数组和 Log 的位置；没有额外未绑定值。固定失败证据显示函数体展开的是空自动变量数组。该具体结果是本机证据与语言语义的联合结论，不能泛化为“任何名叫 Args 的函数在所有 PowerShell 版本都必然静默失败”。某些声明形式可能更早报绑定错误，避免自动变量名才是稳定规则。

| 目标 | 原本应收到 | 当前实际结果 | 等级 |
| --- | --- | --- | --- |
| where.exe | `pnpm` | 无 pattern，输出帮助 | `F` |
| pnpm version | `--version` | 无子命令，输出 pnpm 帮助 | `F` |
| 三个 pnpm config | `config`, `get`, `<key>` | 三份相同无子命令帮助 | `F` |
| Node | `<probe.mjs>`, `<package-manager.js>`, `<desktop>` | 无脚本，进入交互等待；日志因等待结束才写而缺失 | `F/I` |
| Forge probe | 四次真实 spawnPackageManager | 没有运行结果 | `F`；不能归类 Forge 执行失败 |

call operator `&` 接受程序和独立参数；它不会把一个包含“程序+参数”的字符串再解析成命令。因此 `& $File @CommandArgs` 中 File 必须只表示 executable，不能把整条命令塞进去，也不应改成 `Invoke-Expression`。[Microsoft call operator](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_operators?view=powershell-7.5#call-operator-)

### 3.2 不应随改名遗留的缺口

| 项目 | 原脚本事实/风险 | 裁定 |
| --- | --- | --- |
| 位置参数 | 简单函数接受三个位置参数；目前数组字面量与预期一致，暂无第二个独立丢参数事实 | 新函数 `CmdletBinding(PositionalBinding=false)`，调用全部命名；数组显式 `[string[]]` |
| 数组展平 | splatting 将数组元素按位置展开；嵌套数组/隐式 string cast 可能改变元素 | 只接受一维 string 数组，拒绝 null、空字符串、NUL/CR/LF；运行前和 worker 内分别验证计数 |
| quoting | PowerShell/.NET native 参数与 `cmd /c` 是不同层次；字符串拼接可能引入二次解析 | exe 用 ArgumentList；cmd 只允许固定 ASCII pnpm 字面量，不支持任意 shell 参数 |
| stdout/stderr | `2>&1` 加 `ForEach-Object { "$_" }` 混流并改写原生输出形态 | 双流异步复制原始字节到不同文件；禁止从混合流解析 JSON |
| 超时 | 同步 `&` 无 watchdog；Node 等待使函数一直不能返回 | 每项 wall-clock 上限，包含 worker 启动；超时后清理同 job，禁止运行下一项 |
| 退出码 | `$LASTEXITCODE` 紧接正常 native 返回时可用；启动失败或其他 native 调用后可能是旧值 | 选定方案取目标 Process.ExitCode；启动失败 `exitCode=null`，不伪造 native 退出码 |
| 判断顺序 | 六项都运行后才综合判断；`ConvertFrom-Json` 在退出检查前 | 每项立即校验；Forge 首先判退出/超时/清理，再判 JSON schema |
| config 值 | 原脚本直接 config 只查两项 exit，未严格检查两个 `undefined` | 四个 pnpm 结果全部精确值，不接受帮助、空输出、多行内容 |
| 状态核验 | `verify-state.ps1` 使用 CRLF 的摘要与基线 LF 不一致 | 固定历史 LF 序列化，不能换算法后报告 node_modules 漂移 |
| ready 后执行 | 原脚本 `Read-Host GO` 后存在 package 分支；control 用模糊字符串判断 | R0-only 完全移除 package 分支，读取精确 control 版本/任务行；无交互继续开关 |

`$LASTEXITCODE` 是最近一个 native 程序或明确退出的脚本的退出值，不是所有 PowerShell 命令的通用状态。`$?` 与 `$ErrorActionPreference` 也不能替代 native 返回码。[Microsoft LASTEXITCODE](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-7.5#lastexitcode) PowerShell 7.3 以后的 native argument passing 有 Windows/Legacy 等差异，`.cmd` 属于需要特别注意的调用类型；下一任务记录 PowerShell 版本，不能只说“Windows 上一样”。[Microsoft parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.5#passing-arguments-to-native-commands)

## 4. 两种实现比较与唯一选择

| 维度 | A：改名后 `& $File @CommandArgs` | B：ProcessStartInfo（选定） |
| --- | --- | --- |
| exe | 改动少；依赖 PowerShell native 参数模式 | 绝对 exe + ArgumentList；参数不预加引号 |
| 无扩展名 | 受 PowerShell alias/function/脚本/PATH 优先级影响，必须额外排除遮蔽 | 不依赖 PowerShell命令发现；只允许 `pnpm`，明确通过系统 cmd 解析 |
| `.cmd` | PowerShell 有 batch 兼容处理，仍经 cmd quoting | 不能直接执行；使用受限 cmd adapter。任意 `.cmd` 路径在本函数中拒绝 |
| 空格/Unicode | 必须考虑 native passing 模式与 batch 二次解析 | exe 路径/参数由 .NET 保留；cmd 路径风险仍在，所以固定任务根和 literal pnpm 查询 |
| 双流 | 同步 `&` 简单重定向可以落盘，但对象流/编码和超时处理另需监督器 | 两条 BaseStream 同时 CopyToAsync 到文件，无顺序 ReadToEnd 死锁 |
| 退出码 | 必须立即保存 LASTEXITCODE；启动异常单列 | 原生 Process.ExitCode；与 supervisor 状态、超时分开 |
| 硬超时 | 原函数做不到；需增加 worker/watchdog | 父进程有界等待、job 终止、5 秒 drain/cleanup |
| 后代收口 | 只停 PowerShell job/父进程不保证 native 后代退出 | Windows Job + 启动门闩，生命周期覆盖 worker/native/Forge 后代 |
| Forge 同构性 | PowerShell pnpm 调用不是 Forge cross-spawn 本身 | direct pnpm 只是初筛；最后仍由原 Forge spawnPackageManager 作同构证明 |

**选择 B；不让执行方自行在 A/B 之间切换。** A 可以修复当前形参缺陷，但为了满足硬超时和后代收口仍要增添外围监督器，最终并不比 B 简单。B 的 job 支持代码是生命周期基础，不是 pnpm/产品架构改造。

`.ArgumentList` 由 .NET 转义并构造系统命令行，输入不要预加引号，也不能同时设置 `.Arguments`。唯独受限 cmd adapter 使用 `.Arguments`，因为 `cmd /c` 接收的是 shell 表达式；该表达式由四个精确允许值选择，不接收任意字符串。[ArgumentList](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.argumentlist)

重定向要求 `UseShellExecute=false`。同时先消费 stdout/stderr，再等待进程结束，防止子进程填满其中一条 pipe 后彼此等待。[RedirectStandardOutput](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.redirectstandardoutput) `Kill(true)` 后根进程 `HasExited` 或 `WaitForExit` 并不证明所有后代退出；本文使用 job active count 作为收口门禁。[Process.Kill](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process.kill)

## 5. 完整 Run-Captured 建议实现

下列**整个代码块**是一个可复制单元，包含函数所需的 job 类型与 worker；不需要另找未提供的 cleanup helper。仅限 Windows 11、PowerShell 7.4+ x64 的外部 R0 driver，`.NET` 必须具备 ArgumentList。不要在 Windows PowerShell 5.1 降级运行。类型首次编译与 Job API 权限需要由下一任务的 harness 前置检查确认；D14 没有执行 Add-Type。

函数有意只支持三个 executable labels：系统 where、裸 pnpm、固定 Node Forge probe。参数/路径由外层固定快照核验后提供。每次 `EvidenceDirectory` 必须全新且其父目录已经属于新任务。代码内部不生成 ready marker，不运行 package；返回 `transportOk` 仅表示捕获与收口成功，业务结果由第 6 节严格校验。

```powershell
# Proposed R0-only driver code. Do not execute during D14.
if (-not ('MarisR0Job' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public sealed class MarisR0Job : IDisposable {
    [StructLayout(LayoutKind.Sequential)] struct Basic {
        public long PerProcess, PerJob;
        public uint Flags;
        public UIntPtr MinWorkingSet, MaxWorkingSet;
        public uint ActiveLimit;
        public UIntPtr Affinity;
        public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct Io {
        public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes;
    }
    [StructLayout(LayoutKind.Sequential)] struct Extended {
        public Basic Basic; public Io Io;
        public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
    }
    [StructLayout(LayoutKind.Sequential)] public struct Accounting {
        public long UserTime, KernelTime, PeriodUserTime, PeriodKernelTime;
        public uint PageFaults, TotalProcesses, ActiveProcesses, TerminatedProcesses;
    }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateJobObjectW(IntPtr attrs, string name);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool SetInformationJobObject(SafeFileHandle job, int kind,
        ref Extended value, uint length);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool AssignProcessToJobObject(SafeFileHandle job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool QueryInformationJobObject(SafeFileHandle job, int kind,
        out Accounting value, uint length, IntPtr returned);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool TerminateJobObject(SafeFileHandle job, uint code);
    readonly SafeFileHandle handle;
    static Exception Failure() { return new InvalidOperationException("job_api_failed"); }
    public MarisR0Job(uint maxActive) {
        handle = new SafeFileHandle(CreateJobObjectW(IntPtr.Zero, null), true);
        if (handle.IsInvalid) { handle.Dispose(); throw Failure(); }
        var limits = new Extended();
        limits.Basic.Flags = 0x2000 | 0x8; // KILL_ON_JOB_CLOSE + ACTIVE_PROCESS
        limits.Basic.ActiveLimit = maxActive; // no breakaway flags
        if (!SetInformationJobObject(handle, 9, ref limits,
            (uint)Marshal.SizeOf<Extended>())) {
            handle.Dispose(); throw Failure();
        }
    }
    public void Attach(Process process) {
        if (!AssignProcessToJobObject(handle, process.Handle)) throw Failure();
    }
    public Accounting Read() {
        Accounting value;
        if (!QueryInformationJobObject(handle, 1, out value,
            (uint)Marshal.SizeOf<Accounting>(), IntPtr.Zero)) throw Failure();
        return value;
    }
    public void Stop() {
        if (!TerminateJobObject(handle, 124)) throw Failure();
    }
    public void Dispose() { handle.Dispose(); }
}
'@
}

function Run-Captured {
    [CmdletBinding(PositionalBinding = $false)]
    param(
        [Parameter(Mandatory)][ValidateSet('where-pnpm','pnpm','forge-probe')]
        [string]$ExecutableLabel,
        [Parameter(Mandatory)][string]$File,
        [Parameter(Mandatory)][string[]]$CommandArgs,
        [Parameter(Mandatory)][ValidateRange(1,3)][int]$ExpectedArgCount,
        [Parameter(Mandatory)][string[]]$ArgumentLabels,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$EvidenceDirectory,
        [Parameter(Mandatory)][ValidateRange(1,60)][int]$TimeoutSeconds
    )
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'
    if (-not $IsWindows -or $PSVersionTable.PSVersion -lt [version]'7.4' -or
        -not [Environment]::Is64BitProcess) { throw 'unsupported_driver_runtime' }
    if ($CommandArgs.Count -ne $ExpectedArgCount -or
        $ArgumentLabels.Count -ne $ExpectedArgCount) { throw 'argument_count_mismatch' }
    foreach ($item in $CommandArgs) {
        if ([string]::IsNullOrEmpty($item) -or $item -match '[\x00\r\n]') {
            throw 'invalid_argument'
        }
    }
    foreach ($label in $ArgumentLabels) {
        if ($label -notmatch '^[a-z0-9-]+$') { throw 'invalid_semantic_label' }
    }
    foreach ($pathValue in @($WorkingDirectory, $EvidenceDirectory)) {
        if (-not [IO.Path]::IsPathFullyQualified($pathValue)) { throw 'absolute_path_required' }
    }
    if (-not [IO.Directory]::Exists($WorkingDirectory) -or
        -not [IO.Directory]::Exists([IO.Path]::GetDirectoryName($EvidenceDirectory)) -or
        (Test-Path -LiteralPath $EvidenceDirectory)) { throw 'fresh_evidence_required' }
    $systemCmd = Join-Path ([Environment]::SystemDirectory) 'cmd.exe'
    $systemWhere = Join-Path ([Environment]::SystemDirectory) 'where.exe'
    $maxActive = 2; $maxTotal = 2
    switch ($ExecutableLabel) {
        'where-pnpm' {
            if ($File -ine $systemWhere -or $ExpectedArgCount -ne 1 -or
                $CommandArgs[0] -cne 'pnpm') { throw 'where_contract_mismatch' }
        }
        'pnpm' {
            $allowedQueries = @('--version', 'config get hoist-pattern',
                'config get public-hoist-pattern', 'config get node-linker')
            foreach ($item in $CommandArgs) {
                if ($item -cnotmatch '^[a-z-]+$') { throw 'cmd_token_rejected' }
            }
            if ($File -cne 'pnpm' -or
                ($CommandArgs -join ' ') -cnotin $allowedQueries) { throw 'pnpm_contract_mismatch' }
            if ($env:ComSpec -ine $systemCmd) { throw 'comspec_mismatch' }
            $maxActive = 3; $maxTotal = 3
        }
        'forge-probe' {
            if (-not [IO.Path]::IsPathFullyQualified($File) -or
                [IO.Path]::GetFileName($File) -ine 'node.exe' -or
                $ExpectedArgCount -ne 3) { throw 'node_contract_mismatch' }
            foreach ($item in $CommandArgs) {
                if (-not [IO.Path]::IsPathFullyQualified($item)) { throw 'probe_path_required' }
            }
            if (-not [IO.File]::Exists($CommandArgs[0]) -or
                -not [IO.File]::Exists($CommandArgs[1]) -or
                -not [IO.Directory]::Exists($CommandArgs[2])) { throw 'probe_input_missing' }
            $maxActive = 4; $maxTotal = 10
        }
    }
    if ($ExecutableLabel -ne 'pnpm' -and -not [IO.File]::Exists($File)) {
        throw 'executable_missing'
    }
    [void][IO.Directory]::CreateDirectory($EvidenceDirectory)
    $utf8 = [Text.UTF8Encoding]::new($false)
    $writeJson = {
        param([string]$Target, [object]$Value)
        $jsonText = ($Value | ConvertTo-Json -Depth 12 -Compress) + "`n"
        $bytes = $utf8.GetBytes($jsonText)
        $stream = [IO.File]::Open($Target, [IO.FileMode]::CreateNew,
            [IO.FileAccess]::Write, [IO.FileShare]::Read)
        try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
    }
    $commandId = [guid]::NewGuid().ToString('N')
    $safeStart = [ordered]@{
        schema='maris-r0-command-start-v1'; commandId=$commandId
        executableLabel=$ExecutableLabel; argumentCount=$CommandArgs.Count
        commandTokenCount=1+$CommandArgs.Count; argumentLabels=$ArgumentLabels
        timeoutSeconds=$TimeoutSeconds; startedAtUtc=[DateTime]::UtcNow.ToString('o')
    }
    & $writeJson (Join-Path $EvidenceDirectory 'start.json') $safeStart

    # No child can be launched before the parent assigns this worker to its job.
    $workerSource = @'
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$utf8Worker = [Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8Worker
$payloadLine = [Console]::In.ReadLine()
if ([string]::IsNullOrEmpty($payloadLine)) { exit 125 }
$payload = $payloadLine | ConvertFrom-Json
try {
    $nativeArgs = [string[]]@($payload.commandArgs)
    if ($nativeArgs.Count -ne $payload.expectedArgCount) { throw 'worker_argument_count' }
    $nativeInfo = [Diagnostics.ProcessStartInfo]::new()
    $nativeInfo.UseShellExecute = $false
    $nativeInfo.CreateNoWindow = $true
    $nativeInfo.WorkingDirectory = $payload.cwd
    if ($payload.label -eq 'pnpm') {
        # Only previously validated literal ASCII query tokens enter this shell string.
        foreach ($token in $nativeArgs) {
            if ($token -cnotmatch '^[a-z-]+$') { throw 'worker_cmd_token' }
        }
        $nativeInfo.FileName = $payload.systemCmd
        $nativeInfo.Arguments = '/d /s /v:off /c "pnpm ' + ($nativeArgs -join ' ') + '"'
    } else {
        $nativeInfo.FileName = $payload.file
        foreach ($token in $nativeArgs) { $nativeInfo.ArgumentList.Add($token) }
    }
    $dispatch = [ordered]@{
        commandId=$payload.commandId; executableLabel=$payload.label
        argumentCount=$nativeArgs.Count; argumentLabels=$payload.argumentLabels
        startedAtUtc=[DateTime]::UtcNow.ToString('o')
    }
    [IO.File]::WriteAllText((Join-Path $payload.evidence 'dispatch.json'),
        (($dispatch | ConvertTo-Json -Compress) + "`n"), $utf8Worker)
    $nativeProcess = [Diagnostics.Process]::new()
    $nativeProcess.StartInfo = $nativeInfo
    if (-not $nativeProcess.Start()) { throw 'native_start_failed' }
    $nativeIdentity = [ordered]@{
        commandId=$payload.commandId; pid=$nativeProcess.Id
        startTimeUtc=$nativeProcess.StartTime.ToUniversalTime().ToString('o')
        executableLabel=$payload.label
    }
    [IO.File]::WriteAllText((Join-Path $payload.evidence 'native-start.json'),
        (($nativeIdentity | ConvertTo-Json -Compress) + "`n"), $utf8Worker)
    # Only worker blocks; parent owns the wall-clock deadline and the entire job.
    $nativeProcess.WaitForExit()
    $nativeCode = $nativeProcess.ExitCode
    $nativeResult = [ordered]@{ commandId=$payload.commandId; exitCode=$nativeCode }
    [IO.File]::WriteAllText((Join-Path $payload.evidence 'native-result.json'),
        (($nativeResult | ConvertTo-Json -Compress) + "`n"), $utf8Worker)
    $nativeProcess.Dispose()
    exit $nativeCode
} catch {
    [Console]::Error.WriteLine('r0_worker_failed') # Never print raw exception paths.
    exit 125
}
'@
    $payload = [ordered]@{
        commandId=$commandId; file=$File; commandArgs=$CommandArgs
        expectedArgCount=$ExpectedArgCount; argumentLabels=$ArgumentLabels
        label=$ExecutableLabel; cwd=$WorkingDirectory; evidence=$EvidenceDirectory
        systemCmd=$systemCmd
    }
    $workerInfo = [Diagnostics.ProcessStartInfo]::new()
    $workerInfo.FileName = Join-Path $PSHOME 'pwsh.exe'
    $workerInfo.UseShellExecute = $false
    $workerInfo.CreateNoWindow = $true
    $workerInfo.WorkingDirectory = $WorkingDirectory
    $workerInfo.RedirectStandardInput = $true
    $workerInfo.RedirectStandardOutput = $true
    $workerInfo.RedirectStandardError = $true
    $workerInfo.StandardInputEncoding = $utf8
    foreach ($token in @('-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',
        [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($workerSource)))) {
        $workerInfo.ArgumentList.Add($token)
    }
    $workerInfo.Environment['MARIS_R0_COMMAND_ID'] = $commandId
    $worker = [Diagnostics.Process]::new(); $worker.StartInfo = $workerInfo
    $job = $null; $stdoutFile = $null; $stderrFile = $null
    $outPump = $null; $errPump = $null; $clock = [Diagnostics.Stopwatch]::StartNew()
    $started = $false; $attached = $false; $timedOut = $false
    $captureComplete = $false; $cleanupComplete = $false; $failure = $null
    $drainAttempted = $false
    $forcedCleanup = $false; $jobTotal = $null; $workerCode = $null; $nativeCode = $null
    try {
        $stdoutFile = [IO.File]::Open((Join-Path $EvidenceDirectory 'stdout.bin'),
            [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        $stderrFile = [IO.File]::Open((Join-Path $EvidenceDirectory 'stderr.bin'),
            [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
        $job = [MarisR0Job]::new([uint32]$maxActive)
        $started = $worker.Start()
        if (-not $started) { throw 'worker_start_failed' }
        $outPump = $worker.StandardOutput.BaseStream.CopyToAsync($stdoutFile)
        $errPump = $worker.StandardError.BaseStream.CopyToAsync($stderrFile)
        $job.Attach($worker); $attached = $true
        & $writeJson (Join-Path $EvidenceDirectory 'owner.json') ([ordered]@{
            commandId=$commandId; pid=$worker.Id
            startTimeUtc=$worker.StartTime.ToUniversalTime().ToString('o')
            executableLabel='powershell-r0-worker'; jobAttached=$true
        })
        $worker.StandardInput.WriteLine(($payload | ConvertTo-Json -Depth 8 -Compress))
        $worker.StandardInput.Close() # EOF to accidental interactive children.
        while (-not $worker.WaitForExit(50)) {
            if ($outPump.IsFaulted -or $errPump.IsFaulted) { throw 'capture_failed' }
            if ($stdoutFile.Length -gt 1MB -or $stderrFile.Length -gt 1MB) {
                throw 'output_limit_exceeded'
            }
            if ($job.Read().TotalProcesses -gt $maxTotal) { throw 'process_budget_exceeded' }
            if ($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
                $timedOut = $true; throw 'command_timeout'
            }
        }
        if ($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
            $timedOut = $true; throw 'command_timeout'
        }
        $workerCode = $worker.ExitCode
        $accounting = $job.Read(); $jobTotal = $accounting.TotalProcesses
        if ($jobTotal -gt $maxTotal) { throw 'process_budget_exceeded' }
        if ($accounting.ActiveProcesses -ne 0) { throw 'descendant_remaining' }
        $cleanupComplete = $true
        $pumps = [Threading.Tasks.Task[]]@($outPump, $errPump)
        $drainAttempted = $true
        if (-not [Threading.Tasks.Task]::WaitAll($pumps, 5000)) { throw 'drain_timeout' }
        $captureComplete = $true
        if ($stdoutFile.Length -gt 1MB -or $stderrFile.Length -gt 1MB) {
            throw 'output_limit_exceeded'
        }
    } catch {
        # Exception.Message may contain private paths; use only an allowlisted code.
        $knownCodes = @('worker_start_failed','capture_failed','output_limit_exceeded',
            'process_budget_exceeded','command_timeout','descendant_remaining','drain_timeout')
        $failure = if ($_.Exception.Message -cin $knownCodes) {
            $_.Exception.Message
        } else { 'harness_capture_failure' }
    } finally {
        if ($started -and -not $cleanupComplete) {
            try {
                $forcedCleanup = $true
                if ($attached) {
                    $job.Stop()
                    $cleanupClock = [Diagnostics.Stopwatch]::StartNew()
                    do {
                        $accounting = $job.Read(); $jobTotal = $accounting.TotalProcesses
                        if ($accounting.ActiveProcesses -eq 0) { $cleanupComplete = $true; break }
                        [Threading.Thread]::Sleep(25)
                    } while ($cleanupClock.ElapsedMilliseconds -lt 5000)
                } else {
                    # The unassigned worker is still gated, so it has no target children.
                    if (-not $worker.HasExited) { $worker.Kill() }
                    $cleanupComplete = $worker.WaitForExit(5000)
                }
            } catch { $cleanupComplete = $false }
        } elseif (-not $started) { $cleanupComplete = $true }
        if (-not $drainAttempted -and $null -ne $outPump -and $null -ne $errPump) {
            $drainAttempted = $true
            try {
                $captureComplete = [Threading.Tasks.Task]::WaitAll(
                    [Threading.Tasks.Task[]]@($outPump,$errPump), 5000)
            } catch { $captureComplete = $false }
        }
        if ($started) {
            try {
                if ($worker.HasExited) { $workerCode = $worker.ExitCode }
                $worker.StandardOutput.Close(); $worker.StandardError.Close()
                $worker.StandardInput.Close()
            } catch { $captureComplete = $false }
        }
        if ($null -ne $stdoutFile) { $stdoutFile.Dispose() }
        if ($null -ne $stderrFile) { $stderrFile.Dispose() }
        if ($null -ne $job) { $job.Dispose() } # KILL_ON_JOB_CLOSE last defence.
        $worker.Dispose()
    }
    $nativeResultFile = Join-Path $EvidenceDirectory 'native-result.json'
    if ([IO.File]::Exists($nativeResultFile)) {
        try {
            $nativeResult = Get-Content -LiteralPath $nativeResultFile -Raw | ConvertFrom-Json
            if ($nativeResult.commandId -cne $commandId -or
                ($nativeResult.exitCode -isnot [long] -and $nativeResult.exitCode -isnot [int])) {
                throw 'native_result_invalid'
            }
            $nativeCode = [int]$nativeResult.exitCode
            if (-not $timedOut -and $nativeCode -ne $workerCode) { throw 'exit_code_mismatch' }
        } catch { $failure = 'native_result_invalid' }
    } elseif ($null -eq $failure) { $failure = 'native_result_missing' }
    $fileHashes = [ordered]@{}
    foreach ($leaf in @('stdout.bin','stderr.bin','start.json','dispatch.json',
        'owner.json','native-start.json','native-result.json')) {
        $fullName = Join-Path $EvidenceDirectory $leaf
        $fileHashes[$leaf] = if ([IO.File]::Exists($fullName)) {
            (Get-FileHash -LiteralPath $fullName -Algorithm SHA256).Hash.ToLowerInvariant()
        } else { $null }
    }
    $result = [pscustomobject][ordered]@{
        schema='maris-r0-command-result-v1'; commandId=$commandId
        executableLabel=$ExecutableLabel; argumentCount=$CommandArgs.Count
        exitCode=$nativeCode; workerExitCode=$workerCode; timedOut=$timedOut
        captureComplete=$captureComplete; cleanupComplete=$cleanupComplete
        forcedCleanup=$forcedCleanup; totalOwnedProcesses=$jobTotal
        failureCode=$failure; elapsedMs=$clock.ElapsedMilliseconds; sha256=$fileHashes
        transportOk=($null -eq $failure -and -not $timedOut -and
            $captureComplete -and $cleanupComplete -and -not $forcedCleanup)
    }
    & $writeJson (Join-Path $EvidenceDirectory 'result.json') $result
    return $result
}
```

### 5.1 使用合同与限制

- Job Object 的 `KILL_ON_JOB_CLOSE` 不修改系统策略；关联失败时绝不向 worker 写 payload。worker 用 `-NoProfile -NonInteractive` 启动并在读取 payload 前不创建子进程，避免“先启动目标再关联 job”的竞态。只操作自己持有的 process/job handle，不按名字或易复用的 PID 盲杀。[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- 5 秒 cleanup 与最多 5 秒 drain 是命令 deadline 之后的收口预算，不算业务继续运行。`drainAttempted` 保证正常/失败路径合计只等待一次 drain，不能用 finally 再获得一个新的 5 秒窗口。清理或捕获无法证明完成，结果失败；close-job 只是兜底动作，不能把未证明的收口回写成通过。
- 1 MiB 是 R0 单流证据上限监测，50 ms 采样可能有短时超出；不是磁盘硬配额。它阻止帮助输出/意外 flood 被当有效结果。无 `ReadToEnd()` 先阻塞某条管道；文件先创建，任务中断也尽量保留已写字节。
- worker 的 native `WaitForExit()` 由独立父进程 watchdog 约束，不会使 controller 同步等待失去控制。stdin 在放行后关闭，误启动的 Node 无脚本时也不能无限借用用户终端输入。
- `exitCode` 只记录目标真实退出码；超时杀掉 worker 而没拿到 native-result 时保持 null。`workerExitCode=124/125` 不可冒充 pnpm/Node 的退出码。`transportOk=true` 且 `exitCode!=0` 仍是失败。
- 原生 where/Node 支持路径空格和 Unicode，参数不预加引号。Windows cmd 的 `%`、`!`、`&`、`|`、括号等另有解析语义；本方案只向 cmd 传固定 ASCII 查询词，不提供任意 batch 引号算法。
- task root 和 shim native 目标继续使用原先固定的短 ASCII 路径。shim 内是带双引号的绝对 native 路径、`%*`、下一行 `exit /b %ERRORLEVEL%`，不能放入括号块后依赖提前展开的 errorlevel。
- 此方案不声称普通 cmd 与 Forge cross-spawn 的实现完全相同。第 6 项依旧使用真实 Forge `spawnPackageManager`，保留其 PATH/PATHEXT/cwd 和已安装 cross-spawn 的解析；不 patch node_modules，不替换成 native 直调。

命名调用示例（仅建议，不在 D14 执行）：

```powershell
$check = Run-Captured -ExecutableLabel 'pnpm' -File 'pnpm' `
    -CommandArgs ([string[]]@('config','get','hoist-pattern')) `
    -ExpectedArgCount 3 -ArgumentLabels @('config','get','hoist-pattern') `
    -WorkingDirectory $desktopRoot -EvidenceDirectory $freshCommandDirectory `
    -TimeoutSeconds 15
if (-not $check.transportOk -or $check.exitCode -ne 0) {
    throw 'r0_command_failed' # Outer controller records failure and exits; no next check.
}
```

## 6. 六项参数与结果 evidence 合同

### 6.1 计数定义与任务卡勘误

`argumentCount` 一律不计 executable token。对 Node，它包含 `.mjs` 路径：Node 收到三个参数，probe 的 `process.argv` 长度应为 4，其中第 0 项是 Node 本身；`process.argv.slice(2)` 长度为 2。三个 config 查询一律是 3 参数/4 command tokens。**四个实参的要求不能照字面实施**，需要总控在下一任务中纠正此处规范冲突。

| 顺序 | executable label | CommandArgs（语义） | argumentCount / commandTokenCount | 硬超时 | 输出合同 |
| --- | --- | --- | --- | --- | --- |
| Q1 | where-pnpm | `pnpm` | 1 / 2 | 10 s | exit 0；首个完整输出行精确为本任务 shim 的绝对路径；任务根为 ASCII，按首行字节核对 |
| Q2 | pnpm | `--version` | 1 / 2 | 15 s | exit 0；唯一一行精确 `12.7.0` |
| Q3 | pnpm | `config`, `get`, `hoist-pattern` | **3 / 4** | 15 s | exit 0；唯一一行精确字符串 `undefined` |
| Q4 | pnpm | `config`, `get`, `public-hoist-pattern` | **3 / 4** | 15 s | exit 0；唯一一行精确字符串 `undefined` |
| Q5 | pnpm | `config`, `get`, `node-linker` | **3 / 4** | 15 s | exit 0；唯一一行精确 `hoisted` |
| Q6 | forge-probe | `<probe.mjs>`, `<package-manager.js>`, `<desktop-root>` | 3 / 4 | 60 s | exit 0；严格 Forge JSON；内部四次调用全部对应固定 args 和值 |

所有 Qn：stdout/stderr 分别落盘；`result.json` 含真实 exit、timeout、transport、cleanup、强制收口、文件摘要。stderr 正常预期为空；非空必须停止并分类，不能一边把警告混入 JSON 一边通过。Q1 的多条 where 匹配可以包含旧 shim，但首项必须是本任务 shim；不能因第二项存在旧 shim 误判，也不能只搜索输出里有没有 `pnpm.cmd`。

编码不混用：原始双流按 bytes 保存。Q1 的冻结任务首路径与 Q2～Q5 预期值都是 ASCII，直接比对字节和可选单个 CRLF/LF，避免将 Windows OEM 输出误用 UTF-8 解码；Q1 后续含个人/Unicode路径的行仅原样保留，不依赖解码判断首项。Q6 为 Node 写出的 UTF-8 JSON，使用严格 UTF-8 decoder；非法字节停止。worker 的 JSON 输入显式使用 UTF-8，以保留 exe 参数中的空格和 Unicode。

每条命令都有 controller 的 `start.json` 与 worker 的 `dispatch.json`，比对 command ID、count、语义 labels。两个记录只能证明送入 native dispatch 的数组一致，**不能单凭计数文件证明第三方程序内部 argv**。因此同时要求精确结果；Node probe 另写它实际收到的 argv count 证据。不得输出假造的“where 已回报 argv=1”。

### 6.2 新 probe 的窄改动合同

旧 probe 原样保留；新任务只在新的 evidence 子目录生成新 probe，逻辑仍是按顺序调用真实 `spawnPackageManager` 四次：

1. import 前检查 `process.argv.length===4`，核验两个绝对输入与 controller 固定清单。把 `nodeArgumentCount=3`、`scriptArgumentCount=2`、三个语义标签写到**独立** probe receipt，不写路径值。
2. 四个 args 数组固定为 `['--version']`、`['config','get',key]`；每个调用之前向外部 evidence 写 count/labels/序号，不能只在全部成功后写一条摘要。
3. 使用原 module 的 `spawnPackageManager(PACKAGE_MANAGERS.pnpm, commandArgs, {cwd: desktopRoot, ...})`；保留 `pm.executable='pnpm'`，禁止直接 pnpm-native 绕过 shim。
4. 每项独立原始 stdout/stderr 与 exit evidence：现装 cross-spawn-promise 成功只返回 stdout，内部 stderr 会被收集却不返回。使用其透传的 `stdio: ['ignore', stdoutFd, stderrFd]` 将两个已打开的**不同文件描述符**交给真实 spawn（已静态核对其将 opts 转发 cross-spawn），并设置 `windowsHide: true`；resolve 后读 stdout 文件并按原 Forge `.trim()` 规则取值。返回的库字符串此时为空，不能拿它作值。reject 时按 error 类型记录 code/signal；启动失败无 native code 写 null，禁止默认 0。四次 promise resolved 才记录 exit 0。日志 fd 在 finally 关闭，任何非空 stderr 停止。这是捕获配置，不是替换 launcher；动态兼容仍为 U。
5. 使用每次 10 秒的 `AbortSignal` 作为内部辅助上限；Q6 外层 60 秒 job deadline 是强制后代收口保证。abort 必须停止循环，不运行下一个查询，不能只用 Promise.race 留下未收口子进程。
6. 最终 stdout 只写一次 JSON，严格四个字符串字段：`version`、`hoistPattern`、`publicHoistPattern`、`nodeLinker`。stderr/receipt/调试输出独立保存。

成功 JSON 只能是以下值集合，字段顺序不限：

```json
{"version":"12.7.0","hoistPattern":"undefined","publicHoistPattern":"undefined","nodeLinker":"hoisted"}
```

### 6.3 解析顺序

1. 检查 command result 存在、schema 和 command ID 正确；timeout=false、captureComplete=true、cleanupComplete=true、forcedCleanup=false、transportOk=true、exitCode=0。
2. 检查 stdout 非空且不超 1 MiB、stderr 为空、文件 SHA-256 匹配；Q1～Q5 只允许一个终止 CRLF/LF，不用宽泛 `Trim()` 抹掉多行帮助或额外内容。
3. Q6 用 `System.Text.Json.JsonDocument` 枚举顶层属性：根必须 Object，恰有四个**唯一且大小写精确**字段；用属性枚举检测重复键，不能依赖 ConvertFrom-Json 覆盖重复属性。全部值必须 Json String 且逐项等于上述值，拒绝数字、null、unknown fields、尾随多段 JSON、comments 和 trailing comma。
4. 检查 probe receipt 与四个子命令独立证据，前后 snapshot 和环境不变性通过，job active count 为 0。
5. 全部满足后 controller 才原子生成 result 与 ready marker；marker 含新任务 ID、control hash、源码/工具/环境配方/evidence hash、`packageAttempt='0/1'`。使用 create-new 或 temporary→rename，已有 marker 不能覆盖。

帮助输出即使 exit=0，也不满足 Q2～Q5 精确值或 Q6 JSON schema；Q1 帮助行也不满足绝对路径和首项合同。没有任何以“输出里包含版本号”判断成功的分支。

## 7. R0-only 次序、预算与现场不变性

### 7.1 只读起点

下一任务由总控命名并冻结新 manifest，D14 不创建。开始时严格顺序：

1. 读最新 control，确认本任务唯一负责人以及只授权 R0；复算**D14 被接受后新生成**的任务起点，不能用旧 D14 manifest 当新执行快照。
2. 复算 E4/R1 source 198 项、C source copy 198 项；旧 E4 evidence 26 项、R1 evidence 14 项及 controller/probe/shim hashes 全部不变。
3. 验证 Node/pnpm native/lock/`.modules.yaml`、Electron exe/73 文件 dist、Playwright/Forge 版本和 package 安装快照。node_modules 使用原算法：相对路径、bytes、单文件 SHA-256 排序，以 **LF** 连接；12,451 files、570,581,590 bytes、聚合摘要 `f06ce306456134f7f78176e64d3f9a7e54133607d3e9202ff6bb1a9fcbf800c7`。不得以 CRLF 算出不同值后“取较像的一个”。
4. 九个虚拟污染 marker 9/9；out、`.maris-staging`、transition artifacts、旧任务 owned process 全为 0。读取被拒绝时停止/按新任务已授权的只读权限处理，不改 ACL。
5. 记录用户/系统 PATH 的摘要、原进程 PATH 摘要及完整环境的受限快照摘要。原始环境不写入项目文档，避免泄密。

### 7.2 fresh evidence 与单会话

- `<task-root>/<new-r0-id>` 必须不存在；只创建新目录。E4、`r1-pnpm-resume`、旧 logs/controller/probe/shim 都不覆盖。新 controller 不复制旧 ready 后 package 分支。
- 复制旧 shim 或重建同字节 shim前，核验旧内容/hash、pnpm native hash `3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce` 与 53,373,952 bytes；目标必须是既有固定 native exe，不能解析用户 pnpm/store。
- shim 只有三行语义：`@echo off`、带引号绝对 native + `%*`、`exit /b %ERRORLEVEL%`。不写额外日志到 stdout，不添加安装/更新分支。新目标地址不变时优先按字节复制并核验 hash，不为了换行风格重写。
- 一个持续 controller 会话内只构造一次 PATH：新 shim dir + 固定 Node dir + 原 PATH 原顺序；维持相同 cwd、PATHEXT、ComSpec、Electron cache 和 npm/pnpm 相关配置环境。所有 Qn 从该会话派生，调用前后检查 PATH digest。
- 不更改用户/系统 PATH；不运行 pnpm setup/Corepack enable/global install。`$PSHOME` 只读用于定位相同 pwsh；不将任何自动变量改作任务变量。

### 7.3 启动和时间预算

| 单元 | logical cell 次数 | 目标/worker 最大进程数 | 上限 |
| --- | --- | --- | --- |
| harness 前置 | 一次静态语法检查；一次 synthetic lifecycle smoke | 预留最多 6 个任务进程；具体 fixture 由下一卡列明 | 30 s；只写新 evidence，不调用 pnpm/Forge |
| Q1 | 1 | worker + where = 2 | 10 s + 最多 10 s 收口 |
| Q2～Q5 | 各 1 | 每项 worker + cmd + pnpm-native = 3，共 12 | 每项 15 s + 最多 10 s 收口 |
| Q6 | 1；内部四次查询各 1 | worker + Node + 四组 cmd/pnpm-native = 10 | 60 s；内部每项 10 s；最多 10 s 收口 |
| 合计 | 最多 6 个 R0 logical cells | R0 最多 24 个进程；含 controller 1、harness 6，任务总上限 31 | 成功路线 Qn 上限合计 130 s，不含静态 hash |

逻辑 cell 数和 OS process 数必须分开；不能报告“六次进程”忽略 worker、cmd 和 Forge 后代。原生组件意外生成额外进程时停止，不能增加预算让它悄悄通过。Job 的 active 上限与累计监测同时使用，累计超标是失败。

harness smoke 必须在 Q1 之前完成，针对**同一监督组件**验证：含空格/中文参数能原样回显、双流同时输出且非零 native exit 保真、超时进程和它的后代全收口。可以用专用 synthetic PowerShell worker fixture，不能调用或伪装 pnpm/Forge，不得扩大正式 Run-Captured 的三项 allowlist；静态代码检查和支持组件测试的结果不能计入 Qn passed。若无法在冻结的 smoke 预算内实现，先交总控调整，不能跳过后代清理验证。

任何 Qn 失败立即写失败总结并退出；后续 Qn、package/P1/P2 均为 `not_run`。耗时超过五分钟的 node_modules 摘要复算，开始前更新状态和检查点；每十分钟心跳。两个检查点无新输出按协作规则安全停止，不重复执行旧 cell。

### 7.4 成功/失败必须保留的内容

- 启动前安全 label/count、worker dispatch、target PID/start time 和 Job ownership；不记录未脱敏完整命令行。
- 每项原始双流、target exit 或 null、worker exit、timedOut、强制终止标志、job 总进程数、cleanup 与捕获是否完成；旧原始内容不改。
- Forge probe 实收 argv 计数、四项内部查询 receipts、schema 检查结果和原始双流摘要。
- 新/旧 source、lock、node_modules、工具/dist、污染 marker、PATH 和环境摘要前后一致；out/staging/transition 和 owned process=0。
- 新 evidence manifest 不包括自己；规定相对路径顺序、LF、UTF-8 无 BOM、末尾换行算法。对异常只记录分类码，完整私有路径只能保留在受限外部原件。
- 成功只生成 `R0_READY_PACKAGE_0_OF_1`。失败生成 `R0_FAILED_PACKAGE_NOT_RUN`，保留首失败及部分日志，不生成 ready。

### 7.5 故障分类

| 观察结果 | 分类 | 可得结论 |
| --- | --- | --- |
| 参数计数、AST、Add-Type、job attach、写日志或 worker 启动失败，native dispatch 尚未发生 | harness_setup_failure | 被测 pnpm/Forge 未运行；不能扣 package 次数或声称产品失败 |
| dispatch 已发生，但双流/timeout/收口坏了 | harness_runtime_failure | 可能执行了目标；本次不能给通过结论，禁止按 setup error 自动重放 |
| where 首项错误、固定 hash/marker/PATH 变化、目标不可达 | environment_failure | 环境不符合冻结；不更改系统来继续 |
| 参数/解析正确，pnpm native 返回非零或值不符 | pnpm_preflight_failure | R0 确实失败；退出码+双流证据交总控，不自动归因版本 bug |
| Q1～Q5 通过，Forge probe 内真实 spawn 非零/值不符 | forge_preflight_failure | 支持 Forge调用链或其环境差异；与 probe 自己 import/schema/写文件错误分开 |
| probe 导入路径、argv/schema 或捕获适配代码错误 | harness_probe_failure | 并非 Forge 产品缺陷；若已 spawn，下次重放仍需总控授权 |

## 8. R0-ready 后的 package-only 交接

**可以由总控另立 package-only 任务，但以下证据缺一不可：**

1. 总控接受 D14 的计数勘误、Run-Captured、shim/Forge捕获和预算；下一 R0 任务版本明确。
2. Q1～Q6 及内部四项 Forge 查询全通过，原始 evidence、严格 schema、退出码、count 与摘要都存在。
3. 源码/依赖/lock/node_modules/工具/73 dist/9 marker 及旧 evidence 不变；所有 owned process、out、staging、transition 为 0。
4. ready marker 与最终 result、manifest 一致；R0 已 finished，package 仍 0/1。
5. 新任务明确只运行正式 wrapper的一次 package 及必要 package 后静态验收；P1/P2 是否另派由总控决定，不能顺带承接旧授权。
6. 新任务从保留的环境配方构造 PATH，记录原 PATH 尾部及影响 pnpm 的 cwd、PATHEXT、ComSpec、npm config 的摘要。新父会话与 R0 不同，报告必须写“等价重建且摘要匹配”，不能写“继承同一个已退出进程”。若环境发生变化，先停回总控，不自行全量重跑 R0或修改永久 PATH。
7. 总控明确在 package-only 开始前是否许可一次最小 where/Forge复核及其独立预算；没有该条时不能擅自重复 Qn。基于时间间隔/配置变化决定，避免对新会话环境作无证据保证。

ready marker 只是证据，不是自动执行开关。新的 package-only controller 必须重新读取最新 control，旧任务卡中的 GO/package 代码不能恢复使用。

## 9. package wrapper 是否应持久修改

[当前 wrapper](../apps/desktop/scripts/package-desktop.mjs) 通过 `createRequire` 定位 Forge CLI，以 `process.execPath` 启动它，保持 cwd，stage 后在 finally cleanup。E4 在 pnpm 系统检查失败，说明 wrapper 对外部 PATH 有依赖；R1 的参数缺陷发生在 wrapper 前，不能证明 wrapper 需要第二次修复。

**当前 R0 前不改 wrapper 或产品。** 任务专属 PATH 是明确声明的验收环境，能证明“在固定环境中可打包”，但不能证明“普通开发者直接运行 package 一定成功”。报告必须保留这个开发体验缺口，不能把 task-owned shim 藏掉。

以下任一触发后，才单独提出持久工具链任务：

- R0 与 package 真正通过后，正常支持的开发者环境仍可重复命中错误 pnpm；
- 干净 CI/新设备需要每次手动制造私有 shim 才能打包；
- 团队正式要求 package wrapper 独立于调用者 PATH，并冻结受支持 pnpm 的供应/校验/错误提示合同；
- 独立验收证明确有 executable shadowing 或版本漂移影响可复现构建。

届时可比较 repo-owned launcher/显式包管理器路径与受控 PATH，补上版本/完整性/跨环境测试。禁止永久写入本机任务根或个人绝对路径，禁止 wrapper 自动修系统 pnpm，禁止偷偷安装工具。该任务应由执行方实现、测试方验证、总控冻结；D14 只交触发条件。

## 10. 流程复盘：把 driver 自检放在 cell 之前

“一次失败即停止”保留了原始现场，也避免在错误环境下不断重打包。但把 driver 形参冲突、日志写入失败和被测产品失败统一计为同一种 cell failure，会让不触及产品的 setup 错误不断升级成新一轮完整任务。

建议未来任务显式设置两个阶段：

- **Harness preparation**：AST、参数合同、工具定位、证据目录、worker/job及 synthetic 超时收口自检。只有证明没有进入被测命令、产品/环境不变、owned process=0 时，可在原任务预授权范围内最多进行一次 driver-only 修正并保留 v1/v2 两份 evidence。不得覆盖原错误，也不消耗产品 package 预算。
- **Target cell**：在 native dispatch/目标启动前写 attempt marker；启动后失败或是否启动不明确都停止，不享受 setup 重试豁免。R0 某项失败不能在同卡改配置后重跑；package 仍严格一次。

这只是以后任务的流程建议。**本轮 E4-R1 不能追溯套用这项豁免**：where/pnpm/Node 已经被启动，旧 control 明确要求停止；D14 也没有被授权修复或重跑。下一 R0 需要总控新的授权。

## 11. 推荐冻结项

- **P4-D14-F01**：`P4-E4-R1-R0-DRIVER-ARGS-001` 分类为 evidence driver 参数冲突，未形成产品/Forge恢复方案反例。
- **P4-D14-F02**：禁用自动变量名作业务参数，所有调用使用命名参数和一维 string 数组；不使用 Invoke-Expression。
- **P4-D14-F03**：config 为 argumentCount=3 / commandTokenCount=4；总控修正任务卡“四参数”措辞，禁止为凑计数添加参数。
- **P4-D14-F04**：唯一采用本文 ProcessStartInfo方案；exe 使用 ArgumentList，cmd 仅接受四个固定 pnpm 查询，拒绝任意 batch 输入。
- **P4-D14-F05**：worker 先纳入无 breakaway 的任务 Job，再放行 native；关联失败不运行目标，清理不使用进程名。
- **P4-D14-F06**：stdout/stderr 独立异步落盘；保留真实 native exit，启动失败/无法获得退出值时为 null；supervisor code 分开。
- **P4-D14-F07**：每次 dispatch 前写安全 executable label、count 和语义标签；worker 二次核验；不把发送计数冒充第三方 argv 回报。
- **P4-D14-F08**：Q1～Q6 顺序固定、每项一次、立即校验；任何失败阻止后续项与 ready marker。
- **P4-D14-F09**：Q1/Q2～5/Q6 上限分别 10/15/60 秒，cleanup≤5秒、drain≤5秒；超时与残留进程均失败。
- **P4-D14-F10**：R0 24 个进程预算，含 controller 和 harness 上限31；Forge内部四项各一次，超预算停止。
- **P4-D14-F11**：Q1 首项精确 shim，pnpm四值精确，非空stderr停止；帮助输出不算成功，即使退出码0。
- **P4-D14-F12**：Forge exit0和传输/清理通过后才解析 JSON；四个唯一字符串字段，拒绝重复键、额外字段、类型错误与污染输出。
- **P4-D14-F13**：最后一项保留已安装 Forge真实 spawnPackageManager；新 probe只补 argv/双流证据，不 patch node_modules或改为native直调。
- **P4-D14-F14**：E4/R1原始 evidence、driver、shim、probe保留只读；新目录 create-new，禁止覆盖失败现场。
- **P4-D14-F15**：新任务先复算 D14后的新起点、198 source、旧26/14 evidence、工具、lock、node_modules、73 dist、9 marker与零残留。
- **P4-D14-F16**：node_modules聚合摘要沿用原LF算法；CRLF诊断差异不能误记内容漂移。
- **P4-D14-F17**：单持续会话一次构造进程级 PATH，固定其余环境；用户/系统PATH、系统pnpm不变。
- **P4-D14-F18**：只有六项结果、严格schema、不变性与收口全通过才写 `R0_READY_PACKAGE_0_OF_1` 并退出；driver没有package分支。
- **P4-D14-F19**：R0-ready不能自动授权package；package-only由总控另立，重建环境不得冒称继承已经退出的R0进程。
- **P4-D14-F20**：当前不修改wrapper/产品；task-owned PATH限制在验收环境，普通开发者体验单独登记触发后续工具链任务。
- **P4-D14-F21**：未来可预授权一次无目标执行的harness修正；本轮不追溯授权，不重启E4-R1，不创建D14-R1或P4-C12。

## 12. 仍需总控裁定与验收限制

1. 接受 config 实参 3、命令 tokens 4 的勘误；这是下一任务可以执行的前置规范修正。
2. 接受唯一捕获实现及 Windows Job/worker 边界；下一卡绑定 PowerShell具体版本，并授权仅在fresh evidence中做支持组件synthetic自检。若无法满足，暂停路线，不临场退回无限等待的call operator。
3. 接受新probe独立双流捕获方式与严格JSON；规定其源码/hash作为新的任务产物，旧probe保持不变。
4. 冻结新任务目录、31进程总上限、各项deadline，以及是否为harness前置错误预授权一次保留现场的修正。
5. 决定R0-ready后是否另立package-only，以及新会话前最小环境复核的具体预算。无新授权不执行package。
6. 普通开发者打包体验记录为待验证；何时将其升级为持久wrapper工具链任务，由总控按第9节触发条件决定。

本文完成的是只读裁定与可复制建议代码，不是 R0 通过证明。未动态验证 .NET/Job在当前宿主中的权限与运行、双流/超时/后代收口、六项预检、新probe、package或P1/P2。技术顾问交付到 `review / finished` 后停止，后续执行和最终验收仍由总控授权。
