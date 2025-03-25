# PowerShell script to remove large files from Git tracking
$maxFileSizeBytes = 2147483648  # 2GB in bytes
$largeFiles = Get-ChildItem -Recurse | Where-Object { $_.Length -gt $maxFileSizeBytes }

foreach ($file in $largeFiles) {
    Write-Host "Processing large file: $($file.FullName) - $([math]::Round($file.Length / 1MB, 2)) MB"

    # Remove from Git tracking if tracked
    if (git ls-files --error-unmatch $file.FullName 2>$null) {
        Write-Host "Removing $($file.FullName) from Git tracking..."
        git rm --cached "$($file.FullName)"
    }

    # Add to .gitignore
    Write-Host "Adding $($file.FullName) to .gitignore..."
    Add-Content -Path ".gitignore" -Value "`n$($file.FullName)"
}

Write-Host "Large files have been removed from tracking and added to .gitignore."