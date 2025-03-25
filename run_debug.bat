@echo off
echo Running comprehensive debug for node-llama-cpp...
echo Results will be saved to detailed_debug.txt

node debug_node_llama_detailed.js > detailed_debug.txt 2>&1

echo.
echo Debug complete. Please check detailed_debug.txt for results.
echo Opening the file now...

start notepad detailed_debug.txt

pause
