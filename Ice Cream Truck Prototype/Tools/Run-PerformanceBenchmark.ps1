param([ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Label = 'latest', [switch]$FullHD)

$ErrorActionPreference = 'Stop'
$projectPath = Split-Path $PSScriptRoot -Parent
$repoPath = Split-Path $projectPath -Parent
$lockPath = Join-Path $repoPath '.codex/unity-mcp.lock'
$prepared = $false
$env:UNITY_NON_INTERACTIVE = '1'
$env:UNITY_NO_BANNER = '1'

function Invoke-EditorCommand {
    param([string[]]$Arguments)
    $raw = & unity command @Arguments --json
    if ($LASTEXITCODE -ne 0) { throw ($raw -join "`n") }
    $response = ($raw -join "`n") | ConvertFrom-Json
    if (-not $response.success -or $response.data.result.success -eq $false) {
        throw ($raw -join "`n")
    }
    return $response.data.result
}

Push-Location $projectPath
try {
    & unity status --json
    if ($LASTEXITCODE -ne 0) { throw 'Unity is not connected.' }
    $state = Invoke-EditorCommand -Arguments @('editor_status')
    if ($state.playMode -ne 'stopped') { throw 'Stop Play Mode before running this benchmark.' }
    New-Item -ItemType Directory -Path (Join-Path $repoPath '.codex') -Force | Out-Null
    New-Item -ItemType Directory -Path $lockPath -ErrorAction Stop | Out-Null
    try {
        Set-Content -LiteralPath (Join-Path $lockPath 'owner.txt') -Value ('performance-benchmark ' + [DateTime]::UtcNow.ToString('o'))
        Invoke-EditorCommand -Arguments @('set_autotick', '--enable', 'true') | Out-Null
        Invoke-EditorCommand -Arguments @('run_script', '--file', 'Tools/PerformanceBenchmark.cs', '--entry', 'PerformanceBenchmark.Prepare') | Out-Null
        $prepared = $true
        Invoke-EditorCommand -Arguments @('editor_play') | Out-Null
        $entry = if ($FullHD) { 'PerformanceBenchmark.RunGraphics' } else { 'PerformanceBenchmark.Run' }
        $frames = Invoke-EditorCommand -Arguments @('run_script', '--file', 'Tools/PerformanceBenchmark.cs', '--entry', $entry)
        $navigation = Invoke-EditorCommand -Arguments @('run_script', '--file', 'Tools/NavigationBenchmark.cs', '--entry', 'NavigationBenchmark.Run')
        $errors = Invoke-EditorCommand -Arguments @('get_console_logs', '--severity', 'error')
        if ($errors.total -gt 0) { throw ($errors | ConvertTo-Json -Depth 10) }
        $report = $frames.result + "`n" + $navigation.result
        Set-Content -LiteralPath (Join-Path $projectPath "Library/CodexPlaytests/Performance/$Label.txt") -Value $report
        Write-Output $report
    }
    finally {
        try {
            if ($prepared) {
                Invoke-EditorCommand -Arguments @('editor_stop') | Out-Null
                Invoke-EditorCommand -Arguments @('run_script', '--file', 'Tools/PerformanceBenchmark.cs', '--entry', 'PerformanceBenchmark.Restore') | Out-Null
            }
        }
        finally {
            Remove-Item -LiteralPath (Join-Path $lockPath 'owner.txt')
            Remove-Item -LiteralPath $lockPath
        }
    }
}
finally { Pop-Location }
