@echo off
echo Running minimal LLama example...

:: Change to the project directory
cd node-llama-project

:: Copy the example file if not already there
if not exist "minimal_llama_example.mjs" (
    echo Copying minimal example to project directory...
    copy ..\minimal_llama_example.mjs .
)

:: Run the example
echo.
echo Running minimal example...
node minimal_llama_example.mjs

echo.
echo It appears this module might have compatibility issues with Node.js v22.
echo Consider:
echo 1. Installing Node.js v20 LTS, which is more likely to be compatible
echo 2. Using the Python llama-cpp-python library instead
echo 3. Using LM Studio, which provides a GUI and API for your models
pause
