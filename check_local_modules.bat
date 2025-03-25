@echo off
echo Checking Node.js modules in node-llama-project...

cd node-llama-project

echo Installed packages (from package.json):
node -e "const fs=require('fs'); try { const pkg=JSON.parse(fs.readFileSync('package.json')); console.log(pkg.dependencies || 'No dependencies found'); } catch(e) { console.error('Error reading package.json:', e.message); }"

echo.
echo Actual module directories:
dir /b node_modules 2>nul || echo No node_modules directory found!

echo.
echo Checking for @llama-node directory:
if exist "node_modules\@llama-node" (
    dir /b "node_modules\@llama-node"
    echo.
    echo Checking for llama-cpp:
    dir /b "node_modules\@llama-node\llama-cpp" 2>nul || echo Not found!
) else (
    echo @llama-node directory not found!
)

echo.
echo Checking for node-llama-cpp directory:
if exist "node_modules\node-llama-cpp" (
    dir /b "node_modules\node-llama-cpp"
) else (
    echo node-llama-cpp directory not found!
)

echo.
echo Installing @llama-node/llama-cpp just to be sure...
call npm install @llama-node/llama-cpp

echo.
pause
