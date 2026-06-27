[CmdletBinding()]
param(
    [string]$Port,
    [string]$RepositoryRoot,
    [string]$Sketch = "button_capture",
    [string]$Fqbn = "esp32:esp32:XIAO_ESP32S3:PSRAM=opi",
    [string]$ArduinoCli,
    [ValidateRange(5, 120)]
    [int]$VerifyTimeoutSeconds = 20,
    [switch]$CompileOnly,
    [switch]$SkipVerify,
    [switch]$KeepBuild
)

$ErrorActionPreference = "Stop"

function Resolve-ArduinoCli {
    param([string]$RequestedPath)

    if ($RequestedPath) {
        if (Test-Path -LiteralPath $RequestedPath -PathType Leaf) {
            return (Resolve-Path -LiteralPath $RequestedPath).Path
        }

        $requestedCommand = Get-Command $RequestedPath -ErrorAction SilentlyContinue
        if ($requestedCommand) {
            return $requestedCommand.Source
        }

        throw "Arduino CLI was not found at '$RequestedPath'."
    }

    $localCli = Join-Path $env:LOCALAPPDATA "CodexTools\arduino-cli\arduino-cli.exe"
    if (Test-Path -LiteralPath $localCli -PathType Leaf) {
        return $localCli
    }

    $pathCommand = Get-Command "arduino-cli" -ErrorAction SilentlyContinue
    if ($pathCommand) {
        return $pathCommand.Source
    }

    throw "Arduino CLI was not found. Install it or pass -ArduinoCli <path>."
}

function Find-RepositoryRoot {
    param([string]$StartPath)

    $current = [System.IO.DirectoryInfo](Resolve-Path -LiteralPath $StartPath).Path
    while ($current) {
        $sketchFile = Join-Path $current.FullName "button_capture\button_capture.ino"
        $agentsFile = Join-Path $current.FullName "AGENTS.md"
        if ((Test-Path -LiteralPath $sketchFile -PathType Leaf) -and
            (Test-Path -LiteralPath $agentsFile -PathType Leaf)) {
            return $current.FullName
        }

        $current = $current.Parent
    }

    return $null
}

function Invoke-Arduino {
    param([string[]]$CliArguments)

    & $script:CliPath @CliArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Arduino CLI failed with exit code $LASTEXITCODE while running: $($CliArguments -join ' ')"
    }
}

function Get-DetectedEsp32Ports {
    $json = & $script:CliPath board list --format json
    if ($LASTEXITCODE -ne 0) {
        throw "Arduino CLI could not discover connected boards."
    }

    $boardList = $json | ConvertFrom-Json
    return @(
        $boardList.detected_ports |
            Where-Object {
                $_.port.protocol -eq "serial" -and
                @($_.matching_boards | Where-Object { $_.fqbn -like "esp32:esp32:*" }).Count -gt 0
            } |
            ForEach-Object { $_.port.address }
    )
}

function Resolve-UploadPort {
    param([string]$RequestedPort)

    $detected = @(Get-DetectedEsp32Ports)

    if ($RequestedPort) {
        if ($detected -notcontains $RequestedPort) {
            $listed = if ($detected.Count) { $detected -join ", " } else { "none" }
            throw "Requested port '$RequestedPort' is not a detected ESP32 serial port. Detected: $listed."
        }

        return $RequestedPort
    }

    if ($detected.Count -eq 0) {
        throw "No ESP32 serial port was detected. Reconnect the board or enter BOOT mode, then retry."
    }

    if ($detected.Count -gt 1) {
        throw "Multiple ESP32 serial ports were detected ($($detected -join ', ')). Pass -Port COMx."
    }

    return $detected[0]
}

function Wait-ForSerialPort {
    param(
        [string]$Address,
        [int]$TimeoutSeconds = 10
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ([System.IO.Ports.SerialPort]::GetPortNames() -contains $Address) {
            return
        }
        Start-Sleep -Milliseconds 250
    }

    throw "Serial port '$Address' did not return within $TimeoutSeconds seconds after upload."
}

function Test-FirmwareStartup {
    param(
        [string]$Address,
        [int]$TimeoutSeconds
    )

    Wait-ForSerialPort -Address $Address

    $serial = [System.IO.Ports.SerialPort]::new(
        $Address,
        115200,
        [System.IO.Ports.Parity]::None,
        8,
        [System.IO.Ports.StopBits]::One
    )
    $serial.ReadTimeout = 250
    $serial.DtrEnable = $false
    $serial.RtsEnable = $false

    $cameraReady = $false
    $sdReady = $false
    $triggerReady = $false
    $fatalMessage = $null

    try {
        $serial.Open()
        $serial.DiscardInBuffer()

        # Pulse reset after opening so the complete startup sequence is observable.
        $serial.RtsEnable = $true
        Start-Sleep -Milliseconds 150
        $serial.RtsEnable = $false

        $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
        while ([DateTime]::UtcNow -lt $deadline) {
            try {
                $line = ($serial.ReadLine() -replace "[\x00\r]", "").Trim()
                if (-not $line) {
                    continue
                }

                Write-Host "[serial] $line"

                if ($line -match "^Camera ready:") {
                    $cameraReady = $true
                }
                if ($line -match "^microSD ready:") {
                    $sdReady = $true
                }
                if ($line -match "^Ready\. Pull the shared trigger LOW to capture\.$") {
                    $triggerReady = $true
                }
                if ($line -match "Stopped\.|PSRAM was not found|Camera init failed|Camera initialization failed|Card Mount Failed|No SD card attached") {
                    $fatalMessage = $line
                    break
                }
                if ($cameraReady -and $sdReady -and $triggerReady) {
                    break
                }
            }
            catch [System.TimeoutException] {
                # Keep polling until the bounded deadline.
            }
        }
    }
    finally {
        if ($serial.IsOpen) {
            $serial.Close()
        }
        $serial.Dispose()
    }

    if ($fatalMessage) {
        throw "Firmware startup failed: $fatalMessage"
    }

    $missing = @()
    if (-not $cameraReady) { $missing += "camera ready" }
    if (-not $sdReady) { $missing += "microSD ready" }
    if (-not $triggerReady) { $missing += "trigger ready" }
    if ($missing.Count) {
        throw "Firmware startup was not verified within $TimeoutSeconds seconds. Missing: $($missing -join ', ')."
    }
}

$script:CliPath = Resolve-ArduinoCli -RequestedPath $ArduinoCli

if ($RepositoryRoot) {
    $resolvedRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
}
else {
    $resolvedRoot = Find-RepositoryRoot -StartPath (Get-Location).Path
    if (-not $resolvedRoot) {
        $resolvedRoot = Find-RepositoryRoot -StartPath $PSScriptRoot
    }
}

if (-not $resolvedRoot) {
    throw "Could not locate the esp32Cam repository. Run from its root or pass -RepositoryRoot."
}

$sketchPath = Join-Path $resolvedRoot $Sketch
$sketchFile = Join-Path $sketchPath "$([System.IO.Path]::GetFileName($Sketch)).ino"
if (-not (Test-Path -LiteralPath $sketchFile -PathType Leaf)) {
    throw "Sketch entry point was not found: $sketchFile"
}

$buildPath = Join-Path ([System.IO.Path]::GetTempPath()) ("esp32Cam-xiao-" + [Guid]::NewGuid().ToString("N"))
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd("\") + "\"
$resolvedBuildPath = [System.IO.Path]::GetFullPath($buildPath)
if (-not $resolvedBuildPath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to use a build path outside the temporary directory: $resolvedBuildPath"
}

New-Item -ItemType Directory -Path $resolvedBuildPath | Out-Null

try {
    Write-Host "Repository: $resolvedRoot"
    Write-Host "Arduino CLI: $script:CliPath"
    Write-Host "Target: $Fqbn"
    Write-Host "Compiling: $sketchFile"

    Invoke-Arduino -CliArguments @(
        "compile",
        "--fqbn", $Fqbn,
        "--build-path", $resolvedBuildPath,
        $sketchPath
    )

    if ($CompileOnly) {
        Write-Host "Compile verification passed."
        return
    }

    $selectedPort = Resolve-UploadPort -RequestedPort $Port
    Write-Host "Uploading to: $selectedPort"

    Invoke-Arduino -CliArguments @(
        "upload",
        "-p", $selectedPort,
        "--fqbn", $Fqbn,
        "--input-dir", $resolvedBuildPath,
        $sketchPath
    )

    if ($SkipVerify) {
        Write-Warning "Upload passed, but serial startup verification was skipped."
        return
    }

    Write-Host "Verifying startup on $selectedPort..."
    Test-FirmwareStartup -Address $selectedPort -TimeoutSeconds $VerifyTimeoutSeconds
    Write-Host "Deployment verified: camera, microSD, and trigger startup all passed on $selectedPort."
}
finally {
    if ($KeepBuild) {
        Write-Host "Build artifacts kept at: $resolvedBuildPath"
    }
    elseif (Test-Path -LiteralPath $resolvedBuildPath) {
        Remove-Item -LiteralPath $resolvedBuildPath -Recurse -Force
    }
}
