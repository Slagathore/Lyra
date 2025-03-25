@echo off
echo Exploring the default export of @llama-node/llama-cpp...

:: Change to the project directory
cd node-llama-project

:: Copy the explore file if not already there
if not exist "explore_default_export.mjs" (
    echo Copying explore file to project directory...
    copy ..\explore_default_export.mjs .
)

:: Run the exploration
echo Running exploration...
node explore_default_export.mjs

echo.
pause
