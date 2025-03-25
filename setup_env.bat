@echo off
echo Setting up compatible environment for llama-cpp-python and PyTorch with CUDA...

:: Create a virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate

:: Install PyTorch with CUDA 11.8 support (compatible with most modern GPUs)
echo Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

:: Check for required build tools
echo Checking for required build tools...
where cmake >nul 2>&1
if %errorlevel% neq 0 (
    echo CMAKE not found! Installing it...
    pip install cmake
)

:: Install llama-cpp-python with CUDA support - with better error handling
echo Installing llama-cpp-python with CUDA support...
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
set FORCE_CMAKE=1
pip install --verbose llama-cpp-python

:: Check if installation was successful
pip show llama-cpp-python >nul 2>&1
if %errorlevel% neq 0 (
    echo First installation attempt failed. Trying alternative approach...
    
    :: Try with specific version that's known to work well with CUDA
    echo Installing llama-cpp-python with specific version...
    pip install llama-cpp-python==0.2.23
    
    :: Check again
    pip show llama-cpp-python >nul 2>&1
    if %errorlevel% neq 0 (
        echo Second installation attempt failed.
        echo Trying pre-built wheels approach...
        
        :: Try with pre-built wheels if compilation fails
        pip install llama-cpp-python --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118
        
        pip show llama-cpp-python >nul 2>&1
        if %errorlevel% neq 0 (
            echo ERROR: Failed to install llama-cpp-python. Please see error messages above.
            goto end
        )
    )
)

echo Verifying installation...
python -c "import llama_cpp; print(f'Successfully installed llama-cpp-python version: {llama_cpp.__version__}')"
if %errorlevel% neq 0 (
    echo ERROR: llama-cpp-python installed but failed to import. Check compatibility issues.
    goto end
)

:: Run the test script to verify the setup
echo Running test script...
python test_llama.py

:end
echo Done!
