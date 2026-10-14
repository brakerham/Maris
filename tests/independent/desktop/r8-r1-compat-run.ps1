$ErrorActionPreference='Stop'
$ownRoot=[IO.Path]::GetFullPath($PSScriptRoot)
if($ownRoot -ne 'D:\CodeX_gap\wife-system\tests\independent\desktop'){throw 'wrong_root'}
$control=Get-Content -LiteralPath 'D:\CodeX_gap\wife-system\docs\coordination\control.md' -Raw
if(-not $control.Contains('2026-10-14T07:16:34+08:00')){throw 'control_changed'}
$ev=Join-Path $ownRoot 'evidence/r8-r1'
foreach($entry in Get-ChildItem -LiteralPath $ev -Force -Recurse){if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse'}}
foreach($line in Get-Content -LiteralPath (Join-Path $ev 'compat-source.sha256')){$parts=$line -split "`t";if((Get-FileHash -LiteralPath (Join-Path $ownRoot $parts[0])).Hash.ToLowerInvariant() -ne $parts[1]){throw 'source_changed'}}
$out=Join-Path $ev 'compat'
if(Test-Path -LiteralPath $out){throw 'first_exists_no_rerun'}
New-Item -ItemType Directory -Path $out | Out-Null
$node='C:\MarisModulesR6\R6-20261013-002100\tools\node\node.exe'
$utf8=[Text.UTF8Encoding]::new($false)
$proc=[Diagnostics.Process]::new();$proc.StartInfo=[Diagnostics.ProcessStartInfo]::new()
$proc.StartInfo.FileName=$node;$proc.StartInfo.WorkingDirectory=$ownRoot;$proc.StartInfo.UseShellExecute=$false;$proc.StartInfo.CreateNoWindow=$true
$proc.StartInfo.RedirectStandardOutput=$true;$proc.StartInfo.RedirectStandardError=$true
$workerFile=Join-Path $out 'workers.jsonl';$proc.StartInfo.Environment['R8R1_COMPAT_WORKERS']=$workerFile
foreach($a in @('C:\MarisModulesR6\R6-20261013-002100\workspace\node_modules\vitest\vitest.mjs','run','--configLoader','native','--config',(Join-Path $ownRoot 'r8-r1-compat.config.mjs'))){$proc.StartInfo.ArgumentList.Add($a)}
$clock=[Diagnostics.Stopwatch]::StartNew();$handles=@{};$started=$false;$timedOut=$false;$forced=$false;$failure=$null;$workers=@();$stdout=$null;$stderr=$null
try {
 $started=$proc.Start();if(-not $started){throw 'start_failed'}
 $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
 while(-not $proc.HasExited){
  if(Test-Path -LiteralPath $workerFile){foreach($row in Get-Content -LiteralPath $workerFile){$r=$row|ConvertFrom-Json;$id=[int]$r.pid;if(-not $handles.ContainsKey($id)){
   if([int]$r.parentPid -ne $proc.Id){throw 'ownership_unknown'}
   $h=Get-Process -Id $id -ErrorAction SilentlyContinue
   if($h){$native=$h.Handle;if($h.Path -ne $node -or $h.StartTime.ToUniversalTime() -lt $proc.StartTime.ToUniversalTime().AddSeconds(-1)){throw 'identity_unknown'};$handles[$id]=$h}else{$handles[$id]=$null}
  }}}
  if($clock.ElapsedMilliseconds -ge 299000){$timedOut=$true;break}
  $proc.WaitForExit(20)|Out-Null
 }
}catch{$failure=if($_.Exception.Message -in @('ownership_unknown','identity_unknown','start_failed')){$_.Exception.Message}else{'observer_error'}}
finally {
 if($started){if(-not $proc.HasExited){$forced=$true;$proc.Kill($true)};$proc.WaitForExit(2000)|Out-Null
  foreach($id in $handles.Keys){$h=$handles[$id];$exited=$null;$code=$null;$wkforced=$false;if($h){$h.Refresh();if(-not $h.HasExited){$wkforced=$true;$h.Kill($true);$h.WaitForExit(2000)|Out-Null};$exited=$h.HasExited;if($exited){$code=$h.ExitCode}}else{$exited=$null -eq (Get-Process -Id $id -ErrorAction SilentlyContinue)}
   $workers+=@{pid=$id;exited=$exited;nativeExitCode=$code;forced=$wkforced;identityVerified=($null -ne $h)}
  }
 }
 $streams=@();foreach($label in @('stdout','stderr')){$t=if($label -eq 'stdout'){$stdout}else{$stderr};$raw=if($t -and $t.IsCompletedSuccessfully){$t.Result}else{''};$safe=foreach($line in ($raw -split "`r?`n")){if($line -match '^\{"stage":"compat_result"'){$line}elseif($line){'<redacted_output_line>'}else{''}};[IO.File]::WriteAllText((Join-Path $out "$label.log"),($safe -join "`n"),$utf8);$streams+=@{name=$label;complete=($t -and $t.IsCompletedSuccessfully);rawBytes=$utf8.GetByteCount($raw)}}
 $result=@{rootPid=if($started){$proc.Id}else{$null};rootExited=if($started){$proc.HasExited}else{$null};rootExitCode=if($started -and $proc.HasExited){$proc.ExitCode}else{$null};workers=$workers;failure=$failure;timedOut=$timedOut;forced=$forced;durationMs=$clock.ElapsedMilliseconds;streams=$streams;productStarts=0;scope='four_compat_files_28_once'}
 [IO.File]::WriteAllText((Join-Path $out 'process.json'),(($result|ConvertTo-Json -Depth 6)+"`n"),$utf8)
 $result|ConvertTo-Json -Depth 6
}
if($failure -or $timedOut -or $forced -or -not $started -or $proc.ExitCode -ne 0){exit 1}
