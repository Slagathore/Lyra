@echo off
echo Running JSON example with node-llama-cpp...

:: Change to the project directory
cd node-llama-project

:: Copy the JSON example if not already there
if not exist "json_example.mjs" (
    echo Copying JSON example to project directory...
    copy ..\json_example.mjs .
)

echo.
echo Running JSON example...
node json_example.mjs

pause
