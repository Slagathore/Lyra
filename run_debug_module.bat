@echo off
echo Running module inspection for node-llama-cpp...
echo.

:: Change to the project directory
cd node-llama-project

:: Run the debug script
node debug_module_exports.mjs > module_exports_debug.txt

echo.
echo Debug information saved to module_exports_debug.txt
echo Opening file...

start notepad module_exports_debug.txt

pause
