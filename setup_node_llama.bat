@echo off
echo Setting up node-llama-cpp environment...

:: Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js from https://nodejs.org/
    echo Then run this script again.
    goto end
)

:: Create a new directory for the Node.js project
if not exist "node-llama-project" (
    echo Creating project directory...
    mkdir node-llama-project
)

:: Move into the project directory
cd node-llama-project

:: Initialize a new Node.js project if package.json doesn't exist
if not exist "package.json" (
    echo Initializing Node.js project...
    call npm init -y
)

:: Install node-llama-cpp
echo Installing node-llama-cpp...
call npm install @llama-node/llama-cpp

:: Create a simple test script
echo Creating test script...
echo console.log("Testing node-llama-cpp installation..."); > test_llama.js
echo const { createLlama } = require("@llama-node/llama-cpp"); >> test_llama.js
echo const path = require('path'); >> test_llama.js
echo. >> test_llama.js
echo // Log environment info >> test_llama.js
echo console.log(`Node.js version: ${process.version}`); >> test_llama.js
echo console.log(`Architecture: ${process.arch}`); >> test_llama.js
echo console.log(`Platform: ${process.platform}`); >> test_llama.js
echo console.log(`CUDA available: Check below for GPU methods`); >> test_llama.js
echo. >> test_llama.js
echo // Check if module imported correctly >> test_llama.js
echo console.log("Available methods in createLlama:"); >> test_llama.js
echo console.log(Object.keys(createLlama)); >> test_llama.js
echo. >> test_llama.js

echo Running test script...
call node test_llama.js

echo.
echo Setup complete! Next steps:
echo 1. Download a model file (like 'mistral-7b-instruct-v0.2.Q4_K_M.gguf')
echo 2. Run the example in test_llama_complete.js
echo 3. See the repository at https://github.com/withcatai/node-llama-cpp for more examples

:end
