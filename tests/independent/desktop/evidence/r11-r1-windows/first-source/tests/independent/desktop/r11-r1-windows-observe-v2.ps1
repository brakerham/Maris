param([ValidateSet('SelfTest','Observe')][string]$Mode='Observe',[string]$ReceiptPath='',[int]$ControllerPid=0)
$ErrorActionPreference='Stop'
$ev=Join-Path $PSScriptRoot 'evidence/r11-r1-windows'
$out=Join-Path $ev ($Mode.ToLowerInvariant()+'-v2.json')
$journal=Join-Path $ev ($Mode.ToLowerInvariant()+'-v2.jsonl')
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $journal)){throw 'first_exists'}
$watch=[Diagnostics.Stopwatch]::StartNew()
function Emit($value){[IO.File]::AppendAllText($journal,(($value|ConvertTo-Json -Depth 9 -Compress)+"`n"),[Text.UTF8Encoding]::new($false))}
function Norm([string]$value){return $value.Replace('/','\').ToLowerInvariant()}
function DateUtc($value){if($value -is [DateTime]){return $value.ToUniversalTime().ToString('o')};if($value -is [DateTimeOffset]){return $value.UtcDateTime.ToString('o')};if($value -is [string]){return [DateTimeOffset]::Parse($value).UtcDateTime.ToString('o')};throw 'date_type_unknown'}
function Scoped($rows,[int[]]$exclude,[string[]]$scopes){
 $found=@();foreach($row in $rows){if($exclude -contains [int]$row.ProcessId){continue};$exe=Norm ([string]$row.ExecutablePath);$cmd=Norm ([string]$row.CommandLine)
  for($i=0;$i -lt $scopes.Count;$i++){$scope=(Norm $scopes[$i]).TrimEnd('\');if($exe.StartsWith($scope+'\') -or $cmd.Contains($scope+'\') -or $cmd.Contains($scope+'"')){$found+=@{pid=[int]$row.ProcessId;parentPid=[int]$row.ParentProcessId;created=DateUtc $row.CreationDate;scopeIndex=$i;executableInsideScope=$exe.StartsWith($scope+'\')};break}}
 };return ,$found
}
function SafeError($record){$e=$record.Exception;return @{errorType=$e.GetType().FullName;hresult=$e.HResult;nativeErrorCode=if($e.PSObject.Properties['NativeErrorCode']){[string]$e.NativeErrorCode}else{$null};statusCode=if($e.PSObject.Properties['StatusCode']){[string]$e.StatusCode}else{$null};category=[string]$record.CategoryInfo.Category;safeCode=if($e.Message -in @('self_identity_unknown','target_process_present','date_type_unknown','observation_deadline')){$e.Message}else{'unknown'}}}
$result=@{at=[DateTimeOffset]::Now.ToString('o');mode=$Mode;passed=$false;stages=@();productStarts=0;helperStarts=0;processInventoryStored=$false;firstError=$null;exitCode=$null;signal=$null}
$phase='initial'
if($ReceiptPath){$selfInfo=[Diagnostics.Process]::GetCurrentProcess();[IO.File]::WriteAllText($ReceiptPath,(@{pid=$PID;parentPid=$ControllerPid;parentVerified=$false;created=$selfInfo.StartTime.ToUniversalTime().ToString('o');executable=$selfInfo.MainModule.FileName;scriptSha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()}|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))}

try{
 if($Mode -eq 'SelfTest'){
  $checks=@();function Check([string]$id,$expected,$actual){$v=@{id=$id;expected=$expected;actual=$actual;passed=($expected -ceq $actual)};$script:checks+=,$v;Emit $v;if(-not $v.passed){throw 'selftest_comparison'}}
  $checks=@();$script:checks=@();$d=[datetime]::UtcNow;$rows=@([pscustomobject]@{ProcessId=10;ParentProcessId=9;CreationDate=$d;ExecutablePath='C:/VirtualRoot/observe.exe';CommandLine=''},[pscustomobject]@{ProcessId=11;ParentProcessId=9;CreationDate=$d;ExecutablePath='C:\VirtualRoot\target.exe';CommandLine=''},[pscustomobject]@{ProcessId=12;ParentProcessId=9;CreationDate=$d;ExecutablePath='C:\VirtualRootSuffix\other.exe';CommandLine=''})
  Check 'OBS-SELF-EXACT-EXCLUSION' 1 (Scoped $rows @(10) @('C:\VirtualRoot')).Count
  Check 'OBS-SELF-FOREIGN-RETAINED' 11 (Scoped $rows @(10) @('C:/VirtualRoot'))[0].pid
  Check 'OBS-SELF-DATETIME' ($d.ToUniversalTime().ToString('o')) (DateUtc $d)
  Check 'OBS-SELF-DATEOFFSET' ($d.ToUniversalTime().ToString('o')) (DateUtc ([datetimeoffset]$d))
  $errorValue=$null;try{throw [System.UnauthorizedAccessException]::new('virtual hidden')}catch{$errorValue=SafeError $_}
  Check 'OBS-SELF-ERROR-NATIVE-NULL' $null $errorValue.nativeErrorCode
  Check 'OBS-SELF-ERROR-TYPE' 'System.UnauthorizedAccessException' $errorValue.errorType
  Check 'OBS-SELF-EMPTY-INVENTORY' 0 (Scoped @() @() @('C:/VirtualRoot')).Count
  $first=$null;$released=$false;try{try{throw 'virtual_first'}catch{$first='first'} }finally{$released=$true;try{throw 'virtual_second'}catch{if(-not $first){$first='second'}}}
  Check 'OBS-SELF-FIRST-ERROR' 'first' $first;Check 'OBS-SELF-FINALLY' $true $released
  $bad=$false;try{'{'|ConvertFrom-Json|Out-Null}catch{$bad=$true};Check 'OBS-SELF-BAD-RESULT' $true $bad
  $missing=$null;Check 'OBS-SELF-MISSING-NOT-ZERO' $true ($null -eq $missing)
  Check 'OBS-SELF-IDS-UNIQUE' $script:checks.Count @($script:checks.id|Select-Object -Unique).Count
  $native=$null;try{$fake=[System.UnauthorizedAccessException]::new('virtual');$fake|Add-Member NativeErrorCode 'AccessDenied';$fake|Add-Member StatusCode '2';throw $fake}catch{$native=SafeError $_}
  Check 'OBS-SELF-NATIVE-CODE' 'AccessDenied' $native.nativeErrorCode
  Check 'OBS-SELF-STATUS-CODE' '2' $native.statusCode
  Check 'OBS-SELF-ERROR-NOT-EMPTY' $false ($null -eq $native)
  $result.checks=$script:checks;$result.passed=$true
 }else{
  if(-not (Get-Content -LiteralPath 'D:\CodeX_gap\wife-system\docs\coordination\control.md' -Raw).Contains('2026-11-03T00:05:00+08:00')){throw 'control_changed'}
  $phase='process_query';Emit @{stage=$phase;event='enter';at=[DateTimeOffset]::Now.ToString('o')}
  $all=@(Get-CimInstance Win32_Process -OperationTimeoutSec 3 -ErrorAction Stop)
  $self=[Diagnostics.Process]::GetCurrentProcess();$own=@($all|Where-Object ProcessId -eq $PID)
  if($own.Count -ne 1 -or (Norm $own[0].ExecutablePath) -ne (Norm $self.MainModule.FileName) -or [Math]::Abs(($own[0].CreationDate.ToUniversalTime()-$self.StartTime.ToUniversalTime()).TotalSeconds) -gt 2){throw 'self_identity_unknown'}
  if($ReceiptPath){$rc=Get-Content -LiteralPath $ReceiptPath -Raw|ConvertFrom-Json;$rc.parentPid=[int]$own[0].ParentProcessId;$rc.parentVerified=$rc.parentPid -eq $ControllerPid;[IO.File]::WriteAllText($ReceiptPath,($rc|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))}
  $scopes=@('C:\MarisC12','C:\MarisIpcR9\R9-20261101-161412','C:\MarisQuitR7\R7-20261014-191500','C:\MarisSettingsR8\R8-20261019-103900')
  $excluded=@([int]$PID);$parent=@($all|Where-Object ProcessId -eq $own[0].ParentProcessId)
  $parentVerified=$parent.Count -eq 1 -and (Norm $parent[0].ExecutablePath) -eq (Norm $self.MainModule.FileName) -and $parent[0].CommandLine.Contains($PSCommandPath) -and $parent[0].CreationDate -le $own[0].CreationDate
  if($parentVerified){$excluded+=,[int]$parent[0].ProcessId}
  $related=Scoped $all $excluded $scopes
  $v=@{stage=$phase;event='result';status='success';selfPid=$PID;selfIdentityVerified=$true;selfCreation=DateUtc $own[0].CreationDate;parentIdentityVerified=$parentVerified;excludedExactPids=$excluded;related=$related;relatedCount=$related.Count;processesReturned=$all.Count};$result.stages+=,$v;Emit $v
  if($related.Count){throw 'target_process_present'}
  if($watch.ElapsedMilliseconds -ge 6000){throw 'observation_deadline'}
  $phase='listener_query';Emit @{stage=$phase;event='enter';at=[DateTimeOffset]::Now.ToString('o')}
  $listeners=@(Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'State=2' -OperationTimeoutSec 2 -ErrorAction Stop)
  $v=@{stage=$phase;event='result';status='success';querySucceeded=$true;listenerCount=$listeners.Count;relatedListenerCount=@($listeners|Where-Object {$related.pid -contains [int]$_.OwningProcess}).Count};$result.stages+=,$v;Emit $v
  $phase='uia_load';Emit @{stage=$phase;event='enter';at=[DateTimeOffset]::Now.ToString('o')}
  Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop;Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
  $phase='uia_read';Emit @{stage=$phase;event='enter';at=[DateTimeOffset]::Now.ToString('o')}
  $desktop=[System.Windows.Automation.AutomationElement]::RootElement
  $tops=$desktop.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
  $v=@{stage=$phase;event='result';status='success';topLevelCount=$tops.Count;dialogAction='existing_owned_button_adapter_requires_target_identity';deviceUnavailable=$false};$result.stages+=,$v;Emit $v
  $phase='tray_read';Emit @{stage=$phase;event='enter';at=[DateTimeOffset]::Now.ToString('o')}
  $cond=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ClassNameProperty,'Shell_TrayWnd');$tray=$desktop.FindAll([System.Windows.Automation.TreeScope]::Children,$cond)
  $v=@{stage=$phase;event='result';status='success';rootCount=$tray.Count;actionAdapter='not_implemented';deviceUnavailable=$false};$result.stages+=,$v;Emit $v
  if($watch.ElapsedMilliseconds -gt 8000){throw 'observation_deadline'}
  $result.passed=$true
 }
}catch{$result.firstError=@{stage=$phase;details=(SafeError $_)};Emit @{stage=$phase;event='error';details=$result.firstError.details}}
finally{$result.durationMs=$watch.ElapsedMilliseconds;$result.exitCode=if($result.passed){0}else{1};[IO.File]::WriteAllText($out,(($result|ConvertTo-Json -Depth 12)+"`n"),[Text.UTF8Encoding]::new($false));$result|ConvertTo-Json -Depth 12}
exit $result.exitCode
