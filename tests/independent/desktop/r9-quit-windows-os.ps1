param([ValidateSet('snapshot','close','dialog')][string]$Action='snapshot',[int]$RootPid,[int]$ExpectedParentPid,[string]$StartedUtc,[string]$Button='',[string]$KnownJson='[]')
$ErrorActionPreference='Stop'
$exe='C:\MarisQuitR7\R7-20261014-191500\workspace\apps\desktop\out\Maris-win32-x64\Maris.exe'
$all=@(Get-CimInstance Win32_Process)
$root=$all|Where-Object ProcessId -eq $RootPid
$start=[DateTimeOffset]::Parse($StartedUtc).UtcDateTime
$verified=$root -and $root.ExecutablePath -eq $exe -and $root.ParentProcessId -eq $ExpectedParentPid -and $root.CreationDate.ToUniversalTime() -ge $start.AddSeconds(-2)
$known=@($KnownJson|ConvertFrom-Json)
$ids=[System.Collections.Generic.HashSet[int]]::new()
if($verified){[void]$ids.Add($RootPid)}elseif($root){throw 'root_identity_changed'}
foreach($k in $known){$v=$all|Where-Object ProcessId -eq $k.pid;if($v -and $v.CreationDate.ToUniversalTime().ToString('o') -eq $k.created){[void]$ids.Add([int]$k.pid)}}
$changed=$true;while($changed){$changed=$false;foreach($v in $all){if($ids.Contains([int]$v.ParentProcessId) -and $v.CreationDate.ToUniversalTime() -ge $start.AddSeconds(-2)){if($ids.Add([int]$v.ProcessId)){$changed=$true}}}}
$owned=@($all|Where-Object {$ids.Contains([int]$_.ProcessId)}|ForEach-Object {[pscustomobject]@{pid=[int]$_.ProcessId;parentPid=[int]$_.ParentProcessId;created=$_.CreationDate.ToUniversalTime().ToString('o');kind=if($_.ExecutablePath -eq $exe){'product'}elseif($_.Name -eq 'python.exe'){'python'}elseif($_.Name -eq 'conhost.exe'){'conhost'}else{'other'}}})
 Add-Type -TypeDefinition @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;using System.Text;
public static class R9Windows {public delegate bool CB(IntPtr h,IntPtr l);[DllImport("user32.dll")]public static extern bool EnumWindows(CB cb,IntPtr l);[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);[DllImport("user32.dll",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32.dll")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);public static int Count(int[] ps){int n=0;EnumWindows((h,l)=>{uint id;GetWindowThreadProcessId(h,out id);if(Array.IndexOf(ps,(int)id)>=0)n++;return true;},IntPtr.Zero);return n;}public static List<IntPtr> Main(int p){var a=new List<IntPtr>();EnumWindows((h,l)=>{uint id;GetWindowThreadProcessId(h,out id);var s=new StringBuilder(256);GetWindowText(h,s,256);if(id==p&&s.ToString()=="Maris")a.Add(h);return true;},IntPtr.Zero);return a;}}
'@
if($Action -eq 'snapshot'){
 $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$ids.Contains([int]$_.OwningProcess)}|ForEach-Object {[pscustomobject]@{pid=[int]$_.OwningProcess;port=[int]$_.LocalPort;loopback=($_.LocalAddress -eq '127.0.0.1' -or $_.LocalAddress -eq '::1')}})
 [pscustomobject]@{rootVerified=[bool]$verified;rootPresent=[bool]$root;owned=$owned;listeners=$listeners;windowCount=[R9Windows]::Count([int[]]@($ids))}|ConvertTo-Json -Depth 5 -Compress
 exit 0
}
if(-not $verified){throw 'root_not_owned'}
if($Action -eq 'close'){

 $windows=[R9Windows]::Main($RootPid);if($windows.Count -ne 1){throw 'owned_main_ambiguous'}
 $posted=[R9Windows]::PostMessage($windows[0],0x0010,[IntPtr]::Zero,[IntPtr]::Zero)
 [pscustomobject]@{rootVerified=$true;matchingMainWindows=$windows.Count;closePosted=$posted;postedUtc=[DateTimeOffset]::UtcNow.ToString('o');rootPid=$RootPid;parentVerified=$true}|ConvertTo-Json -Compress
 exit 0
}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
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
