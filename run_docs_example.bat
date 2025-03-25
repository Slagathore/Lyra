@echo off
echo Running official documentation example...

:: Change to the project directory
cd node-llama-project

:: Copy the docs example if not already there
if not exist "docs_example.mjs" (
    echo Copying docs example to project directory...
    copy ..\docs_example.mjs .
)

echo.
echo Running docs example...
node docs_example.mjs

echo.
echo If the example fails, please consider:
echo 1. Downgrading to Node.js v20 LTS (current LTS version)
echo 2. Using a smaller model for initial testing
echo 3. Checking documentation at: https://node-llama-cpp.withcat.ai/guide/

pause
