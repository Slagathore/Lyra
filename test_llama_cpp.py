
Installing CUDA-enabled llama-cpp-python in oobabooga...
print("llama-cpp-python version:", llama_cpp.__version__
print("Module path:", llama_cpp.__file__) 
print("CUDA support available:", any('cuda' in attr.lower() for attr in dir(llama_cpp.Llama))) 
has_cuda = any('cuda' in attr.lower() or 'gpu' in attr.lower() for attr in dir(llama_cpp.Llama)) 
print("✓ CUDA support confirmed!" if has_cuda else "❌ CUDA support not found") 
