@echo off
echo Running Qwen2.5 model with node-llama-cpp...
echo.

:: Create a project directory if it doesn't exist
if not exist "node-llama-project" (
    mkdir node-llama-project
    cd node-llama-project
    echo Initializing new project...
    call npm init -y
    echo Installing node-llama-cpp...
    call npm install node-llama-cpp
    :: Set project to use ES modules
    node -e "const fs=require('fs');const pkg=JSON.parse(fs.readFileSync('package.json'));pkg.type='module';fs.writeFileSync('package.json',JSON.stringify(pkg,null,2));"
    cd ..
) else (
    echo Project directory already exists.
)

:: Copy example file
echo Copying example file to project directory...
copy /Y run_qwen.mjs node-llama-project\

:: Run the example
cd node-llama-project
echo.
echo Running example...
node run_qwen.mjs

pause
