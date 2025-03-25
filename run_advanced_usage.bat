@echo off
echo Checking available modules and capabilities in node-llama-cpp...

:: Change to the project directory
cd node-llama-project

:: Copy the advanced usage file if not already there
if not exist "advanced_usage.mjs" (
    echo Copying advanced usage script to project directory...
    copy ..\advanced_usage.mjs .
)

:: Run the advanced usage script
echo.
echo Running advanced usage script...
node advanced_usage.mjs

echo.
echo For additional features and examples, visit:
echo https://node-llama-cpp.withcat.ai/guide/
pause
