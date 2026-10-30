param([Parameter(Mandatory=$true)][string]$WorkPath,[switch]$Restore)
$ErrorActionPreference='Stop'
$job=(Resolve-Path -LiteralPath $WorkPath).Path
$manifestPath=Join-Path $job 'manifest.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$app=$manifest.appPath
$admin=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $admin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run this script in an elevated PowerShell; see README.md'}
if($manifest.status -notin @('prepared','installed','failed')){throw 'Invalid job status'}
if((Get-Item -LiteralPath (Join-Path $app 'Claude.exe')).VersionInfo.FileVersion -ne $manifest.version){throw 'Claude was updated. Refusing to restore/apply across versions.'}
foreach($entry in $manifest.files){
    $sourceRoot=if($Restore){'original'}else{'stage'}
    if($Restore -and -not $entry.existed){continue}
    $source=Join-Path (Join-Path $job $sourceRoot) $entry.path
    $expected=if($Restore){$entry.originalHash}else{$entry.patchedHash}
    if((Get-FileHash -LiteralPath $source).Hash -ne $expected){throw "Backup/stage hash mismatch: $($entry.path)"}
    $destination=Join-Path $app $entry.path
    if(Test-Path -LiteralPath $destination){
        $current=(Get-FileHash -LiteralPath $destination).Hash
        if($current -ne $entry.originalHash -and $current -ne $entry.patchedHash){throw "App changed since preparation: $($entry.path)"}
    }elseif($entry.existed){throw "App file vanished: $($entry.path)"}
}
# Only processes whose executable lives directly in the chosen app directory.
Get-Process -Name claude -ErrorAction SilentlyContinue | Where-Object { $_.Path -and (Split-Path -Parent $_.Path) -eq $app } | Stop-Process -Force
$aclSaved=@()
$written=@()
try{
    $paths=@($app,(Join-Path $app 'resources'))
    $paths+=@($manifest.files | ForEach-Object {Join-Path $app $_.path} | Where-Object {Test-Path -LiteralPath $_})
    foreach($path in $paths){
        $acl=Get-Acl -LiteralPath $path
        $aclSaved+=@{path=$path;acl=$acl}
        $newAcl=Get-Acl -LiteralPath $path
        $rule=[Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.WindowsIdentity]::GetCurrent().Name,'FullControl','Allow')
        $newAcl.SetAccessRule($rule)
        Set-Acl -LiteralPath $path -AclObject $newAcl -ErrorAction Stop
    }
    foreach($entry in $manifest.files){
        $destination=Join-Path $app $entry.path
        $written+=$entry
        if($Restore -and -not $entry.existed){
            # Exact file created by this job, already hash-checked above.
            if(Test-Path -LiteralPath $destination){Remove-Item -LiteralPath $destination -Force}
        }else{
            Copy-Item -LiteralPath (Join-Path (Join-Path $job $sourceRoot) $entry.path) -Destination $destination -Force
            $expected=if($Restore){$entry.originalHash}else{$entry.patchedHash}
            if((Get-FileHash -LiteralPath $destination).Hash -ne $expected){throw 'Post-copy verification failed'}
        }
    }
    $manifest.status=if($Restore){'restored'}else{'installed'}
}catch{
    $failure=$_
    if(-not $Restore){
        foreach($entry in $written){
            $destination=Join-Path $app $entry.path
            if($entry.existed){Copy-Item -LiteralPath (Join-Path (Join-Path $job 'original') $entry.path) -Destination $destination -Force}
            elseif(Test-Path -LiteralPath $destination){Remove-Item -LiteralPath $destination -Force}
        }
    }
    $manifest.status='failed'
    throw $failure
}finally{
    $aclErrors=@()
    foreach($saved in $aclSaved){try{Set-Acl -LiteralPath $saved.path -AclObject $saved.acl -ErrorAction Stop}catch{$aclErrors+=$_.Exception.Message}}
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    if($aclErrors.Count){throw ('Permission restoration needs attention: '+($aclErrors -join '; '))}
}
Write-Host $manifest.status
