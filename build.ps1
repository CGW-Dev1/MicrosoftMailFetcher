param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

function Remove-GeneratedDirectory([string]$Name) {
    $ProjectRoot = [IO.Path]::GetFullPath($PSScriptRoot)
    $Target = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Name))
    if (-not $Target.StartsWith($ProjectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the project: $Target"
    }
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}

$OriginalLocation = (Get-Location).Path
try {
    Set-Location -LiteralPath $PSScriptRoot
    $AppName = "wrmail"
    $SpecPath = Join-Path $PSScriptRoot "$AppName.spec"
    $VersionInfoPath = Join-Path $PSScriptRoot "packaging\windows_version_info.txt"

    if (-not $SkipInstall) {
        python -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Dependency installation failed with exit code $LASTEXITCODE"
        }
    }
    Remove-GeneratedDirectory "build"
    Remove-GeneratedDirectory "dist"

    $PyInstallerArgs = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--optimize", "1",
        "--noupx",
        "--onedir",
        "--contents-directory", "runtime",
        "--name", $AppName,
        "--icon", ".\assets\mail.ico",
        "--version-file", $VersionInfoPath,
        "app.py"
    )
    python @PyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
    Remove-GeneratedDirectory "build"
    if (Test-Path -LiteralPath $SpecPath) {
        Remove-Item -LiteralPath $SpecPath -Force
    }

    $Architecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    $BundlePath = Join-Path $PSScriptRoot "dist\$AppName"
    $ArchiveName = "$AppName-windows-$Architecture.zip"
    $ArchivePath = Join-Path $PSScriptRoot "dist\$ArchiveName"
    $ChecksumPath = Join-Path $PSScriptRoot "dist\$AppName-windows-$Architecture.sha256"
    Compress-Archive -Path (Join-Path $BundlePath "*") -DestinationPath $ArchivePath -CompressionLevel Optimal
    $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArchivePath).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $ChecksumPath -Value "$Hash  $ArchiveName" -Encoding ascii

    Write-Host ""
    Write-Host ("Build complete: dist\" + $AppName + "\" + $AppName + ".exe")
    Write-Host ("Release archive: dist\" + $ArchiveName)
    Write-Host ("SHA-256: " + $Hash)
} finally {
    Set-Location -LiteralPath $OriginalLocation
}
