param([string]$ArchivePath)
$ErrorActionPreference='Stop'
$OutputEncoding=[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$expectedCli='efcd697b940f78b6457829453888d9c608f19d2fcd331d0005b1ff47a7839357'
$expectedZip='b675d53806a63463f15f7bd50862ede62fb5eb7604bec24c3ce6a51d517c84bd'
$destination=Join-Path $PSScriptRoot 'unity-cli.exe'
if(Test-Path -LiteralPath $destination) {
    if((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $expectedCli) { throw 'An existing CLI differs from the pinned version; preserving it.' }
    Write-Output 'Pinned unity-cli 0.18.1 is already present.'
    exit 0
}
$token=[Guid]::NewGuid().ToString('N')
$temporaryZip=Join-Path ([IO.Path]::GetTempPath()) ('unity-cli-'+$token+'.zip')
$temporaryExe=Join-Path $PSScriptRoot ('.unity-cli-'+$token+'.tmp')
try {
    if($ArchivePath) { $archive=(Resolve-Path -LiteralPath $ArchivePath -ErrorAction Stop).ProviderPath }
    else {
        $archive=$temporaryZip
        [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/0everey/unity-cli-2023-portable/releases/download/v0.18.1-r1/UnityCLI2023-Portable-0.18.1-r1-20261015.zip' -OutFile $archive -TimeoutSec 300
    }
    if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expectedZip) { throw 'Release ZIP SHA256 mismatch; nothing installed.' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip=[IO.Compression.ZipFile]::OpenRead($archive)
    try {
        $entry=$zip.GetEntry('UnityCLI2023-Portable-0.18.1-r1-20261015/unity-cli.exe')
        if($null -eq $entry) { throw 'Pinned CLI is missing from the release ZIP.' }
        $inputStream=$entry.Open()
        $outputStream=[IO.File]::Open($temporaryExe,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $inputStream.CopyTo($outputStream) }
        finally { $outputStream.Dispose(); $inputStream.Dispose() }
    } finally { $zip.Dispose() }
    if((Get-FileHash -LiteralPath $temporaryExe -Algorithm SHA256).Hash -ne $expectedCli) { throw 'CLI SHA256 mismatch; nothing installed.' }
    [IO.File]::Move($temporaryExe,$destination)
    Write-Output 'Installed pinned unity-cli 0.18.1; ZIP and executable SHA256 both verified.'
} finally {
    foreach($temporary in @($temporaryZip,$temporaryExe)) {
        if(Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
    }
}
