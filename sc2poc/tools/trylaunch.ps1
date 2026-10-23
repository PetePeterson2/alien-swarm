# Close this project's own test client, launch the last build, and print the
# script log the client writes once the map has loaded (or after 90 s).
param([switch]$QA, [switch]$Demo, [switch]$Kit, [switch]$KitPainted, [switch]$Auto)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Get-CimInstance Win32_Process -Filter "name='SC2_x64.exe'" | Where-Object { $_.CommandLine -like '*-run Test\AlienPOC*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Start-Sleep -Seconds 3 }
$logs = Join-Path $env:USERPROFILE 'OneDrive\Documents\StarCraft II\GameLogs'
$start = Get-Date
if ($KitPainted) { & (Join-Path $root 'launch.ps1') -NoBuild -KitPainted } elseif ($Kit) { & (Join-Path $root 'launch.ps1') -NoBuild -Kit } elseif ($Auto) { & (Join-Path $root 'launch.ps1') -NoBuild -Auto } elseif ($Demo) { & (Join-Path $root 'launch.ps1') -NoBuild -Demo } elseif ($QA) { & (Join-Path $root 'launch.ps1') -NoBuild -QA } else { & (Join-Path $root 'launch.ps1') -NoBuild }
$deadline = $start.AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
    $err = Get-ChildItem $logs -Filter '*ScriptError.txt' | Where-Object { $_.LastWriteTime -gt $start } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($err) { Start-Sleep -Seconds 4; "=== $($err.Name)"; Get-Content $err.FullName | Select-Object -Skip 21; break }
}
if (-not $err) { 'No script errors logged within 90 s.' }
$alerts = Get-ChildItem $logs -Filter '*Alerts.txt' | Where-Object { $_.LastWriteTime -gt $start } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($alerts) { "=== $($alerts.Name)"; Get-Content $alerts.FullName | Select-Object -Skip 21 | Select-Object -First 60 }
