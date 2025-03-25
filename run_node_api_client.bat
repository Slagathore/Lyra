@echo off
echo Running Node.js API client for oobabooga text-generation-webui
echo.

echo Installing node-fetch if needed...
cd node-llama-project
call npm install node-fetch

echo.
echo Copying API client to project directory...
copy /Y ..\node_api_client.mjs .

echo.
echo Running API client...
echo Make sure the oobabooga text-generation-webui is running with --api flag!
echo.

node node_api_client.mjs

echo.
echo Done!
pause
