$ErrorActionPreference = 'Stop'
$diagnosticRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$expectedRoot = [IO.Path]::GetFullPath('D:\CodeX_gap\wife-system\docs\coordination\diagnostics\p4-d15')
if ($diagnosticRoot -ne $expectedRoot) { throw 'd15_wrong_root' }
$resultRoot = Join-Path $diagnosticRoot 'results'
if (Test-Path -LiteralPath $resultRoot) { throw 'd15_first_results_already_exist_no_rerun' }
foreach ($item in Get-ChildItem -LiteralPath $diagnosticRoot -Force -Recurse) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'd15_reparse_not_allowed' }
}
$nodeExe = 'C:\MarisLazyR5\R5-20261002-222300\tools\node\node.exe'
$vitestCli = 'C:\MarisLazyR5\R5-20261002-222300\workspace\node_modules\vitest\vitest.mjs'
$manifest = Get-Content -LiteralPath (Join-Path $diagnosticRoot 'probe-source.sha256')
foreach ($line in $manifest) {
    $parts = $line -split "`t"
    if ($parts.Count -ne 2) { throw 'd15_bad_frozen_manifest' }
    $target = [IO.Path]::GetFullPath((Join-Path $diagnosticRoot $parts[0]))
    if (-not $target.StartsWith($diagnosticRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'd15_manifest_escape' }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $parts[1]) { throw 'd15_probe_source_changed' }
}
New-Item -ItemType Directory -Path $resultRoot | Out-Null
$sessionTimer = [Diagnostics.Stopwatch]::StartNew()
$sessionResults = @()
$sessionComplete = $false
try {
    foreach ($probe in @('p1', 'p2', 'p3')) {
        if ($sessionTimer.ElapsedMilliseconds -ge 60000) { throw 'd15_session_deadline' }
        $startInfo = [Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $nodeExe
        $startInfo.WorkingDirectory = $diagnosticRoot
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $startInfo.Environment['P4_D15_PROBE'] = $probe
        $startInfo.Environment['P4_D15_RESULT_FILE'] = Join-Path $resultRoot ($probe + '.json')
        foreach ($argument in @($vitestCli, 'run', '--config', (Join-Path $diagnosticRoot 'vitest.config.mjs'))) {
            $startInfo.ArgumentList.Add($argument)
        }
        $process = [Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        $targetTimer = [Diagnostics.Stopwatch]::StartNew()
        $targetStartedUtc = [DateTime]::UtcNow.ToString('o')
        $timedOut = $false
        try {
            if (-not $process.Start()) { throw 'd15_process_start_failed' }
            $rootPid = $process.Id
            $stdoutTask = $process.StandardOutput.ReadToEndAsync()
            $stderrTask = $process.StandardError.ReadToEndAsync()
            while (-not $process.WaitForExit(20)) {
                if ($targetTimer.ElapsedMilliseconds -ge 15000 -or $sessionTimer.ElapsedMilliseconds -ge 55000) {
                    $timedOut = $true
                    $process.Kill($true)
                    break
                }
            }
            if (-not $process.WaitForExit(2000)) { throw 'd15_owned_process_not_closed' }
            if (-not [Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask), 2000)) { throw 'd15_streams_not_closed' }
            $exitCode = $process.ExitCode
            # Preserve first streams separately; redact only known local roots.
            $stdout = $stdoutTask.Result.Replace($diagnosticRoot.Replace('\','/'), '<D15_ROOT>').Replace($diagnosticRoot, '<D15_ROOT>')
            $stderr = $stderrTask.Result.Replace($diagnosticRoot.Replace('\','/'), '<D15_ROOT>').Replace($diagnosticRoot, '<D15_ROOT>')
            $externalRoot = 'C:\MarisLazyR5\R5-20261002-222300'
            $stdout = $stdout.Replace($externalRoot.Replace('\','/'), '<R5_ROOT>').Replace($externalRoot, '<R5_ROOT>')
            $stderr = $stderr.Replace($externalRoot.Replace('\','/'), '<R5_ROOT>').Replace($externalRoot, '<R5_ROOT>')
            [IO.File]::WriteAllText((Join-Path $resultRoot ($probe + '.stdout.log')), $stdout, [Text.UTF8Encoding]::new($false))
            [IO.File]::WriteAllText((Join-Path $resultRoot ($probe + '.stderr.log')), $stderr, [Text.UTF8Encoding]::new($false))
            $workerPid = $null
            $workerExited = $null
            $receiptFile = Join-Path $resultRoot ($probe + '.json')
            if (Test-Path -LiteralPath $receiptFile) {
                $receipt = Get-Content -LiteralPath $receiptFile -Raw | ConvertFrom-Json
                $workerPid = $receipt.workerPid
                if ($receipt.workerParentPid -ne $rootPid) { throw 'd15_worker_ownership_unknown' }
                $workerExited = $null -eq (Get-Process -Id $workerPid -ErrorAction SilentlyContinue)
            }
            $run = [ordered]@{ probe=$probe; invocation=1; startedUtc=$targetStartedUtc; durationMs=$targetTimer.ElapsedMilliseconds;
                exitCode=$exitCode; timedOut=$timedOut; rootPid=$rootPid; rootExited=$process.HasExited;
                workerPid=$workerPid; workerExited=$workerExited; stdoutBytes=([Text.Encoding]::UTF8.GetByteCount($stdout));
                stderrBytes=([Text.Encoding]::UTF8.GetByteCount($stderr)); testTimeoutMs=10000; processDeadlineMs=15000 }
            $sessionResults += $run
            $run | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resultRoot ($probe + '.process.json')) -Encoding utf8
            Write-Output ($run | ConvertTo-Json -Compress)
            if ($timedOut -or $exitCode -ne 0 -or $workerExited -ne $true) { throw 'd15_first_nonclean_result_stop' }
        } finally {
            if ($process.Id -and -not $process.HasExited) {
                $process.Kill($true)
                if (-not $process.WaitForExit(2000)) { throw 'd15_finally_owned_process_not_closed' }
            }
            $process.Dispose()
        }
    }
    $sessionComplete = $true
} finally {
    [ordered]@{ completed=$sessionComplete; actualInvocations=$sessionResults.Count; durationMs=$sessionTimer.ElapsedMilliseconds;
        sessionDeadlineMs=60000; targets=$sessionResults; retries=0; productStarts=0; electronStarts=0; packages=0 } |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $resultRoot 'session.json') -Encoding utf8
}
