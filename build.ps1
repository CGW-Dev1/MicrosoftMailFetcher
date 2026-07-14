param(
    [switch]$OneFile,
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
    $AppName = -join ([char[]](0x90AE, 0x4EF6, 0x9A8C, 0x8BC1, 0x7801, 0x52A9, 0x624B))
    $SpecPath = Join-Path $PSScriptRoot "$AppName.spec"

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
        "--name", $AppName,
        "--icon", ".\assets\mail.ico"
    )
    if ($OneFile) {
        $PyInstallerArgs += "--onefile"
    } else {
        # Directory mode starts immediately because Qt does not need to be
        # extracted to a temporary folder on every launch.
        $PyInstallerArgs += @("--onedir", "--contents-directory", "runtime")
    }
    $PyInstallerArgs += "app.py"
    python @PyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
    Remove-GeneratedDirectory "build"
    if (Test-Path -LiteralPath $SpecPath) {
        Remove-Item -LiteralPath $SpecPath -Force
    }

    Write-Host ""
    if ($OneFile) {
        Write-Host ("Build complete (single-file): dist\" + $AppName + ".exe")
    } else {
        Write-Host ("Build complete (fast startup): dist\" + $AppName + "\" + $AppName + ".exe")
    }
} finally {
    Set-Location -LiteralPath $OriginalLocation
}
