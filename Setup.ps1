param([string]$AppPath,[string]$WorkPath,[switch]$KeepSuggestions,[switch]$PrepareOnly)
$ErrorActionPreference='Stop'
if(-not $AppPath){
    $running=@(Get-Process claude -ErrorAction SilentlyContinue | Where-Object {$_.Path -and $_.Path -match 'WindowsApps\\.*Claude.*\\app\\Claude.exe$'} | ForEach-Object {Split-Path -Parent $_.Path} | Select-Object -Unique)
    if($running.Count -eq 1){$AppPath=$running[0]}else{
        $candidates=@(Get-AppxPackage '*Claude*' | ForEach-Object {Join-Path $_.InstallLocation 'app'} | Where-Object {Test-Path -LiteralPath (Join-Path $_ 'Claude.exe')})
        if($candidates.Count -ne 1){throw 'Cannot choose a unique Claude install. Supply -AppPath pointing to the app directory.'}
        $AppPath=$candidates[0]
    }
}
if(-not $WorkPath){$WorkPath=Join-Path $env:LOCALAPPDATA ('ClaudeZhComplete/jobs/'+(Get-Date -Format 'yyyyMMdd-HHmmss'))}
& (Join-Path $PSScriptRoot 'scripts/Prepare.ps1') -AppPath $AppPath -WorkPath $WorkPath -KeepSuggestions:$KeepSuggestions
if($PrepareOnly){return}
Write-Host 'Prepared. Windows may request administrator approval. This modifies application archives and invalidates the vendor signature. Backup is preserved.'
$apply=Join-Path $PSScriptRoot 'scripts/Apply.ps1'
$arguments='-NoProfile -ExecutionPolicy Bypass -File "'+$apply+'" -WorkPath "'+$WorkPath+'"'
$process=Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -Verb RunAs -WindowStyle Hidden -Wait -PassThru
if($process.ExitCode -ne 0){throw "Apply failed. Backup and manifest: $WorkPath"}
$result=Get-Content -LiteralPath (Join-Path $WorkPath 'manifest.json') -Raw | ConvertFrom-Json
if($result.status -ne 'installed'){throw "Unexpected status $($result.status). See $WorkPath"}
Write-Host "Installed. Restart Claude manually. To restore, run scripts/Apply.ps1 -WorkPath `"$WorkPath`" -Restore as administrator."
