@echo off
echo Capturing output to output_log.txt
echo ================================== > output_log.txt
echo Running node_llama_troubleshoot.bat >> output_log.txt
echo ================================== >> output_log.txt
call node_llama_troubleshoot.bat >> output_log.txt 2>&1

echo.
echo Output has been saved to output_log.txt
echo Please share that file content to diagnose what's happening.
pause
