$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

$iconArgs = @()
if (Test-Path "$scriptDir/assets/icon.ico") {
    $iconArgs = @("--icon", "assets/icon.ico")
}

.\.venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --name KAIRO @iconArgs main.py
