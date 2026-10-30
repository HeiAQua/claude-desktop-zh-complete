param(
    [Parameter(Mandatory=$true)][string]$AppPath,
    [Parameter(Mandatory=$true)][string]$WorkPath,
    [switch]$KeepSuggestions
)
$ErrorActionPreference='Stop'
$project=Split-Path -Parent $PSScriptRoot
$app=(Resolve-Path -LiteralPath $AppPath).Path
$version=(Get-Item -LiteralPath (Join-Path $app 'Claude.exe')).VersionInfo.FileVersion
if($version -notmatch '^4\.4212\.0(?:\.0)?$'){throw "Untested Claude version: $version. See docs/COMPATIBILITY.md; refusing to modify the installation."}
if(Test-Path -LiteralPath $WorkPath){throw 'WorkPath must be a NEW directory'}
$null=Get-Command python -ErrorAction Stop
& python -c 'import sys; assert sys.version_info >= (3,10)'
if($LASTEXITCODE -ne 0){throw 'Python 3.10+ is required'}
New-Item -ItemType Directory -Path (Join-Path $WorkPath 'stage/resources'),(Join-Path $WorkPath 'original/resources') -Force | Out-Null
$job=(Resolve-Path -LiteralPath $WorkPath).Path
$stage=Join-Path $job 'stage'
$original=Join-Path $job 'original'
$manifest=[ordered]@{schema=1;appPath=$app;version=$version;created=(Get-Date -Format o);files=@();status='preparing'}
foreach($relative in @('Claude.exe','resources/app.asar','resources/ion-dist.asar','resources/zh-CN.json')){
    $source=Join-Path $app $relative
    $exists=Test-Path -LiteralPath $source -PathType Leaf
    if(-not $exists -and $relative -ne 'resources/zh-CN.json'){throw "Missing file: $relative"}
    $hash=$null
    if($exists){
        Copy-Item -LiteralPath $source -Destination (Join-Path $original $relative)
        $hash=(Get-FileHash -LiteralPath (Join-Path $original $relative)).Hash
        if((Get-FileHash -LiteralPath $source).Hash -ne $hash){throw 'App changed during backup'}
    }
    if($relative -ne 'resources/zh-CN.json'){Copy-Item -LiteralPath $source -Destination (Join-Path $stage $relative)}
    $manifest.files+=@{path=$relative;existed=$exists;originalHash=$hash;patchedHash=$null}
}
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $job 'manifest.json') -Encoding UTF8
. (Join-Path $project 'vendor/upstream/scripts/library.ps1')
$resources=Join-Path $stage 'resources'
$target=Initialize-FrontendPatchTarget $resources
Install-LanguageFiles $resources (Get-LanguageResources 'zh-CN') 'zh-CN'
Register-Language $resources 'zh-CN'
Patch-HardcodedFrontendStrings $resources 'zh-CN'
Patch-SlashCommandMenu $resources 'zh-CN'
Patch-LanguageDisplayNames $resources
$pythonArgs=@((Join-Path $PSScriptRoot 'supplement.py'),'--resources',$resources)
if($KeepSuggestions){$pythonArgs+='--keep-suggestions'}
& python @pythonArgs
if($LASTEXITCODE -ne 0){throw 'Supplement failed; installed application has NOT been modified'}
Complete-FrontendPatchTarget $target
Sync-ClaudeExeAsarIntegrity $resources
foreach($entry in $manifest.files){$entry.patchedHash=(Get-FileHash -LiteralPath (Join-Path $stage $entry.path)).Hash}
$manifest.status='prepared'
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $job 'manifest.json') -Encoding UTF8
Write-Host "PREPARED: $job"
