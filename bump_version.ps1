$ErrorActionPreference = "Stop"

$versionPath = Join-Path $PSScriptRoot "VERSION"
$constantsPath = Join-Path $PSScriptRoot "mail_fetcher\constants.py"
$readmePath = Join-Path $PSScriptRoot "README.md"

if (-not (Test-Path $versionPath)) {
    "V1.0" | Set-Content -LiteralPath $versionPath -Encoding UTF8
}

$current = (Get-Content -LiteralPath $versionPath -Raw).Trim()
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
$next | Set-Content -LiteralPath $versionPath -Encoding UTF8

$constantsText = Get-Content -LiteralPath $constantsPath -Raw -Encoding UTF8
$constantsText = [regex]::Replace($constantsText, 'APP_VERSION = "V\d+\.\d+"', "APP_VERSION = `"$next`"")
Set-Content -LiteralPath $constantsPath -Value $constantsText -Encoding UTF8

if (Test-Path $readmePath) {
    $readme = Get-Content -LiteralPath $readmePath -Raw -Encoding UTF8
    if ($readme -match '(?m)^当前版本：V\d+\.\d+\s*$') {
        $readme = [regex]::Replace($readme, '(?m)^当前版本：V\d+\.\d+\s*$', "当前版本：$next")
    } else {
        $lines = $readme -split "`r?`n"
        if ($lines.Count -gt 0) {
            if ($lines.Count -gt 1) {
                $lines = @($lines[0], "当前版本：$next") + $lines[1..($lines.Count - 1)]
            } else {
                $lines = @($lines[0], "当前版本：$next")
            }
            $readme = $lines -join "`r`n"
        } else {
            $readme = "当前版本：$next"
        }
    }
    Set-Content -LiteralPath $readmePath -Value $readme -Encoding UTF8
}

Write-Host "Version bumped: $current -> $next"
