#Requires -Version 5.1
<#
.SYNOPSIS
    Bootstrap this repository on Windows.

.DESCRIPTION
    Creates .venv, installs the package editable with the dev and docs extras, prints the read-only
    environment report, registers the git hooks, installs the trainer's node dependencies if trainer/
    exists, and prints the next steps.

    It never runs elevated, never installs into a global interpreter, and never touches data/gen:
    regeneration is a decision you make on purpose (adr/0001), not a side effect of installing.

    Every tool call goes through "<python> -m <module>" rather than a bare command name, because pip
    puts Windows console scripts in %APPDATA%\Python\Python312\Scripts, which is frequently not on
    PATH. See docs/development/local-dev.md.

.PARAMETER PythonExe
    Path or command name of the interpreter to build the venv with. When omitted, candidates are probed
    and each one has to actually print a Python version >= 3.11: a command that exists but is a stub
    (Windows Store alias, or a moved c:\python312\python.exe) is rejected here instead of failing later
    inside pip.

.PARAMETER NoTrainer
    Skip npm ci even when trainer/package.json exists.

.PARAMETER SkipHooks
    Skip "pre-commit install" and the first full hook run.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File setup/install.ps1

.EXAMPLE
    pwsh setup/install.ps1 -PythonExe C:\Python312\python.exe -NoTrainer
#>
[CmdletBinding()]
param(
    [string]$PythonExe,
    [switch]$NoTrainer,
    [switch]$SkipHooks
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSCommandPath | Split-Path -Parent
Set-Location -Path $Root

function Say([string]$Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Note([string]$Message) { Write-Host "warn: $Message" -ForegroundColor Yellow }

function Test-PythonCandidate([string]$Candidate, [string[]]$ExtraArgs) {
    <#
    A candidate is usable only if it runs and reports 3.11+. `Get-Command` alone is not enough on
    Windows: store aliases and moved installs resolve to a file that cannot start.
    #>
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $false }
    try {
        $probe = & $Candidate @ExtraArgs '-c' 'import sys; print("%d.%d" % sys.version_info[:2])' 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $probe) { return $false }
        $parts = "$probe".Trim().Split('.')
        if ($parts.Count -ne 2) { return $false }
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        return ($major -eq 3 -and $minor -ge 11)
    }
    catch {
        return $false
    }
}

function Get-BootstrapPython {
    if ($PythonExe) {
        if (Test-PythonCandidate $PythonExe @()) { return @{ Command = $PythonExe; Args = @() } }
        throw "-PythonExe $PythonExe is not a usable Python >= 3.11"
    }
    $plain = @('python', 'python3', 'python3.12', 'python3.11')
    foreach ($candidate in $plain) {
        if (Test-PythonCandidate $candidate @()) { return @{ Command = $candidate; Args = @() } }
    }
    # The py launcher is the other way Windows installs get found; it takes the version as an argument.
    foreach ($flag in @('-3.12', '-3.11', '-3') ) {
        if (Test-PythonCandidate 'py' @($flag)) { return @{ Command = 'py'; Args = @($flag) } }
    }
    throw 'no Python >= 3.11 found. Install one (winget install Python.Python.3.12) and re-run.'
}

$chosen = Get-BootstrapPython
$resolvedVersion = & $chosen.Command @($chosen.Args) '-c' 'import sys; print(sys.version.split()[0])'
Say "using interpreter: $($chosen.Command) $($chosen.Args -join ' ') ($resolvedVersion)"

# --- fail early on a repository-state problem, not a pip one ------------------------------------
# pyproject declares readme = "README.md". If that file is absent, `pip install -e .` dies inside
# metadata generation with an error that names neither the file nor the cause, and a contributor can
# spend an hour blaming their environment. Checked here so the message is about the real problem.
if (Test-Path (Join-Path $Root 'pyproject.toml')) {
    $readmeLine = Select-String -Path (Join-Path $Root 'pyproject.toml') -Pattern '^\s*readme\s*=' |
        Select-Object -First 1
    if ($readmeLine -and $readmeLine.Line -match '"([^"]+)"') {
        $declared = $Matches[1]
        if (-not (Test-Path (Join-Path $Root $declared))) {
            Note "pyproject.toml declares readme = `"$declared`" but $Root\$declared does not exist."
            Note 'pip install -e . will fail on metadata generation. This is a repository-state issue;'
            Note 'no amount of reinstalling or re-creating the venv will fix it.'
            exit 1
        }
    }
}

# --- virtual environment ------------------------------------------------------------------------
$Venv = Join-Path $Root '.venv'
if (-not (Test-Path $Venv)) {
    Say 'creating .venv'
    & $chosen.Command @($chosen.Args) -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "python -m venv failed with exit $LASTEXITCODE" }
}
else {
    Say '.venv exists; reusing it (remove the directory for a clean rebuild)'
}

if (Test-Path (Join-Path $Venv 'Scripts\python.exe')) {
    $VenvPy = Join-Path $Venv 'Scripts\python.exe'   # Windows layout
}
else {
    $VenvPy = Join-Path $Venv 'bin/python'           # POSIX layout, for pwsh on Linux/macOS
}

Say 'installing pokergto editable with dev + docs extras'
& $VenvPy -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
& $VenvPy -m pip install -e '.[dev,docs]'
if ($LASTEXITCODE -ne 0) { throw 'pip install -e ".[dev,docs]" failed; read the output above' }

Say 'environment report (read-only)'
& $VenvPy (Join-Path $Root 'setup\doctor.py')
if ($LASTEXITCODE -ne 0) { Note 'doctor reported failures -- read the lines above before continuing' }

# --- git hooks ------------------------------------------------------------------------------------
# Registering the hooks is what makes the gates run without anyone remembering to run them. It writes
# only .git/hooks. The first full run is expected to report failures at M0 on a few gates whose
# baseline is still being authored; those are listed in docs/development/local-dev.md.
$gitDir = Join-Path $Root '.git'
if ((-not $SkipHooks) -and (Test-Path $gitDir)) {
    & $VenvPy -c 'import pre_commit' 2>$null
    if ($LASTEXITCODE -eq 0) {
        Say 'installing pre-commit git hooks'
        & $VenvPy -m pre_commit install
        Say 'running every hook once, over all files'
        & $VenvPy -m pre_commit run --all-files
        if ($LASTEXITCODE -ne 0) { Note 'hooks reported failures; some are known M0 baseline gates' }
    }
    else {
        Note 'pre-commit is not importable in the new venv; skipping hook registration'
    }
}

# --- trainer --------------------------------------------------------------------------------------
if ($NoTrainer) {
    Say 'trainer: skipped (-NoTrainer)'
}
elseif (Test-Path (Join-Path $Root 'trainer\package.json')) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
        Say 'installing trainer node dependencies (npm ci)'
        Push-Location (Join-Path $Root 'trainer')
        try { npm ci } finally { Pop-Location }
    }
    else {
        Note 'trainer/package.json exists but npm is not on PATH; skipping npm ci'
    }
}
else {
    Say 'trainer: skipped (no trainer/package.json yet)'
}

# --- next steps -----------------------------------------------------------------------------------
@'

Next steps

  1. activate the environment in your shell:
       .venv\Scripts\Activate.ps1        (PowerShell)
       .venv\Scripts\activate            (Git Bash)
       cmd: .venv\Scripts\activate.bat
  2. confirm the tools are reachable through the interpreter:
       python -m ruff check .
       python -m pytest
       python -m mkdocs build --strict
  3. read the two docs that decide how you work here:
       docs\development\local-dev.md         (which commands actually run on this machine)
       docs\development\bilingual-style.md   (both languages, or the pull request is red)
  4. serve the site while you write:
       python -m mkdocs serve                http://127.0.0.1:8000
  5. use the CLI through the module form, which needs no PATH change:
       python -m pokergto mdf --pot 1 --bet 0.5 --lang zh

Two Windows-specific facts worth knowing now:

  - Bare ruff, mkdocs and poker may still be "command not found". pip puts its console scripts in
    %APPDATA%\Python\Python312\Scripts, which is frequently not on PATH. python -m <tool> always works,
    because it runs the module the interpreter can already see; adding that directory to PATH is
    optional and per-machine, never per-repository.
  - Chinese CLI output needs a UTF-8 console. The CLI reconfigures its own streams, so --lang zh prints
    correctly; type, cat and redirected files depend on the terminal code page instead (chcp 65001, or
    run python with -X utf8).
'@ | Write-Host

exit 0
