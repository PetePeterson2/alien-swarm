# Build HALCYON DRIFT and open it in the installed StarCraft II client.
#
#   .\launch.ps1            build the playable map and hand it to SC2
#   .\launch.ps1 -QA        build with script errors shown on screen
#   .\launch.ps1 -NoBuild   launch the last build
#
# Adapted from ../../Documents/GameNight/launch.ps1. If StarCraft II is already
# open, the switcher hands the map to that client and brings it to the front,
# so only run this while that client is sitting in its menus.
param([switch]$QA, [switch]$Demo, [switch]$NoBuild)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$installRoot = 'C:\Program Files (x86)\StarCraft II'
$name = if ($Demo) { 'AlienPOC-Demo' } elseif ($QA) { 'AlienPOC-QA' } else { 'AlienPOC' }
if (-not $NoBuild) {
    $buildArgs = @((Join-Path $projectRoot 'build.py'))
    if ($QA) { $buildArgs += '--qa' }
    if ($Demo) { $buildArgs += '--demo' }
    & py @buildArgs
    if ($LASTEXITCODE -ne 0) { throw 'Build failed; nothing was launched.' }
}
$mapPath = Join-Path $projectRoot "dist\$name.SC2Map"
$testRoot = Join-Path $installRoot 'Maps\Test'
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
# A client still holding the previous build keeps a lock on it: stage under a fresh name instead.
$stageName = "$name.SC2Map"
try { Copy-Item -LiteralPath $mapPath -Destination (Join-Path $testRoot $stageName) -Force -ErrorAction Stop }
catch [System.IO.IOException] {
    $stageName = '{0}-{1}.SC2Map' -f $name, (Get-Date).ToString('HHmmss')
    Copy-Item -LiteralPath $mapPath -Destination (Join-Path $testRoot $stageName) -Force
}
Start-Process -FilePath (Join-Path $installRoot 'Support64\SC2Switcher_x64.exe') -ArgumentList @(
    '-run', "Test\$stageName", '-NoUserCheats', '-reloadcheck', '-speed', '2'
) -WorkingDirectory $installRoot -WindowStyle Hidden | Out-Null
"Launched Test\$stageName"
