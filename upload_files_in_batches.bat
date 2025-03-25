@echo off
echo Starting batch upload process...

:: Add all files
git add .

:: Get count of staged files
for /f "tokens=*" %%a in ('git diff --cached --numstat ^| find /c /v ""') do set total=%%a

echo Found %total% files to commit

:: Commit and push
git commit -m "Batch upload: %total% files"
git push

echo Upload process completed.
pause