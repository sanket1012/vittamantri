$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WatchdogScript = Join-Path $PSScriptRoot "vittamantri_watchdog.ps1"

$existing = Get-CimInstance Win32_Process -Filter "name = 'powershell.exe'" |
    Where-Object { $_.CommandLine -like "*$WatchdogScript*" }

if ($existing) {
    "VittaMantri watchdog is already running."
    exit 0
}

Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$WatchdogScript`"" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden

"VittaMantri watchdog started."
