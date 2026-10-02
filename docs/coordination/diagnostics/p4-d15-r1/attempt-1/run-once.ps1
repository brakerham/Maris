$ErrorActionPreference = 'Stop'
$ownRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$expectedRoot = 'D:\CodeX_gap\wife-system\docs\coordination\diagnostics\p4-d15-r1\attempt-1'
if ($ownRoot -ne $expectedRoot) { throw 'd15_r1_wrong_root' }
foreach ($item in Get-ChildItem -LiteralPath (Split-Path $ownRoot) -Force -Recurse) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'd15_r1_reparse' }
}
$control = Get-Content -LiteralPath 'D:\CodeX_gap\wife-system\docs\coordination\control.md' -Raw
if (-not $control.Contains('2026-10-03T01:07:00+08:00')) { throw 'd15_r1_control_changed' }
$firstRoot=Join-Path (Split-Path $ownRoot) 'attempt-0'
$gate=Get-Content -LiteralPath (Join-Path $firstRoot 'results/pre-main-correction-gate.json') -Raw | ConvertFrom-Json
$audit=Get-Content -LiteralPath (Join-Path $firstRoot 'end-audit.json') -Raw | ConvertFrom-Json
if (-not $gate.parentMatchesOwnedRoot -or -not $gate.rootExited -or -not $gate.workerExited -or
    -not $gate.sequenceComplete -or $gate.mainImportRequests -ne 0 -or -not $audit.passed) { throw 'd15_r1_correction_gate' }
foreach($line in Get-Content -LiteralPath (Join-Path $firstRoot 'delivery.sha256')) {
    $parts=$line -split "`t"
    $firstFile=[IO.Path]::GetFullPath((Join-Path $firstRoot $parts[0]))
    if (-not $firstFile.StartsWith($firstRoot+'\') -or
        (Get-FileHash -LiteralPath $firstFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $parts[1]) { throw 'd15_r1_first_evidence_changed' }
}
foreach ($line in Get-Content -LiteralPath (Join-Path $ownRoot 'probe-source.sha256')) {
    $parts = $line -split "`t"
    if ($parts.Count -ne 2) { throw 'd15_r1_bad_manifest' }
    $targetPath = [IO.Path]::GetFullPath((Join-Path $ownRoot $parts[0]))
    if (-not $targetPath.StartsWith($ownRoot + '\')) { throw 'd15_r1_manifest_escape' }
    if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $parts[1]) { throw 'd15_r1_source_changed' }
}
$resultRoot = Join-Path $ownRoot 'results'
if (Test-Path -LiteralPath $resultRoot) { throw 'd15_r1_first_results_exist_no_rerun' }
New-Item -ItemType Directory -Path $resultRoot | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
function Write-New([string]$File, [string]$Value) {
    $stream = [IO.File]::Open($File, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $bytes=$utf8.GetBytes($Value); $stream.Write($bytes); $stream.Flush($true) } finally { $stream.Dispose() }
}
$controllerFile = Join-Path $resultRoot 'controller.journal.jsonl'
$controllerStream = [IO.File]::Open($controllerFile, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$sessionClock = [Diagnostics.Stopwatch]::StartNew()
$controllerSeq = 0
function Record-Control([string]$Stage, [hashtable]$Detail) {
    $script:controllerSeq++
    $row = [ordered]@{seq=$script:controllerSeq; stage=$Stage; elapsedMs=$sessionClock.ElapsedMilliseconds}
    foreach ($key in $Detail.Keys) { $row[$key]=$Detail[$key] }
    $bytes = $utf8.GetBytes(($row | ConvertTo-Json -Compress) + "`n")
    $controllerStream.Write($bytes); $controllerStream.Flush($true)
}
$nodeExe = 'C:\MarisLazyR5\R5-20261002-222300\tools\node\node.exe'
$cli = 'C:\MarisLazyR5\R5-20261002-222300\workspace\node_modules\vitest\vitest.mjs'
$workerJournal = Join-Path $resultRoot 'worker.journal.jsonl'
$process = [Diagnostics.Process]::new()
$process.StartInfo = [Diagnostics.ProcessStartInfo]::new()
$process.StartInfo.FileName=$nodeExe
$process.StartInfo.WorkingDirectory=$ownRoot
$process.StartInfo.UseShellExecute=$false
$process.StartInfo.CreateNoWindow=$true
$process.StartInfo.RedirectStandardOutput=$true
$process.StartInfo.RedirectStandardError=$true
$process.StartInfo.Environment['P4_D15_R1_JOURNAL']=$workerJournal
foreach ($argument in @($cli,'run','--config',(Join-Path $ownRoot 'vitest.config.mjs'))) { $process.StartInfo.ArgumentList.Add($argument) }
$rootStarted=$false; $rootPid=$null; $workerPid=$null; $workerHandle=$null
$owned=$null; $timeout=$false; $forcedRoot=$false; $forcedWorker=$false; $lastSeq=0
$mainCount=0; $journalInvalid=$false; $failureCode=$null
$safeFailure=$null; $nextControllerCall='start_process'
$stdoutTask=$null; $stderrTask=$null; $exitCode=$null; $rootExited=$null; $workerExited=$null
Record-Control 'controller_ready' @{processDeadlineMs=15000; testTimeoutMs=10000; collectionReserveMs=500; sessionDeadlineMs=60000; mainBudget=1; correctionBudgetUsed=1}
try {
    if (-not $process.Start()) { throw 'd15_r1_start_failed' }
    $rootStarted=$true; $rootPid=$process.Id
    Record-Control 'root_started' @{rootPid=$rootPid}
    $stdoutTask=$process.StandardOutput.ReadToEndAsync(); $stderrTask=$process.StandardError.ReadToEndAsync()
    while ($true) {
        if (Test-Path -LiteralPath $workerJournal) {
            $nextControllerCall='read_shared_journal'
            # The native journal writer remains open. Windows readers must share Write.
            $journalReaderStream=[IO.FileStream]::new($workerJournal,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
            try {
                $journalReader=[IO.StreamReader]::new($journalReaderStream)
                try {$journalText=$journalReader.ReadToEnd()} finally {$journalReader.Dispose()}
            } finally {$journalReaderStream.Dispose()}
            $nextControllerCall='parse_complete_journal_lines'
            $completeLines=$journalText -split "`n"
            for ($index=0; $index -lt $completeLines.Length-1; $index++) {
                if (-not $completeLines[$index]) { continue }
                $row=$completeLines[$index] | ConvertFrom-Json
                if ($row.seq -le $lastSeq) { continue }
                if ($row.seq -ne $lastSeq+1) { $journalInvalid=$true; throw 'd15_r1_journal_sequence' }
                if ($row.seq -eq 1) {
                    $workerPid=[int]$row.pid
                    $owned=($row.stage -eq 'worker_start' -and [int]$row.parentPid -eq $rootPid)
                    if (-not $owned) { throw 'd15_r1_worker_ownership_unknown' }
                    $workerHandle=Get-Process -Id $workerPid -ErrorAction SilentlyContinue
                    Record-Control 'worker_registered' @{workerPid=$workerPid; parentPid=[int]$row.parentPid; ownershipVerified=$owned}
                }
                if ([int]$row.pid -ne $workerPid -or [int]$row.parentPid -ne $rootPid) { throw 'd15_r1_worker_identity_changed' }
                if ($row.stage -eq 'main_import_enter') { $mainCount++ }
                if ($mainCount -gt 1) { throw 'd15_r1_main_budget' }
                $lastSeq=[int]$row.seq
            }
        }
        if ($process.HasExited) { break }
        # Leave a collection reserve within the original 15-second ceiling.
        if ($sessionClock.ElapsedMilliseconds -ge 14500) {
            $timeout=$true; $forcedRoot=$true
            Record-Control 'deadline_termination_enter' @{rootPid=$rootPid}
            $process.Kill($true)
            break
        }
        $process.WaitForExit(20) | Out-Null
    }
} catch {
    $failureCode='controller_or_observer_failure'
    $caught=$_.Exception
    while($caught.InnerException){$caught=$caught.InnerException}
    $safeFailure=[ordered]@{kind=if($caught -is [IO.IOException]){'IOException'}else{'other'};
        hresult=$caught.HResult; win32LowWord=($caught.HResult -band 65535); call=$nextControllerCall}
    Record-Control 'controller_failure' @{journalInvalid=$journalInvalid; ownershipVerified=($owned -eq $true)}
} finally {
    if ($rootStarted) {
        if (-not $process.HasExited) { $forcedRoot=$true; $process.Kill($true) }
        $remaining=[Math]::Max(0,15000-$sessionClock.ElapsedMilliseconds)
        $rootExited=$process.WaitForExit([int]$remaining)
        if ($rootExited) { $exitCode=$process.ExitCode }
        if ($owned -eq $true -and $workerHandle) {
            $workerHandle.Refresh()
            if (-not $workerHandle.HasExited) {
                $forcedWorker=$true; $workerHandle.Kill($true)
                $remaining=[Math]::Max(0,15000-$sessionClock.ElapsedMilliseconds)
                $workerHandle.WaitForExit([int]$remaining) | Out-Null
            }
            $workerHandle.Refresh(); $workerExited=$workerHandle.HasExited
        } elseif ($owned -eq $true) {
            $workerExited=$null -eq (Get-Process -Id $workerPid -ErrorAction SilentlyContinue)
        }
        Record-Control 'exit_checked' @{rootExited=($rootExited -eq $true); workerRegistered=($null -ne $workerPid); workerExited=($workerExited -eq $true)}
    }
    $streamComplete=$false
    if ($stdoutTask -and $stderrTask) {
        $remaining=[Math]::Max(0,15000-$sessionClock.ElapsedMilliseconds)
        $streamComplete=[Threading.Tasks.Task]::WaitAll(@($stdoutTask,$stderrTask),[int]$remaining)
    }
    $streamResults=@()
    foreach ($streamName in @('stdout','stderr')) {
        $task=if ($streamName -eq 'stdout') { $stdoutTask } else { $stderrTask }
        $raw=if ($task -and $task.IsCompletedSuccessfully) { $task.Result } else { '' }
        # Preserve stream boundaries/line order, disclose no raw errors/stacks or paths.
        $redactedLines=0
        $safeLines=foreach ($line in ($raw -split "`r?`n")) {
            if ($line -eq '') { '' }
            elseif ($line -match '^\s*RUN\s+v[0-9.]+' ) { 'RUN <fixed_vitest_version> <R1_ROOT>' }
            elseif ($line -match '^d15_r1_journal_write_failed$') { $line }
            else { $redactedLines++; '<redacted_output_line>' }
        }
        $safeText=$safeLines -join "`n"
        Write-New (Join-Path $resultRoot "$streamName.log") $safeText
        $streamResults += [ordered]@{stream=$streamName; rawBytes=$utf8.GetByteCount($raw); savedBytes=$utf8.GetByteCount($safeText); redactedLines=$redactedLines; complete=($task -and $task.IsCompletedSuccessfully)}
    }
    # Re-read immutable persisted evidence after exit; never infer absence from stdout.
    $events=@()
    if (Test-Path -LiteralPath $workerJournal) {
        foreach ($line in Get-Content -LiteralPath $workerJournal) { if ($line) { $events += ($line | ConvertFrom-Json) } }
    }
    $mainCount=@($events | Where-Object stage -eq 'main_import_enter').Count
    $workerExitEvents=@($events | Where-Object stage -eq 'worker_exit')
    $firstProcess=Get-Content -LiteralPath (Join-Path $firstRoot 'results/process.json') -Raw | ConvertFrom-Json
    $record=[ordered]@{attempt=1; invocation=1; rootPid=$rootPid; rootExited=$rootExited; rootExitCode=$exitCode;
        workerPid=$workerPid; workerParentVerified=$owned; workerExited=$workerExited; workerExitEventCount=$workerExitEvents.Count;
        timedOut=$timeout; forcedRootTermination=$forcedRoot; forcedWorkerTermination=$forcedWorker; streamsComplete=$streamComplete;
        durationMs=$sessionClock.ElapsedMilliseconds; processDeadlineMs=15000; testTimeoutMs=10000; sessionDeadlineMs=60000;
        mainImportRequests=$mainCount; lastWorkerStage=if ($events.Count) {$events[-1].stage} else {$null};
        journalSequenceValid=(-not $journalInvalid); failureCode=$failureCode; safeFailure=$safeFailure; streams=$streamResults;
        cumulativeTargetDurationMs=($firstProcess.durationMs+$sessionClock.ElapsedMilliseconds); totalCliInvocations=2; correctionBudgetUsed=1;
        cleanupEvidenceScope='owned_root_and_registered_worker_only'; electronStarts=0; servicesStarted=0; packages=0}
    Write-New (Join-Path $resultRoot 'process.json') (($record | ConvertTo-Json -Depth 6)+"`n")
    Record-Control 'controller_finished' @{durationMs=$sessionClock.ElapsedMilliseconds; mainImportRequests=$mainCount}
    $controllerStream.Dispose(); if($workerHandle){$workerHandle.Dispose()}; $process.Dispose()
    Write-Output ($record | ConvertTo-Json -Depth 6 -Compress)
}
