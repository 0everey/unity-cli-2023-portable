$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Find-Python.ps1')
Invoke-PortablePython -PythonArguments @((Join-Path $PSScriptRoot 'portable_install.py'),'verify')
exit $LASTEXITCODE
