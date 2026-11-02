$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot 'evidence/r11-origin-settings/capability.json'
if(Test-Path -LiteralPath $out){throw 'first_exists'}
$result=@{at=[DateTimeOffset]::Now.ToString('o');passed=$false;stage='process_query';productStarts=0;helperStarts=0;readOnly=$true}
try {
 $all=@(Get-CimInstance Win32_Process -ErrorAction Stop)
 $roots=@('C:\MarisC12\C12-R9-QUIT-20261016-011200','C:\MarisC12\C12-R9-R1-20261017-001500','C:\MarisC12\C12-R9-R2-20261017-233500','C:\MarisC12\C12-R9-R3-20261018-105500','C:\MarisIpcR9\R9-20261101-161412')
 $matches=@($all|Where-Object {$entry=$_;@($roots|Where-Object {($entry.CommandLine -and $entry.CommandLine.Contains($_)) -or ($entry.ExecutablePath -and $entry.ExecutablePath.StartsWith($_,[StringComparison]::OrdinalIgnoreCase))}).Count -gt 0})
 # Exclude this observer and the invoking shell command, whose arguments name the read-only script only.
 $result.remainingTargetProcesses=$matches.Count
 if($matches.Count){throw 'target_process_present'}
 $result.stage='listener_query';$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop);$result.listenerQueryAvailable=$true
 $result.stage='native_uia_load'
 try {Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop;Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop;$result.uiaAssemblyAvailable=$true}
 catch [System.IO.FileNotFoundException] {$result.uiaAssemblyAvailable=$false;$result.uiaUnavailableReason='UIAutomation_assembly_not_found'}
 if($result.uiaAssemblyAvailable){
  $result.stage='native_uia_read'
  $desktop=[System.Windows.Automation.AutomationElement]::RootElement
  $top=$desktop.FindAll([System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
  $result.uiaReadAvailable=$true;$result.topLevelCount=$top.Count
  $condition=[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ClassNameProperty,'Shell_TrayWnd')
  $trays=$desktop.FindAll([System.Windows.Automation.TreeScope]::Children,$condition)
  $result.trayRootCount=$trays.Count
  $result.trayOwnIconActionAdapter=$false
  $result.trayUnavailableReason='existing_frozen_adapter_has_no_owned_tray_icon_action'
 }
 $result.stage='finished';$result.passed=$true
}catch{
 $result.errorName=$_.Exception.GetType().Name
 $result.hresult=$_.Exception.HResult
 $result.code=if($_.Exception.Message -eq 'target_process_present'){'target_process_present'}else{'unknown'}
}finally{
 [IO.File]::WriteAllText($out,(($result|ConvertTo-Json -Depth 6)+"`n"),[Text.UTF8Encoding]::new($false))
 $result|ConvertTo-Json -Depth 6
}
if(-not $result.passed){exit 1}
