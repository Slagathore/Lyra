# Create a file called unstage-large-files.ps1 with this content
$maxSizeMB = 100
$bytesPerMB = 1048576
$maxSizeBytes = $maxSizeMB * $bytesPerMB

Write-Host "Finding staged files larger than $maxSizeMB MB..."

# Get list of staged files
$stagedFiles = git diff --cached --name-only

$removedCount = 0
foreach ($file in $stagedFiles) {
    # Skip if file doesn't exist
    if (-not (Test-Path $file)) { continue }
    
    # Get file size in bytes
    $fileSize = (Get-Item $file).Length
    $fileSizeMB = [math]::Round($fileSize / $bytesPerMB, 2)
    
    # If file is larger than max size, unstage it
    if ($fileSize -gt $maxSizeBytes) {
        Write-Host "Unstaging: $file ($fileSizeMB MB)" -ForegroundColor Yellow
        git reset HEAD "$file"
        $removedCount++
    }
}

Write-Host "Done! Removed $removedCount large files from staging area" -ForegroundColor Green