param(
    [string]$Version = "1.0.0.0",
    [string]$Publisher = "CN=Deedarian Software Solutions",
    [string]$OutputDir = "desktop\releases\1.0.0",
    [string]$PfxPath = "",
    [string]$PfxPassword = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$stageDir = Join-Path $repoRoot "desktop\installer\msix\_stage"
$manifestTemplate = Join-Path $PSScriptRoot "AppxManifest.xml"
$manifestPath = Join-Path $stageDir "AppxManifest.xml"
$assetsDir = Join-Path $stageDir "Assets"
$desktopDist = Join-Path $repoRoot "dist\DriveSphereDesktop"
$backendDist = Join-Path $repoRoot "dist\DriveSphereBackend"
$logoPng = Join-Path $repoRoot "desktop\drivesphere_desktop\assets\images\logo.png"

if (-not (Test-Path $desktopDist)) { throw "dist\DriveSphereDesktop not found." }
if (-not (Test-Path $backendDist)) { throw "dist\DriveSphereBackend not found." }
if (-not (Test-Path $logoPng)) { throw "Logo not found at desktop\drivesphere_desktop\assets\images\logo.png" }

if (Test-Path $stageDir) { Remove-Item -Recurse -Force $stageDir }
New-Item -ItemType Directory -Path $stageDir | Out-Null
New-Item -ItemType Directory -Path $assetsDir | Out-Null

Copy-Item -Recurse -Force $desktopDist (Join-Path $stageDir "DriveSphereDesktop")
Copy-Item -Recurse -Force $backendDist (Join-Path $stageDir "DriveSphereBackend")

Copy-Item -Force $logoPng (Join-Path $assetsDir "StoreLogo.png")
Copy-Item -Force $logoPng (Join-Path $assetsDir "Square44x44Logo.png")
Copy-Item -Force $logoPng (Join-Path $assetsDir "Square150x150Logo.png")
Copy-Item -Force $logoPng (Join-Path $assetsDir "Square310x310Logo.png")
Copy-Item -Force $logoPng (Join-Path $assetsDir "Wide310x150Logo.png")

$manifest = Get-Content $manifestTemplate -Raw
$manifest = $manifest -replace 'Version="1\.0\.0\.0"', "Version=""$Version"""
$manifest = $manifest -replace 'Publisher="CN=Deedarian Software Solutions"', "Publisher=""$Publisher"""
Set-Content -Path $manifestPath -Value $manifest -Encoding UTF8

if (-not (Test-Path (Join-Path $repoRoot $OutputDir))) {
    New-Item -ItemType Directory -Path (Join-Path $repoRoot $OutputDir) -Force | Out-Null
}

$msixPath = Join-Path $repoRoot "$OutputDir\DriveSphereDesktop-$Version.msix"

$makeAppx = (Get-Command makeappx.exe -ErrorAction SilentlyContinue).Source
if (-not $makeAppx) {
    $makeAppx = "C:\Program Files (x86)\Windows Kits\10\bin\x64\makeappx.exe"
}
if (-not (Test-Path $makeAppx)) { throw "makeappx.exe not found. Install Windows 10/11 SDK." }

& $makeAppx pack /d $stageDir /p $msixPath /o

if ($PfxPath) {
    $signTool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
    if (-not $signTool) {
        $signTool = "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
    }
    if (-not (Test-Path $signTool)) { throw "signtool.exe not found. Install Windows SDK signing tools." }
    if (-not (Test-Path $PfxPath)) { throw "PFX file not found: $PfxPath" }
    if (-not $PfxPassword) { throw "Provide -PfxPassword when using -PfxPath." }
    & $signTool sign /fd SHA256 /f $PfxPath /p $PfxPassword $msixPath
}

Write-Host "MSIX created: $msixPath"
if (-not $PfxPath) {
    Write-Host "Note: Package is unsigned. For installation, sign with a trusted certificate."
}
