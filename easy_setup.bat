@echo off
echo Setting up an easy way to use your model with node-llama-cpp...
echo This script will help you set up the environment based on official documentation.

:: Create project directory if needed
if not exist "node-llama-project" (
    mkdir node-llama-project
)

cd node-llama-project

:: Initialize package if needed
if not exist "package.json" (
    echo Initializing npm package...
    call npm init -y
)

:: Set up package.json to use ESM
node -e "const fs=require('fs');const pkg=JSON.parse(fs.readFileSync('package.json'));pkg.type='module';fs.writeFileSync('package.json',JSON.stringify(pkg,null,2));"

:: Install the module
echo Installing node-llama-cpp...
call npm install node-llama-cpp

:: Create an example based on official documentation
echo Creating example based on official documentation...

echo // Based on official node-llama-cpp documentation > docs_example.mjs
echo import { LlamaModel, LlamaContext, LlamaTokenType } from "node-llama-cpp"; >> docs_example.mjs
echo. >> docs_example.mjs
echo const MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf'; >> docs_example.mjs
echo. >> docs_example.mjs
echo async function main() { >> docs_example.mjs
echo   console.log('Loading model from documentation example...'); >> docs_example.mjs
echo   const model = new LlamaModel({ >> docs_example.mjs
echo     modelPath: MODEL_PATH, >> docs_example.mjs
echo     threads: 4, >> docs_example.mjs
echo     contextSize: 4096 >> docs_example.mjs
echo   }); >> docs_example.mjs
echo. >> docs_example.mjs
echo   const context = new LlamaContext({ model }); >> docs_example.mjs
echo   const prompt = "Write a short poem about artificial intelligence:"; >> docs_example.mjs
echo. >> docs_example.mjs
echo   console.log(`Generating completion for prompt: ${prompt}`); >> docs_example.mjs
echo   const completion = await context.completion({ >> docs_example.mjs
echo     prompt, >> docs_example.mjs
echo     maxTokens: 128, >> docs_example.mjs
echo     temperature: 0.7, >> docs_example.mjs
echo     topP: 0.95, >> docs_example.mjs
echo     stream: true, >> docs_example.mjs
echo   }); >> docs_example.mjs
echo. >> docs_example.mjs
echo   let resultText = ""; >> docs_example.mjs
echo   for await (const chunk of completion) { >> docs_example.mjs
echo     process.stdout.write(chunk.token); >> docs_example.mjs
echo     resultText += chunk.token; >> docs_example.mjs
echo   } >> docs_example.mjs
echo. >> docs_example.mjs
echo   console.log("\nFull text generated:", resultText); >> docs_example.mjs
echo } >> docs_example.mjs
echo. >> docs_example.mjs
echo main().catch(console.error); >> docs_example.mjs

echo.
echo Example script created from documentation!
echo To run it, use: node docs_example.mjs

echo.
echo NOTE: If you encounter errors, you might need to:
echo 1. Downgrade Node.js to v20 LTS for better compatibility
echo 2. Consult the documentation at: https://node-llama-cpp.withcat.ai/guide/
echo 3. Try a smaller model to test functionality

pause
