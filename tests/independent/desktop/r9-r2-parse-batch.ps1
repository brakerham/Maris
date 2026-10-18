param([Parameter(Mandatory)][string]$InputPath,[Parameter(Mandatory)][string]$OutputPath)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'r9-r2-parser.ps1')
$cases=Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8|ConvertFrom-Json
$rows=@(foreach($case in $cases){@{id=$case.id;parsed=(Parse-RootCommand $case.command)}})
$text=ConvertTo-Json -InputObject $rows -Depth 8
[IO.File]::WriteAllText($OutputPath,$text,[Text.UTF8Encoding]::new($false))
