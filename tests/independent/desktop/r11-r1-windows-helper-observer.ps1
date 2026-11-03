param([Parameter(Mandatory)][string]$RequestPath)
$ErrorActionPreference='Stop'
$r=Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$encoding=[Text.UTF8Encoding]::new($false)
function Record([string]$stage,[string]$event,$details) {
  $line=@{callId=$r.callId;stage=$stage;event=$event;at=[DateTimeOffset]::UtcNow.ToString('o');details=$details}|ConvertTo-Json -Depth 8 -Compress
  [IO.File]::AppendAllText($r.stageLog,$line+"`n",$encoding)
}
function SafeError($e) {
  $name=$e.Exception.GetType().Name
  $allow=@('CimException','UnauthorizedAccessException','Win32Exception','RuntimeException','InvalidOperationException','MethodInvocationException')
  return @{type=if($name -in $allow){$name}else{'other'};category=if($e.CategoryInfo.Category -eq 'PermissionDenied' -or $name -eq 'UnauthorizedAccessException'){'access_denied'}else{'query_failed'};hresult=$e.Exception.HResult;nativeErrorCode=if($e.Exception.PSObject.Properties['NativeErrorCode']){[string]$e.Exception.NativeErrorCode}else{$null};statusCode=if($e.Exception.PSObject.Properties['StatusCode']){[string]$e.Exception.StatusCode}else{$null};actualCategory=[string]$e.CategoryInfo.Category}
}
$me=[Diagnostics.Process]::GetCurrentProcess()
$receipt=@{pid=$PID;created=$me.StartTime.ToUniversalTime().ToString('o');executable=$me.MainModule.FileName;scriptPath=$PSCommandPath;scriptSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();callId=$r.callId;marker=$r.descriptor.marker;output=$r.output}
[IO.File]::WriteAllText($r.receipt,($receipt|ConvertTo-Json -Compress),$encoding)
$stage='parser_prepare'
try {
  Record $stage 'enter' @{}
  . $r.parserScript
  Record $stage 'terminal' @{status='success'}
  $stage='process_query'
  Record $stage 'enter' @{}
  $all=@(Get-CimInstance Win32_Process -OperationTimeoutSec 3 -ErrorAction Stop)
  $selfProcess=@($all|Where-Object ProcessId -eq $PID)
  if($selfProcess.Count -eq 1){$receipt.parentPid=[int]$selfProcess[0].ParentProcessId;[IO.File]::WriteAllText($r.receipt,($receipt|ConvertTo-Json -Compress),$encoding)}
  $root=@($all|Where-Object ProcessId -eq $r.rootPid)
  if($root.Count -gt 1){throw 'root_nonunique'}
  $start=[DateTimeOffset]::Parse($r.startedUtc).UtcDateTime
  $verified=$false;$rootData=@{present=$false}
  if($root.Count -eq 1){
    $v=$root[0]
    $parsed=Parse-RootCommand ([string]$v.CommandLine)
    $pathSafe=$false
    if($parsed.ok -and $parsed.argv.Count -eq 2){$pathSafe=Path-WithoutReparse $parsed.argv[1]}
    $verified=$v.ExecutablePath -ceq $r.descriptor.executable -and $v.ParentProcessId -eq $r.parentPid -and $v.CreationDate.ToUniversalTime() -ge $start.AddSeconds(-2)
    $rootData=@{present=$true;pid=[int]$v.ProcessId;parentPid=[int]$v.ParentProcessId;created=$v.CreationDate.ToUniversalTime().ToString('o');executable=$v.ExecutablePath;parsed=$parsed;pathNoReparse=$pathSafe}
  }
  $ids=[Collections.Generic.HashSet[int]]::new()
  if($verified){[void]$ids.Add([int]$r.rootPid)}
  foreach($k in $r.known){
    $v=@($all|Where-Object ProcessId -eq $k.pid)
    if($v.Count -eq 1 -and $v[0].CreationDate.ToUniversalTime().ToString('o') -eq $k.created -and $v[0].ParentProcessId -eq $k.parentPid){[void]$ids.Add([int]$k.pid)}
  }
  $changed=$true
  while($changed){$changed=$false;foreach($v in $all){if($ids.Contains([int]$v.ParentProcessId) -and $v.CreationDate.ToUniversalTime() -ge $start.AddSeconds(-2)){if($ids.Add([int]$v.ProcessId)){$changed=$true}}}}
  $owned=@($all|Where-Object {$ids.Contains([int]$_.ProcessId)}|ForEach-Object {
    [pscustomobject]@{pid=[int]$_.ProcessId;parentPid=[int]$_.ParentProcessId;created=$_.CreationDate.ToUniversalTime().ToString('o');kind=if($_.ExecutablePath -eq $r.descriptor.executable){'target'}elseif($_.Name -eq 'python.exe'){'python'}elseif($_.Name -eq 'conhost.exe'){'conhost'}else{'descendant'}}
  })
  Record $stage 'terminal' @{status='success';rootPresent=($root.Count -eq 1);rootVerified=[bool]$verified;ownedCount=$owned.Count;identityValidation='pending_shared_checker'}
  $result=@{rootData=$rootData;ok=$true;callId=$r.callId;action=$r.action;rootPresent=($root.Count -eq 1);rootVerified=[bool]$verified;identityValidation='pending_shared_checker';owned=$owned;resourceStatus='not_requested';listeners=$null;windowCount=$null}
  if($r.action -eq 'resources'){
    $stage='type_prepare';Record $stage 'enter' @{}
    Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using System.ComponentModel;
public static class R9R2Windows {
 public delegate bool Callback(IntPtr h,IntPtr l);
 [DllImport("user32.dll",SetLastError=true)]public static extern bool EnumWindows(Callback cb,IntPtr l);
 [DllImport("user32.dll",SetLastError=true)]public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 public static int Count(int[] ids){int count=0;bool ok=EnumWindows((h,l)=>{uint p;GetWindowThreadProcessId(h,out p);if(Array.IndexOf(ids,(int)p)>=0)count++;return true;},IntPtr.Zero);if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error());return count;}
}
'@
    Record $stage 'terminal' @{status='success'}
    $stage='window_query';Record $stage 'enter' @{}
    $result.windowCount=[R9R2Windows]::Count([int[]]@($ids))
    Record $stage 'terminal' @{status='success';count=$result.windowCount}
    $stage='listener_query';Record $stage 'enter' @{}
    $listeners=@(Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'State=2' -OperationTimeoutSec 2 -ErrorAction Stop|Where-Object {$ids.Contains([int]$_.OwningProcess)}|ForEach-Object {
      [pscustomobject]@{pid=[int]$_.OwningProcess;port=[int]$_.LocalPort;loopback=($_.LocalAddress -eq '127.0.0.1' -or $_.LocalAddress -eq '::1')}
    })
    $result.listeners=$listeners;$result.resourceStatus='success'
    Record $stage 'terminal' @{status='success';count=$listeners.Count}
  }
  $stage='json_output';Record $stage 'enter' @{}
  $encoded=$result|ConvertTo-Json -Depth 8 -Compress
  [Console]::Out.WriteLine($encoded)
  Record $stage 'terminal' @{status='success';bytes=$encoding.GetByteCount($encoded)}
  exit 0
}catch{
  $errorInfo=SafeError $_
  $errorInfo.code=if($_.Exception.Message -in @('root_identity_mismatch','root_nonunique')){$_.Exception.Message}else{'unclassified'}
  Record $stage 'terminal' @{status='failed';error=$errorInfo}
  $failure=@{ok=$false;callId=$r.callId;stage=$stage;error=$errorInfo}|ConvertTo-Json -Depth 6 -Compress
  [Console]::Out.WriteLine($failure)
  exit 3
}
