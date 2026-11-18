param(
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if ($Port -lt 1 -or $Port -gt 65535) {
    throw "Port must be between 1 and 65535."
}

$VirtualEnvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VirtualEnvPython)) {
    $BasePython = $null
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($Launcher) {
        $Candidates = @()
        foreach ($Line in (& $Launcher.Source -0p 2>$null)) {
            if ($Line -match '^\s*-(?:V:)?(?<Major>\d+)\.(?<Minor>\d+)(?:-\d+)?\s+(?:\*\s+)?(?<Path>.*pythonw?\.exe)\s*$') {
                $Major = [int]$Matches.Major
                $Minor = [int]$Matches.Minor
                if ($Major -gt 3 -or ($Major -eq 3 -and $Minor -ge 10)) {
                    $Candidates += [pscustomobject]@{
                        Major = $Major
                        Minor = $Minor
                        Path = $Matches.Path.Trim()
                    }
                }
            }
        }
        $BasePython = $Candidates |
            Sort-Object Major, Minor -Descending |
            Select-Object -First 1 -ExpandProperty Path
    }

    if (-not $BasePython) {
        $PythonCommand = Get-Command python, python3 -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($PythonCommand) {
            $VersionOutput = & $PythonCommand.Source --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $VersionOutput -match "Python (\d+)\.(\d+)") {
                $Major = [int]$Matches[1]
                $Minor = [int]$Matches[2]
                if ($Major -gt 3 -or ($Major -eq 3 -and $Minor -ge 10)) {
                    $BasePython = $PythonCommand.Source
                }
            }
        }
    }

    if (-not $BasePython) {
        throw "Python 3.10 or newer was not found. Install Python and rerun this script."
    }

    $VersionOutput = & $BasePython --version 2>&1
    Write-Host "Creating project virtual environment with $VersionOutput..."
    $VirtualEnvDirectory = Join-Path $ProjectRoot ".venv"
    & $BasePython -m venv $VirtualEnvDirectory | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create .venv with $VersionOutput."
    }
}

$Python = $VirtualEnvPython
$VersionOutput = & $Python --version 2>&1
if ($LASTEXITCODE -ne 0 -or $VersionOutput -notmatch "Python (\d+)\.(\d+)") {
    throw "Could not determine the project virtual environment Python version."
}
$Major = [int]$Matches[1]
$Minor = [int]$Matches[2]
if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 10)) {
    throw ".venv uses $VersionOutput; Python 3.10 or newer is required. Recreate .venv with a supported interpreter."
}

$DependenciesAvailable = & $Python -c "import importlib.util; modules = ('pandas', 'cryptography'); raise SystemExit(0 if all(importlib.util.find_spec(name) for name in modules) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing or repairing project dependencies from requirements.txt..."
    & $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed. Check Python/pip availability and retry."
    }
}

$Arguments = @("-m", "climate_dashboard.launcher", "--port", "$Port")
if ($NoBrowser) {
    $Arguments += "--no-browser"
}
Write-Host "Launching dashboard with $VersionOutput..."
& $Python @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard command exited with code $LASTEXITCODE."
}
