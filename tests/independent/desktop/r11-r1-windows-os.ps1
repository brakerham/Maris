param([ValidateSet('snapshot','close','dialog')][string]$Action='snapshot',[int]$RootPid,[int]$ExpectedParentPid,[string]$StartedUtc,[string]$Button='',[string]$KnownJson='[]',[string]$ReceiptPath='',[string]$CallId='',[string]$Marker='',[string]$Output='',[string]$StageLog='')
$ErrorActionPreference='Stop'
function Stage([string]$phase,[string]$event,$detail) {if($StageLog){[IO.File]::AppendAllText($StageLog,((@{callId=$CallId;stage=$phase;event=$event;at=[DateTimeOffset]::UtcNow.ToString('o');details=$detail}|ConvertTo-Json -Depth 5 -Compress)+"`n"),[Text.UTF8Encoding]::new($false))}}
$stage='process_query'
try {
Stage $stage 'enter' @{}

$exe='C:\MarisIpcR9\R9-20261101-161412\workspace\apps\desktop\out\Maris-win32-x64\Maris.exe'
$self=[Diagnostics.Process]::GetCurrentProcess()
if($ReceiptPath){[IO.File]::WriteAllText($ReceiptPath,(@{pid=$PID;parentPid=0;created=$self.StartTime.ToUniversalTime().ToString('o');executable=$self.MainModule.FileName;scriptPath=$PSCommandPath;scriptSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();callId=$CallId;marker=$Marker;output=$Output}|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))}
$all=@(Get-CimInstance Win32_Process -OperationTimeoutSec 3 -ErrorAction Stop)
if($ReceiptPath){$v=Get-Content -LiteralPath $ReceiptPath -Raw|ConvertFrom-Json;$v.parentPid=[int]($all|Where-Object ProcessId -eq $PID).ParentProcessId;[IO.File]::WriteAllText($ReceiptPath,($v|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))}
$root=$all|Where-Object ProcessId -eq $RootPid
$start=[DateTimeOffset]::Parse($StartedUtc).UtcDateTime
$verified=$root -and $root.ExecutablePath -eq $exe -and $root.ParentProcessId -eq $ExpectedParentPid -and $root.CreationDate.ToUniversalTime() -ge $start.AddSeconds(-2)
$known=@($KnownJson|ConvertFrom-Json)
$ids=[System.Collections.Generic.HashSet[int]]::new()
if($verified){[void]$ids.Add($RootPid)}elseif($root){throw 'root_identity_changed'}
foreach($k in $known){$v=$all|Where-Object ProcessId -eq $k.pid;if($v -and $v.CreationDate.ToUniversalTime().ToString('o') -eq $k.created){[void]$ids.Add([int]$k.pid)}}
$changed=$true;while($changed){$changed=$false;foreach($v in $all){if($ids.Contains([int]$v.ParentProcessId) -and $v.CreationDate.ToUniversalTime() -ge $start.AddSeconds(-2)){if($ids.Add([int]$v.ProcessId)){$changed=$true}}}}
$owned=@($all|Where-Object {$ids.Contains([int]$_.ProcessId)}|ForEach-Object {[pscustomobject]@{pid=[int]$_.ProcessId;parentPid=[int]$_.ParentProcessId;created=$_.CreationDate.ToUniversalTime().ToString('o');kind=if($_.ExecutablePath -eq $exe){'product'}elseif($_.Name -eq 'python.exe'){'python'}elseif($_.Name -eq 'conhost.exe'){'conhost'}else{'other'}}})
Stage $stage 'terminal' @{status='success';ownedCount=$owned.Count;rootVerified=[bool]$verified}
$stage='type_prepare';Stage $stage 'enter' @{}
 Add-Type -TypeDefinition @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;using System.Text;
public static class R9Windows {public delegate bool CB(IntPtr h,IntPtr l);[DllImport("user32.dll")]public static extern bool EnumWindows(CB cb,IntPtr l);[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);[DllImport("user32.dll",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32.dll")]public static extern bool IsWindowVisible(IntPtr h);[DllImport("user32.dll")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);public static int Count(int[] ps){int n=0;EnumWindows((h,l)=>{uint id;GetWindowThreadProcessId(h,out id);if(Array.IndexOf(ps,(int)id)>=0)n++;return true;},IntPtr.Zero);return n;}public static List<IntPtr> Main(int p){var a=new List<IntPtr>();EnumWindows((h,l)=>{uint id;GetWindowThreadProcessId(h,out id);var s=new StringBuilder(256);GetWindowText(h,s,256);if(id==p&&s.ToString()=="Maris")a.Add(h);return true;},IntPtr.Zero);return a;}}
'@
Stage $stage 'terminal' @{status='success'}
if($Action -eq 'snapshot'){
 $stage='listener_query';Stage $stage 'enter' @{}
 $listeners=@(Get-CimInstance -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection -Filter 'State=2' -OperationTimeoutSec 2 -ErrorAction Stop|Where-Object {$ids.Contains([int]$_.OwningProcess)}|ForEach-Object {[pscustomobject]@{pid=[int]$_.OwningProcess;port=[int]$_.LocalPort;loopback=($_.LocalAddress -eq '127.0.0.1' -or $_.LocalAddress -eq '::1')}})
 Stage $stage 'terminal' @{status='success';count=$listeners.Count}
 $stage='window_query';Stage $stage 'enter' @{}
 $windowCount=[R9Windows]::Count([int[]]@($ids));$visibleMainCount=@([R9Windows]::Main($RootPid)|Where-Object {[R9Windows]::IsWindowVisible($_)}).Count
 Stage $stage 'terminal' @{status='success';count=$windowCount;visibleMainCount=$visibleMainCount}
 [pscustomobject]@{rootVerified=[bool]$verified;rootPresent=[bool]$root;owned=$owned;listeners=$listeners;windowCount=$windowCount;resourceStatus='success';visibleMainCount=$visibleMainCount}|ConvertTo-Json -Depth 5 -Compress
 exit 0
}
if(-not $verified){throw 'root_not_owned'}
if($Action -eq 'close'){
 $stage='native_close';Stage $stage 'enter' @{}

 $windows=[R9Windows]::Main($RootPid);if($windows.Count -ne 1){throw 'owned_main_ambiguous'}
 $posted=[R9Windows]::PostMessage($windows[0],0x0010,[IntPtr]::Zero,[IntPtr]::Zero)
 Stage $stage 'terminal' @{status='success';closePosted=$posted}
 [pscustomobject]@{rootVerified=$true;matchingMainWindows=$windows.Count;closePosted=$posted;postedUtc=[DateTimeOffset]::UtcNow.ToString('o');rootPid=$RootPid;parentVerified=$true}|ConvertTo-Json -Compress
 exit 0
}
$stage='uia_prepare';Stage $stage 'enter' @{}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Stage $stage 'terminal' @{status='success'}
$stage='owned_button';Stage $stage 'enter' @{}
$pidCondition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ProcessIdProperty,$RootPid)
$ownedWindows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,$pidCondition)
$matches=@()
foreach($w in $ownedWindows){if($w.Current.Name -eq 'Maris'){
 $condition=[System.Windows.Automation.AndCondition]::new([System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$Button),[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button))
 $buttons=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
 foreach($b in $buttons){if($b.Current.ProcessId -eq $RootPid){$matches+=,$b}}
}}
if($Button -notin @('保留','明确删除','知道了','隐藏到托盘','退出','取消')){throw 'button_not_allowed'}
if($matches.Count -ne 1){throw 'owned_dialog_button_ambiguous'}
$invoke=$matches[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern);$invoke.Invoke()
[pscustomobject]@{rootVerified=$true;matchingButtons=$matches.Count;invoked=$true}|ConvertTo-Json -Compress

Stage $stage 'terminal' @{status='success';matched=$matches.Count}
}catch{
 $type=$_.Exception.GetType().Name
 $safeType=if($type -in @('CimException','UnauthorizedAccessException','Win32Exception','RuntimeException','InvalidOperationException','MethodInvocationException','FileNotFoundException')){$type}else{'unknown'}
 $code=if($_.Exception.Message -in @('root_identity_changed','root_not_owned','owned_main_ambiguous','button_not_allowed','owned_dialog_button_ambiguous')){$_.Exception.Message}else{'unknown'}
 Stage $stage 'terminal' @{status='error';errorName=$safeType;code=$code;hresult=$_.Exception.HResult}
 @{ok=$false;stage=$stage;errorName=$_.Exception.GetType().FullName;code=$code;hresult=$_.Exception.HResult;nativeErrorCode=if($_.Exception.PSObject.Properties['NativeErrorCode']){[string]$_.Exception.NativeErrorCode}else{$null};statusCode=if($_.Exception.PSObject.Properties['StatusCode']){[string]$_.Exception.StatusCode}else{$null};category=[string]$_.CategoryInfo.Category}|ConvertTo-Json -Compress
 exit 3
}
