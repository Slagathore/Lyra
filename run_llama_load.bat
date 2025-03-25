@echo off
echo Running LLama.load factory example...

:: Change to the project directory
cd node-llama-project

:: Copy the example file if not already there
if not exist "llama_load_example.mjs" (
    echo Copying LLama.load example to project directory...
    copy ..\llama_load_example.mjs .
)

:: Run the example
echo.
echo Running LLama.load example...
node llama_load_example.mjs

echo.
pause
