@echo off
echo Trying factory pattern approach for LLama...

:: Change to the project directory
cd node-llama-project

:: Copy the factory script if not already there
if not exist "factory_approach.mjs" (
    echo Copying factory approach script to project directory...
    copy ..\factory_approach.mjs .
)

:: Run the factory approach
echo.
echo Running factory approach inspection...
node factory_approach.mjs

echo.
pause
