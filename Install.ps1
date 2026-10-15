param([Parameter(Mandatory=$true)][string]$Project,[switch]$DryRun)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Find-Python.ps1')
$pythonArgs=@((Join-Path $PSScriptRoot 'portable_install.py'),'install','--project',$Project)
if($DryRun) { $pythonArgs+='--dry-run' }
Invoke-PortablePython -PythonArguments $pythonArgs
exit $LASTEXITCODE
