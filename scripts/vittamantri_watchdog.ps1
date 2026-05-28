$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$LogDir = Join-Path $ProjectRoot "logs"
$PythonExe = "C:\anaconda3\python.exe"
$NpmExe = "npm.cmd"

$BackendScript = Join-Path $BackendDir "main.py"
$BotScript = Join-Path $BackendDir "bot.py"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Content -Path (Join-Path $LogDir "watchdog.pid") -Value $PID

function Write-WatchdogLog {
    param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path (Join-Path $LogDir "watchdog.log") -Value "$stamp $Message"
}

function Get-PythonAppProcess {
    param([string]$ScriptPath)
    Get-CimInstance Win32_Process -Filter "name = 'python.exe' OR name = 'pythonw.exe'" |
        Where-Object { $_.CommandLine -like "*$ScriptPath*" }
}

function Get-ViteProcess {
    Get-CimInstance Win32_Process -Filter "name = 'node.exe'" |
        Where-Object {
            $_.CommandLine -like "*$FrontendDir*" -and
            $_.CommandLine -like "*vite*"
        }
}

function Ensure-Flask {
    $existing = Get-PythonAppProcess -ScriptPath $BackendScript
    if ($existing) {
        return
    }

    $process = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList "`"$BackendScript`"" `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput (Join-Path $LogDir "flask.out.log") `
        -RedirectStandardError (Join-Path $LogDir "flask.err.log") `
        -WindowStyle Hidden `
        -PassThru

    Write-WatchdogLog "Started Flask backend pid=$($process.Id)"
}

function Ensure-Bot {
    $existing = Get-PythonAppProcess -ScriptPath $BotScript
    if ($existing) {
        return
    }

    $process = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList "`"$BotScript`"" `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput (Join-Path $LogDir "bot.out.log") `
        -RedirectStandardError (Join-Path $LogDir "bot.err.log") `
        -WindowStyle Hidden `
        -PassThru

    Write-WatchdogLog "Started Telegram bot pid=$($process.Id)"
}

function Ensure-Frontend {
    $existing = Get-ViteProcess
    if ($existing) {
        return
    }

    $process = Start-Process `
        -FilePath $NpmExe `
        -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput (Join-Path $LogDir "vite.out.log") `
        -RedirectStandardError (Join-Path $LogDir "vite.err.log") `
        -WindowStyle Hidden `
        -PassThru

    Write-WatchdogLog "Started React dashboard pid=$($process.Id)"
}

Write-WatchdogLog "VittaMantri watchdog started pid=$PID"

while ($true) {
    try {
        Ensure-Flask
        Start-Sleep -Seconds 3
        Ensure-Bot
        Start-Sleep -Seconds 3
        Ensure-Frontend
    }
    catch {
        Write-WatchdogLog "Watchdog error: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds 15
}
