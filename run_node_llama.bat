@echo off
echo Running node-llama-cpp with your model...

:: Change to the project directory
cd node-llama-project

:: Verify installation
echo Checking if node-llama-cpp is installed correctly...
if not exist "node_modules\@llama-node\llama-cpp" (
    echo ERROR: @llama-node/llama-cpp not found in node_modules.
    echo Running npm install to fix this...
    call npm install @llama-node/llama-cpp
    
    if not exist "node_modules\@llama-node\llama-cpp" (
        echo Installation failed. Please try:
        echo 1. Run 'npm init -y' to create a fresh package.json
        echo 2. Run 'npm install @llama-node/llama-cpp'
        echo 3. Run this batch file again
        goto end
    )
)

:: Check for model file in CONFIG
echo Checking model path...
node -e "const fs=require('fs');const path=require('path');try{const content=fs.readFileSync('test_llama_complete.js','utf8');const match=content.match(/modelPath:[^']*'([^']+)'/);if(match&&fs.existsSync(match[1])){console.log('Model file found at: '+match[1])}else{console.log('WARNING: Model file not found at path specified in test_llama_complete.js')}}catch(e){console.error('Error:',e.message)}"

:: You can set the model path here or edit it directly in the JavaScript file
:: set MODEL_PATH=G:\AI\path\to\your\model.gguf

echo.
echo Running the model...
node test_llama_complete.js
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo There seems to be an issue. Checking common problems...
    
    echo 1. Checking if package.json exists with proper dependencies...
    if not exist "package.json" (
        echo ERROR: package.json not found
    ) else (
        node -e "const fs=require('fs');const pkg=JSON.parse(fs.readFileSync('package.json'));console.log('@llama-node/llama-cpp version: '+(pkg.dependencies&&pkg.dependencies['@llama-node/llama-cpp']||'Not found in dependencies'))"
    )
    
    echo.
    echo 2. Checking if test_llama_complete.js exists...
    if not exist "test_llama_complete.js" (
        echo ERROR: test_llama_complete.js not found
        echo Try running setup_node_llama.bat again
    )
    
    echo.
    echo If problems persist, you might need to:
    echo 1. Clone the repository from https://github.com/withcatai/node-llama-cpp.git
    echo 2. Follow the installation instructions in the repository
    echo 3. Copy the examples into your project
)

:end
pause
