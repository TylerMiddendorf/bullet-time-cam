[CmdletBinding()]
param(
    [string]$Fqbn = "esp32:esp32:XIAO_ESP32S3:PSRAM=opi",
    [string]$BuildPath = ".build\button_capture"
)

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$sketchPath = Join-Path $repoRoot "button_capture"
$resolvedBuildPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $BuildPath))
$buildRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".build"))
if (-not $resolvedBuildPath.StartsWith($buildRoot + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "BuildPath must stay below $buildRoot"
}

$arduinoCli = Join-Path $env:LOCALAPPDATA "CodexTools\arduino-cli\arduino-cli.exe"
if (-not (Test-Path -LiteralPath $arduinoCli)) {
    $arduinoCli = (Get-Command arduino-cli -ErrorAction Stop).Source
}

New-Item -ItemType Directory -Force -Path $resolvedBuildPath | Out-Null
& $arduinoCli compile --fqbn $Fqbn --build-path $resolvedBuildPath $sketchPath
if ($LASTEXITCODE -ne 0) {
    throw "Arduino firmware compile failed with exit code $LASTEXITCODE"
}

Write-Host "Firmware build artifacts: $resolvedBuildPath"
