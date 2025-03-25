@echo off
echo Running locally installed node-llama-cpp...

:: Change to the project directory
cd node-llama-project

:: Check if local example exists
if not exist "local_example.mjs" (
    echo ERROR: local_example.mjs not found!
    if exist "local_example.js" (
        echo Found local_example.js - converting to .mjs format
        copy local_example.js local_example.mjs
    ) else (
        echo Run install_local_node_llama.bat first.
        goto end
    )
)

:: Run the example with ES modules
echo Running the local example with ES modules...
node local_example.mjs

:end
pause
