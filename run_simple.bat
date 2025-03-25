@echo off
echo Running simple llama example...

:: Ensure we're in the correct directory where the module is installed
cd node-llama-project

:: Copy the example file if not already there
if not exist "simple_llama_example.mjs" (
    echo Copying example file to project directory...
    copy ..\simple_llama_example.mjs .
)

echo Running from node-llama-project directory to access local modules...
node simple_llama_example.mjs

echo.
pause
