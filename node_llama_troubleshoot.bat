@echo off
echo ===== Node-llama-cpp Troubleshooting Script =====
echo.

:: Change to the project directory
cd node-llama-project

:: Check Node.js version
echo Node.js version:
node --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found or not working properly!
    goto end
)

:: Check npm version
echo.
echo npm version:
npm --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm not found or not working properly!
    goto end
)

:: Check package.json
echo.
echo Checking package.json:
if exist "package.json" (
    echo Found package.json
    type package.json | findstr "@llama-node"
) else (
    echo ERROR: package.json not found!
)

:: Check node_modules installation
echo.
echo Checking @llama-node/llama-cpp installation:
if exist "node_modules\@llama-node\llama-cpp" (
    echo Package files found in node_modules
    
    :: List native bindings
    echo.
    echo Checking for native bindings:
    dir /b "node_modules\@llama-node\llama-cpp\dist\binding"
    
    :: Check if binaries are present
    echo.
    echo Looking for compiled binaries:
    dir /s /b "node_modules\@llama-node\llama-cpp\*.node"
) else (
    echo ERROR: @llama-node/llama-cpp not installed properly!
    echo Running npm install with more verbosity:
    call npm install @llama-node/llama-cpp --verbose
)

:: Check model path in the script
echo.
echo Checking model path in test_llama_complete.js:
if exist "test_llama_complete.js" (
    node -e "const fs=require('fs');const content=fs.readFileSync('test_llama_complete.js','utf8');const match=content.match(/modelPath:[^']*'([^']+)'/);if(match){console.log('Path set to: '+match[1]);console.log('File exists: '+fs.existsSync(match[1]));}else{console.log('Model path not found in script');}"
) else (
    echo ERROR: test_llama_complete.js not found!
)

:: Run a minimal test
echo.
echo Running minimal llama-node test:
echo console.log('Testing @llama-node/llama-cpp loading...'); > minimal_test.js
echo try { >> minimal_test.js
echo   const { createLlama } = require('@llama-node/llama-cpp'); >> minimal_test.js
echo   console.log('Package loaded successfully'); >> minimal_test.js
echo   console.log('Available methods:', Object.keys(createLlama)); >> minimal_test.js
echo } catch (error) { >> minimal_test.js
echo   console.error('Error loading package:', error.message); >> minimal_test.js
echo } >> minimal_test.js

node minimal_test.js

echo.
echo ===== Troubleshooting Complete =====
echo.
echo If you're still having issues, try:
echo 1. Reinstalling with 'npm install @llama-node/llama-cpp --build-from-source'
echo 2. Check your Node.js version (should be 16+ for best compatibility)
echo 3. Make sure you have the latest C++ build tools installed

:end
pause
