param([Parameter(Mandatory=$true)][string]$Project)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Find-Python.ps1')
Invoke-PortablePython -PythonArguments @((Join-Path $PSScriptRoot 'portable_install.py'),'uninstall','--project',$Project)
exit $LASTEXITCODE
