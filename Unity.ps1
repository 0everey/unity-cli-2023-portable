param([string]$Project)
$ErrorActionPreference='Stop'
if(-not $Project) { throw 'Use -Project followed by the Unity project root.' }
. (Join-Path $PSScriptRoot 'Find-Python.ps1')
Invoke-PortablePython -PythonArguments (@((Join-Path $PSScriptRoot 'unity2023.py'),'--project',$Project)+$args)
exit $LASTEXITCODE
