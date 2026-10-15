function Invoke-PortablePython {
    param([string[]]$PythonArguments)
    $OutputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $env:PYTHONIOENCODING = 'utf-8'
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        $usable=$false
        try { & $python.Source -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 2)' 2>$null; $usable=($LASTEXITCODE -eq 0) } catch { $usable=$false }
        if ($usable) { & $python.Source @PythonArguments; return }
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $usable=$false
        try { & $launcher.Source -3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 2)' 2>$null; $usable=($LASTEXITCODE -eq 0) } catch { $usable=$false }
        if ($usable) { & $launcher.Source -3 @PythonArguments; return }
    }
    throw 'Install Python 3.10 or newer for Windows, enable its PATH option, then reopen PowerShell. See INSTALL.zh-CN.md.'
}
