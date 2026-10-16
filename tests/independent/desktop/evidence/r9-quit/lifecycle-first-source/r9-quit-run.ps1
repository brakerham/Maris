$ErrorActionPreference='Stop'
$own=[IO.Path]::GetFullPath($PSScriptRoot)
if($own -ne 'D:\CodeX_gap\wife-system\tests\independent\desktop'){throw 'r9_wrong_root'}
$ev=Join-Path $own 'evidence/r9-quit'
$control=Get-Content -LiteralPath 'D:\CodeX_gap\wife-system\docs\coordination\control.md' -Raw
if(-not $control.Contains('2026-10-16T00:51:00+08:00')){throw 'r9_control_changed'}
foreach($line in Get-Content -LiteralPath (Join-Path $ev 'lifecycle-source.sha256')){
 $p=$line -split "`t";$target=[IO.Path]::GetFullPath((Join-Path $own $p[0]))
 if(-not $target.StartsWith($own+'\') -or (Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant() -ne $p[1]){throw 'r9_source_changed'}
}
foreach($f in Get-ChildItem -LiteralPath $ev -Recurse -Force){if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'r9_reparse'}}
$out=Join-Path $ev 'lifecycle'
if(Test-Path -LiteralPath $out){throw 'r9_first_exists_no_rerun'}
New-Item -ItemType Directory -Path $out | Out-Null
$node='C:\MarisQuitR7\R7-20261014-191500\tools\node\node.exe'
$cli='C:\MarisQuitR7\R7-20261014-191500\workspace\node_modules\vitest\vitest.mjs'
$utf8=[Text.UTF8Encoding]::new($false)
$clock=[Diagnostics.Stopwatch]::StartNew();$seq=0
$journalStream=[IO.File]::Open((Join-Path $out 'controller.journal.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
function Record([string]$Event,[hashtable]$Details){$script:seq++;$b=$utf8.GetBytes((@{seq=$script:seq;event=$Event;elapsedMs=$clock.ElapsedMilliseconds;details=$Details}|ConvertTo-Json -Depth 6 -Compress)+"`n");$journalStream.Write($b);$journalStream.Flush($true)}
function Read-Shared([string]$File){$fs=[IO.FileStream]::new($File,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite);try{$rd=[IO.StreamReader]::new($fs);try{return $rd.ReadToEnd()}finally{$rd.Dispose()}}finally{$fs.Dispose()}}
$proc=[Diagnostics.Process]::new();$proc.StartInfo=[Diagnostics.ProcessStartInfo]::new();$proc.StartInfo.FileName=$node;$proc.StartInfo.WorkingDirectory=$own
$proc.StartInfo.UseShellExecute=$false;$proc.StartInfo.CreateNoWindow=$true;$proc.StartInfo.RedirectStandardOutput=$true;$proc.StartInfo.RedirectStandardError=$true
foreach($a in @($cli,'run','--configLoader','native','--config',(Join-Path $own 'r9-quit-vitest.config.mjs'))){$proc.StartInfo.ArgumentList.Add($a)}
$started=$false;$handles=@{};$workers=@();$failure=$null;$timeout=$false;$forced=$false;$stage='initialization';$stageAt=0;$seen=0;$stdout=$null;$stderr=$null;$streamComplete=$false
Record 'controller_ready' @{initializationMs=60000;bodyMs=15000;cleanupMs=5000;suiteMs=300000;productStarts=0}
try{
 $started=$proc.Start();if(-not $started){throw 'r9_start_failed'}
 $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync();Record 'root_started' @{pid=$proc.Id}
 while($true){
  $workerJournal=Join-Path $out 'worker.journal.jsonl'
  if(Test-Path -LiteralPath $workerJournal){$lines=(Read-Shared $workerJournal) -split "`n";for($i=0;$i -lt $lines.Length-1;$i++){
   if(-not $lines[$i]){continue};$r=$lines[$i]|ConvertFrom-Json;if($r.seq -le $seen){continue};if($r.seq -ne $seen+1){throw 'r9_journal_sequence'};$seen=$r.seq
   $wid=[int]$r.pid
   if(-not $handles.ContainsKey($wid)){
    if($r.event -ne 'worker_start' -or [int]$r.parentPid -ne $proc.Id){throw 'r9_ownership_unknown'}
    $wh=Get-Process -Id $wid -ErrorAction Stop;$native=$wh.Handle
    if($wh.Path -ne $node -or $wh.StartTime.ToUniversalTime() -lt $proc.StartTime.ToUniversalTime().AddSeconds(-1)){throw 'r9_identity_unknown'}
    $handles[$wid]=$wh;Record 'worker_registered' @{pid=$wid;parentPid=$proc.Id;pathAndTimeVerified=$true}
   }
   if([int]$r.parentPid -ne $proc.Id){throw 'r9_parent_changed'}
   if($r.event -eq 'body_enter'){
    if($stage -eq 'initialization' -and $clock.ElapsedMilliseconds -gt 60000){$timeout=$true;throw 'r9_initialization_timeout'}
    $stage='body';$stageAt=$clock.ElapsedMilliseconds;Record 'body_enter' @{id=$r.details.id}
   }
   if($r.event -eq 'cleanup_enter'){
    if($r.details.bodyMs -gt 15000){$timeout=$true;throw 'r9_body_timeout'}
    $stage='cleanup';$stageAt=$clock.ElapsedMilliseconds;Record 'cleanup_enter' @{id=$r.details.id;bodyMs=$r.details.bodyMs}
   }
   if($r.event -eq 'cleanup_terminal'){
    if($r.details.cleanupMs -gt 5000){$timeout=$true;throw 'r9_cleanup_timeout'}
    $stage='between';$stageAt=$clock.ElapsedMilliseconds;Record 'cleanup_terminal' @{id=$r.details.id;cleanupMs=$r.details.cleanupMs}
   }
  }}
  $elapsed=$clock.ElapsedMilliseconds
  $limit=if($stage -eq 'initialization'){60000}elseif($stage -eq 'body'){15000}elseif($stage -eq 'cleanup'){5000}else{60000}
  if($elapsed -ge 299000 -or $elapsed-$stageAt -ge $limit){$timeout=$true;Record 'deadline' @{stage=$stage};break}
  if($proc.HasExited){break};$proc.WaitForExit(20)|Out-Null
 }
}catch{$failure=if($_.Exception.Message -match '^r9_[a-z_]+$'){$_.Exception.Message}else{'r9_controller_error'};Record 'controller_error' @{code=$failure;stage=$stage}}
finally{
 if($started){
  if(-not $proc.HasExited){$forced=$true;$proc.Kill($true)};$proc.WaitForExit(1000)|Out-Null
  foreach($wid in $handles.Keys){$wh=$handles[$wid];$wforced=$false;$wc=$null;$we=$null
   try{$wh.Refresh();if(-not $wh.HasExited){$wforced=$true;$wh.Kill($true);$wh.WaitForExit(1000)|Out-Null};$we=$wh.HasExited;if($we){$wc=$wh.ExitCode}}catch{$failure='r9_worker_exit_unverified'}
   $workers+=@{pid=$wid;exited=$we;nativeExitCode=$wc;forced=$wforced;identityVerified=$true};$wh.Dispose()
  }
 }
 if($stdout -and $stderr){try{$streamComplete=[Threading.Tasks.Task]::WaitAll(@($stdout,$stderr),1000)}catch{}}
 $streams=@();foreach($label in @('stdout','stderr')){
  $t=if($label -eq 'stdout'){$stdout}else{$stderr};$raw=if($t -and $t.IsCompletedSuccessfully){$t.Result}else{''}
  $safe=foreach($line in ($raw -split "`r?`n")){if($line -match '^\{"event":"r9_result","passed":\d+,"failed":\d+,"notRun":\d+\}$'){$line}elseif($line){'<redacted_output_line>'}else{''}}
  [IO.File]::WriteAllText((Join-Path $out "$label.log"),($safe -join "`n"),$utf8);$streams+=@{name=$label;complete=($t -and $t.IsCompletedSuccessfully);rawBytes=$utf8.GetByteCount($raw)}
 }
 $result=@{scope='independent_quit_8_lifecycles_attempt_0';rootPid=if($started){$proc.Id}else{$null};rootExited=if($started){$proc.HasExited}else{$null};rootExitCode=if($started -and $proc.HasExited){$proc.ExitCode}else{$null};workers=$workers;failure=$failure;timedOut=$timeout;forced=$forced;durationMs=$clock.ElapsedMilliseconds;streams=$streams;streamsComplete=$streamComplete;productStarts=0;helperStarts=0;cleanupScope='owned_root_and_registered_workers_only';stagesObserved=$seen}
 [IO.File]::WriteAllText((Join-Path $out 'process.json'),(($result|ConvertTo-Json -Depth 6)+"`n"),$utf8);Record 'controller_finished' @{durationMs=$clock.ElapsedMilliseconds};$journalStream.Dispose();$result|ConvertTo-Json -Depth 6
}
if($failure -or $timeout -or $forced -or -not $started -or $proc.ExitCode -ne 0){exit 1}
