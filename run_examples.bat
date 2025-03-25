@echo off
echo Running node-llama-cpp examples...

:: Change to the project directory
cd node-llama-project

echo.
echo === Running basic example ===
node local_example.mjs

echo.
echo === Running advanced examples ===
echo (This may fail if certain features aren't supported by your model)
node advanced_examples.mjs

echo.
echo Examples completed.
pause
