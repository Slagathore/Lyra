@echo off
echo Installing local node-llama-cpp repository...

:: Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js from https://nodejs.org/
    echo Then run this script again.
    goto end
)

:: Ensure we have a project directory
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

:: Update package.json to support ES modules
echo Updating package.json to support ES modules...
node -e "const fs=require('fs');const pkg=JSON.parse(fs.readFileSync('package.json'));pkg.type='module';fs.writeFileSync('package.json',JSON.stringify(pkg,null,2));"

:: Check if local repository exists
if not exist "..\BigModes\node-llama-cpp-master" (
    echo ERROR: Local repository not found at G:\AI\Lyra\BigModes\node-llama-cpp-master
    echo Please make sure you've cloned the repository correctly.
    goto end
)

:: First, build the local repository
echo Building local node-llama-cpp repository...
cd ..\BigModes\node-llama-cpp-master

:: Install repository dependencies
echo Installing repository dependencies...
call npm install

:: Build the project if needed
if exist "package.json" (
    type package.json | findstr "\"build\"" >nul
    if not errorlevel 1 (
        echo Building the repository...
        call npm run build
    )
)

:: Return to the project directory
cd ..\..\node-llama-project

:: Remove existing installation if present
if exist "node_modules\node-llama-cpp" (
    echo Removing existing node-llama-cpp installation...
    rmdir /S /Q "node_modules\node-llama-cpp"
)

:: Install the local package
echo Installing local package...
call npm install ..\BigModes\node-llama-cpp-master

echo.
echo Creating simple test to verify installation in ESM format...
echo // Testing local node-llama-cpp installation > test_local_llama.mjs
echo import * as llamaModule from 'node-llama-cpp'; >> test_local_llama.mjs
echo try { >> test_local_llama.mjs
echo   console.log('Module loaded successfully!'); >> test_local_llama.mjs
echo   console.log('Available exports:', Object.keys(llamaModule)); >> test_local_llama.mjs
echo   if (llamaModule.createCompletion) { >> test_local_llama.mjs
echo     console.log('createCompletion function found!'); >> test_local_llama.mjs
echo   } else if (llamaModule.default && llamaModule.default.createCompletion) { >> test_local_llama.mjs
echo     console.log('createCompletion function found in default export!'); >> test_local_llama.mjs
echo   } >> test_local_llama.mjs
echo } catch (error) { >> test_local_llama.mjs
echo   console.error('Error loading local module:', error.message); >> test_local_llama.mjs
echo } >> test_local_llama.mjs

echo.
echo Running test to verify local installation...
call node test_local_llama.mjs

echo.
echo Creating ESM example file...
call node -e "const fs=require('fs');fs.writeFileSync('local_example.mjs', fs.readFileSync('../local_example.mjs', 'utf8'));"

echo.
echo Installation complete! Now you can run the example with:
echo node local_example.mjs

:end
pause
