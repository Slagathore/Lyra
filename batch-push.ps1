# Enhanced batch push with validation and skipped file removal
$batchSize = 50
$batchNumber = 1
$totalPushed = 0
$maxFileSize = 100MB

Write-Host "Starting enhanced batch push process..." -ForegroundColor Cyan
Write-Host "Validating files..." -ForegroundColor Yellow

# First, get all staged files to validate
$allStagedFiles = git diff --cached --name-only
$skippedFiles = @()

# Validate each file
foreach ($file in $allStagedFiles) {
    $skipFile = $false
    $skipReason = ""
    
    # Skip if file doesn't exist (might have been deleted)
    if (-not (Test-Path $file)) { 
        $skipFile = $true
        $skipReason = "file doesn't exist"
    }
    # Check file size
    elseif ((Get-Item $file).Length -gt $maxFileSize) {
        $skipFile = $true
        $skipReason = "file too large ($(([math]::Round((Get-Item $file).Length / 1MB, 2))) MB)"
    }
    # Check if in gitignore (manual check as extra validation)
    elseif (git check-ignore $file) {
        $skipFile = $true 
        $skipReason = "file in gitignore"
    }
    
    if ($skipFile) {
        Write-Host "Removing file from commit: $file - $skipReason" -ForegroundColor Red
        git reset HEAD $file
        $skippedFiles += $file
    }
}

Write-Host "Removed $($skippedFiles.Count) invalid files from staging area" -ForegroundColor Yellow
Write-Host "Starting batch processing..." -ForegroundColor Cyan

while ($true) {
    # Get list of all staged files (excluding previously removed files)
    $stagedFiles = git diff --cached --name-only
    
    # Exit if no more files to push
    if ($stagedFiles.Count -eq 0) {
        Write-Host "No more staged files to push. Process complete." -ForegroundColor Green
        break
    }
    
    # Get the current batch of files
    $currentBatch = $stagedFiles | Select-Object -First $batchSize
    $batchCount = $currentBatch.Count
    
    Write-Host "Committing batch $batchNumber with $batchCount files..." -ForegroundColor Yellow
    
    # Create a separate commit for this batch
    git reset HEAD -- $(git diff --cached --name-only | Select-Object -Skip $batchSize)
    & git commit -m "Batch ${batchNumber}: ${batchCount} files"
    
    Write-Host "Pushing batch $batchNumber..." -ForegroundColor Yellow
    git push
    
    $totalPushed += $batchCount
    $batchNumber++
    
    Write-Host "Pushed $totalPushed files so far in $($batchNumber-1) batches" -ForegroundColor Cyan
    
    # Re-stage any files that were unstaged for the next batch
    git add .
}

if ($skippedFiles.Count -gt 0) {
    Write-Host "`nSkipped Files Summary:" -ForegroundColor Yellow
    foreach ($file in $skippedFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
}

Write-Host "`nProcess complete." -ForegroundColor Green
Write-Host "Pushed $totalPushed files in $($batchNumber-1) batches." -ForegroundColor Green
Write-Host "Skipped $($skippedFiles.Count) files." -ForegroundColor Yellow