# Shared real Windows parser: used by both synthetic cases and CIM observation.
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using System.ComponentModel;
public static class R9R2Argv {
 [DllImport("shell32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern IntPtr CommandLineToArgvW(string s,out int n);
 [DllImport("kernel32.dll")]static extern IntPtr LocalFree(IntPtr p);
 public static string[] Parse(string value){if(String.IsNullOrWhiteSpace(value)||value.IndexOf('\0')>=0)throw new ArgumentException("invalid_command_line");int count;IntPtr p=CommandLineToArgvW(value,out count);if(p==IntPtr.Zero)throw new Win32Exception(Marshal.GetLastWin32Error());try{var a=new string[count];for(int i=0;i<count;i++)a[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(p,i*IntPtr.Size));return a;}finally{LocalFree(p);}}
}
'@
function Parse-RootCommand([string]$Value) {
 try { return @{ok=$true;argv=@([R9R2Argv]::Parse($Value))} }
 catch { return @{ok=$false;argv=$null;errorType='command_line_parse_failed'} }
}
function Path-WithoutReparse([string]$Value){
 if($Value -cnotmatch '^[A-Z]:[\\/]'){return $false}
 try{
  $cursor=[IO.Path]::GetFullPath($Value)
  while($cursor){$item=Get-Item -LiteralPath $cursor -Force -ErrorAction Stop;if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){return $false};$parent=[IO.Path]::GetDirectoryName($cursor);if($parent -eq $cursor){break};$cursor=$parent}
  return $true
 }catch{return $false}
}
