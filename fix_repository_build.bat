@echo off
echo Attempting to fix build issues with node-llama-cpp...

:: Check if build tools are installed
where cl >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Microsoft C++ build tools not found!
    echo Please install Visual Studio Build Tools from:
    echo https://visualstudio.microsoft.com/visual-cpp-build-tools/
    goto end
)

:: Check Node.js version
node -v
echo.
echo This repository may have compatibility issues with Node.js v22.x
echo You might need to downgrade to Node.js v20.x LTS for better compatibility

echo.
echo Attempting to rebuild the repository with debugging enabled...
cd BigModes\node-llama-cpp-master

:: Clean node_modules to ensure a fresh build
echo Cleaning node_modules...
rmdir /S /Q node_modules
rmdir /S /Q dist

:: Install dependencies with detailed logs
echo Installing dependencies...
call npm install --verbose

:: Enable debug logging
set DEBUG=*

:: Set required environment variables
set NODE_OPTIONS=--max-old-space-size=8192

:: Try to build with verbose output
echo Building the repository...
call npm run build -- --verbose

:: Check build result
if %errorlevel% neq 0 (
    echo Build failed. Trying alternative build command...
    if exist "binding.gyp" (
        echo Found binding.gyp, trying node-gyp directly...
        call npx node-gyp rebuild --verbose
    ) else (
        echo No binding.gyp found, this may not be a native module.
    )
)

echo.
echo Build process completed. Check for errors above.
echo If the build succeeded, try running the examples again.

:end
pause
