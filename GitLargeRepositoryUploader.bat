@echo off
setlocal EnableDelayedExpansion

echo ===== Git Large Repository Uploader =====
echo Will upload in batches of 5000 files

:: Set batch size
set /a batchSize=5000
set /a maxFileSizeMB=100

:: Track current batch number and total files uploaded
set /a batchNumber=1
set /a totalUploaded=0

:: Make sure we're using the right remote branch
set remoteBranch=master

echo ===== FIXING GITIGNORE ISSUES =====
echo Creating proper .gitignore file...

:: Create a new gitignore file properly without corruption
echo # Python > new_gitignore.txt
echo __pycache__/ >> new_gitignore.txt
echo *.py[cod] >> new_gitignore.txt
echo # BigModes directory - completely excluded >> new_gitignore.txt
echo BigModes/ >> new_gitignore.txt
echo BigModes/* >> new_gitignore.txt
echo BigModes/**/* >> new_gitignore.txt
echo # Skip large files ^(^>100MB^) >> new_gitignore.txt
echo *.gguf >> new_gitignore.txt
echo *.bin >> new_gitignore.txt
echo *.pth >> new_gitignore.txt
echo *.safetensors >> new_gitignore.txt

:: Replace the old gitignore with the new one
copy /Y new_gitignore.txt .gitignore
del new_gitignore.txt

echo.
echo ===== SKIPPING PROBLEMATIC BIGMODES REMOVAL =====
echo Will filter out BigModes files during processing instead...

echo.
echo ===== STARTING UPLOAD PROCESS =====

echo Git Large Repository Uploader Log > upload_log.txt
echo Started at %date% %time% >> upload_log.txt

:upload_batch
echo.
echo Processing batch !batchNumber!...

:: Find files while excluding BigModes directory
echo Finding files to add (excluding BigModes)...
git ls-files --others --exclude-standard --modified | findstr /v /i "BigModes" > batch_files.txt

:: Count total files to process
set /a totalFiles=0
for /f %%A in (batch_files.txt) do set /a totalFiles+=1

echo Found !totalFiles! files to process in this batch.

:: If no files, we're done
if !totalFiles! equ 0 (
    echo No more files to upload.
    del batch_files.txt 2>nul
    goto finish
)

:: Count how many files we've added in this batch
set /a fileCount=0
set /a fileErrors=0

:: Process files in this batch
for /f "tokens=*" %%F in (batch_files.txt) do (
    if !fileCount! lss %batchSize% (
        :: Skip large files
        for %%S in ("%%F") do set size=%%~zS
        set /a sizeMB=!size! / 1048576
        
        if !sizeMB! lss %maxFileSizeMB% (
            git add "%%F" 2>nul
            if !errorlevel! equ 0 (
                set /a fileCount+=1
                set /a totalUploaded+=1
                
                :: Show progress every 100 files
                set /a mod=!fileCount! %% 100
                if !mod! equ 0 echo Added !fileCount! files...
            ) else (
                echo ERROR: Failed to add %%F
                set /a fileErrors+=1
            )
        ) else (
            echo Skipping large file: %%F ^(!sizeMB! MB^)
        )
    ) else (
        goto commit_batch
    )
)

:commit_batch
:: Only commit if we added files
if !fileCount! gtr 0 (
    echo.
    echo Committing batch !batchNumber! with !fileCount! files...
    
    git commit -m "Batch upload !batchNumber!: !fileCount! files" 
    if !errorlevel! neq 0 (
        echo Commit failed. Trying smaller batch...
        git reset HEAD
        set /a batchSize=!batchSize!/2
        if !batchSize! lss 100 set /a batchSize=100
        echo Reduced batch size to !batchSize!
        goto upload_batch
    )
    
    echo Pushing batch !batchNumber!...
    git push origin %remoteBranch%
    if !errorlevel! neq 0 (
        echo Push failed. Trying smaller batch...
        git reset --soft HEAD~1
        set /a batchSize=!batchSize!/2
        if !batchSize! lss 100 set /a batchSize=100
        echo Reduced batch size to !batchSize!
        goto upload_batch
    )
    
    echo Successfully pushed batch !batchNumber!
    set /a batchNumber+=1
    del batch_files.txt 2>nul
    goto upload_batch
) else (
    echo No files added in this batch.
)

:finish
echo.
echo ===== Upload Process Summary =====
echo Total batches processed: !batchNumber!
echo Total files uploaded: !totalUploaded!
echo Files with errors: !fileErrors!
echo.
echo Upload process completed.
pause
