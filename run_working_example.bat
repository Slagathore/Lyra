@echo off
echo Running working example for node-llama-cpp...

:: Change to the project directory
cd node-llama-project

:: Copy the example file if not already there
if not exist "working_example.mjs" (
    echo Copying working example to project directory...
    copy ..\working_example.mjs .
)

:: Run the example
echo.
echo Running working example...
node working_example.mjs

echo.
pause
