$ErrorActionPreference = "Stop"

$versionPath = Join-Path $PSScriptRoot "VERSION"
$constantsPath = Join-Path $PSScriptRoot "mail_fetcher\constants.py"
$androidConstantsPath = Join-Path $PSScriptRoot "android\app\src\main\java\com\cgwdev\wremail\Constants.java"
$androidGradlePath = Join-Path $PSScriptRoot "android\app\build.gradle"
$windowsVersionInfoPath = Join-Path $PSScriptRoot "packaging\windows_version_info.txt"
$readmePath = Join-Path $PSScriptRoot "README.md"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$versionLabel = -join ([char[]](0x5F53, 0x524D, 0x7248, 0x672C))
$versionLinePrefix = $versionLabel + [char]0xFF1A

if (-not (Test-Path $versionPath)) {
    [IO.File]::WriteAllText($versionPath, "V1.0" + [Environment]::NewLine, $utf8NoBom)
}

$current = [IO.File]::ReadAllText($versionPath, $utf8NoBom).Trim()
if ($current -notmatch '^V(\d+)\.(\d+)$') {
    throw "Invalid VERSION value: $current"
}

$major = [int]$Matches[1]
$minor = [int]$Matches[2]
if ($minor -ge 9) {
    $major += 1
    $minor = 0
} else {
    $minor += 1
}

$next = "V$major.$minor"
[IO.File]::WriteAllText($versionPath, $next + [Environment]::NewLine, $utf8NoBom)

$constantsText = [IO.File]::ReadAllText($constantsPath, $utf8NoBom)
$constantsText = [regex]::Replace($constantsText, 'APP_VERSION = "V\d+\.\d+"', "APP_VERSION = `"$next`"")
[IO.File]::WriteAllText($constantsPath, $constantsText, $utf8NoBom)

if (Test-Path $androidConstantsPath) {
    $androidConstants = [IO.File]::ReadAllText($androidConstantsPath, $utf8NoBom)
    $androidConstants = [regex]::Replace($androidConstants, 'APP_VERSION = "V\d+\.\d+"', "APP_VERSION = `"$next`"")
    [IO.File]::WriteAllText($androidConstantsPath, $androidConstants, $utf8NoBom)
}

if (Test-Path $androidGradlePath) {
    $androidVersionCode = ($major * 10) + $minor
    $androidGradle = [IO.File]::ReadAllText($androidGradlePath, $utf8NoBom)
    $androidGradle = [regex]::Replace($androidGradle, '(?m)^\s*versionCode\s+\d+', "        versionCode $androidVersionCode")
    $androidGradle = [regex]::Replace($androidGradle, '(?m)^\s*versionName\s+"\d+\.\d+"', "        versionName `"$major.$minor`"")
    [IO.File]::WriteAllText($androidGradlePath, $androidGradle, $utf8NoBom)
}

if (Test-Path $windowsVersionInfoPath) {
    $windowsVersionInfo = [IO.File]::ReadAllText($windowsVersionInfoPath, $utf8NoBom)
    $windowsVersionInfo = [regex]::Replace($windowsVersionInfo, '(filevers|prodvers)=\(\d+, \d+, 0, 0\)', "`$1=($major, $minor, 0, 0)")
    $windowsVersionInfo = [regex]::Replace($windowsVersionInfo, "(FileVersion|ProductVersion)', '\d+\.\d+\.0'", "`$1', '$major.$minor.0'")
    [IO.File]::WriteAllText($windowsVersionInfoPath, $windowsVersionInfo, $utf8NoBom)
}

if (Test-Path $readmePath) {
    $readme = [IO.File]::ReadAllText($readmePath, $utf8NoBom)
    $versionPattern = '(?m)^' + [regex]::Escape($versionLinePrefix) + 'V\d+\.\d+\s*$'
    if ($readme -match $versionPattern) {
        $readme = [regex]::Replace($readme, $versionPattern, "$versionLinePrefix$next")
    } else {
        $lines = $readme -split "`r?`n"
        if ($lines.Count -gt 0) {
            if ($lines.Count -gt 1) {
                $lines = @($lines[0], "$versionLinePrefix$next") + $lines[1..($lines.Count - 1)]
            } else {
                $lines = @($lines[0], "$versionLinePrefix$next")
            }
            $readme = $lines -join "`r`n"
        } else {
            $readme = "$versionLinePrefix$next"
        }
    }
    [IO.File]::WriteAllText($readmePath, $readme, $utf8NoBom)
}

Write-Host "Version bumped: $current -> $next"
