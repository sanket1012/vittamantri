$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendScript = Join-Path $BackendDir "main.py"
$BotScript = Join-Path $BackendDir "bot.py"
$WatchdogScript = Join-Path $PSScriptRoot "vittamantri_watchdog.ps1"

$watchdogs = Get-CimInstance Win32_Process -Filter "name = 'powershell.exe'" |
    Where-Object { $_.CommandLine -like "*$WatchdogScript*" }

foreach ($process in $watchdogs) {
    Stop-Process -Id $process.ProcessId -Force
}

$pythonProcesses = Get-CimInstance Win32_Process -Filter "name = 'python.exe' OR name = 'pythonw.exe'" |
    Where-Object {
        $_.CommandLine -like "*$BackendScript*" -or
        $_.CommandLine -like "*$BotScript*" -or
        $_.CommandLine -like "* main.py*" -or
        $_.CommandLine -like "* bot.py*"
    }

foreach ($process in $pythonProcesses) {
    Stop-Process -Id $process.ProcessId -Force
}

$viteProcesses = Get-CimInstance Win32_Process -Filter "name = 'node.exe'" |
    Where-Object {
        $_.CommandLine -like "*$FrontendDir*" -and
        $_.CommandLine -like "*vite*"
    }

foreach ($process in $viteProcesses) {
    Stop-Process -Id $process.ProcessId -Force
}

"Stopped VittaMantri watchdog, backend, bot, and dashboard."
