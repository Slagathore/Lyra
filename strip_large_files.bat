@echo off
setlocal EnableDelayedExpansion

echo ===== Stripping Large Files from Git Repository =====
set maxFileSizeBytes=2147483648
set logFile=strip_large_files_log.txt

:: Initialize log file
echo Stripping Large Files Log > %logFile%
echo Started at %date% %time% >> %logFile%

:: Step 1: Identify large files
echo Identifying files larger than 2GB...
for /r %%F in (*) do (
    if %%~zF GTR %maxFileSizeBytes% (
        echo Found large file: "%%F" (Size: %%~zF bytes) >> %logFile%
        echo Found large file: "%%F" (Size: %%~zF bytes)
        echo Checking if "%%F" is tracked by Git...
        git ls-files --error-unmatch "%%F" >nul 2>&1
        if !errorlevel! equ 0 (
            echo Unstaging "%%F" from Git...
            git reset HEAD "%%F"
            echo Removing "%%F" from Git history...
            git rm --cached "%%F"
            echo Adding to .gitignore...
            for /f "delims=" %%P in ('echo %%F^|findstr /b /l /c:"%CD%"') do (
                set "relPath=%%P"
                set "relPath=!relPath:%CD%\=!"
                echo /!relPath! >> .gitignore
            )
        ) else (
            echo Skipping "%%F" as it is not tracked by Git >> %logFile%
        )
    )
)

:: Step 2: Amend the commit to remove large files
echo Amending the last commit to remove large files...
git commit --amend --no-edit

:: Step 3: Force push changes
echo Force pushing changes to remote repository...
git push origin master --force

echo ===== Process Complete =====
echo Completed at %date% %time% >> %logFile%
echo See %logFile% for details.
pause