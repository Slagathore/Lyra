@echo off
echo Running direct binding example for node-llama-cpp...

:: Change to the project directory
cd node-llama-project

echo Building a diagnostic file...
echo // Diagnostic for node-llama-cpp-master bindings > diagnostic.mjs
echo import * as llamaModule from 'node-llama-cpp'; >> diagnostic.mjs
echo console.log('Available exports:', Object.keys(llamaModule)); >> diagnostic.mjs
echo if (llamaModule.Llama) { >> diagnostic.mjs
echo   console.log('Llama class found - checking constructor...'); >> diagnostic.mjs
echo   try { >> diagnostic.mjs
echo     const llama = new llamaModule.Llama({ modelPath: '' }); >> diagnostic.mjs
echo     console.log('  Constructor called without error'); >> diagnostic.mjs
echo   } catch (e) { >> diagnostic.mjs
echo     console.log('  Constructor error:', e.message); >> diagnostic.mjs
echo     console.log('  Error type:', e.name); >> diagnostic.mjs
echo   } >> diagnostic.mjs
echo } >> diagnostic.mjs
echo if (llamaModule.getLlama) { >> diagnostic.mjs
echo   console.log('getLlama function found - trying it...'); >> diagnostic.mjs
echo   try { >> diagnostic.mjs
echo     const llama = llamaModule.getLlama(); >> diagnostic.mjs
echo     console.log('  Function returned:', llama); >> diagnostic.mjs
echo   } catch (e) { >> diagnostic.mjs
echo     console.log('  Function error:', e.message); >> diagnostic.mjs
echo   } >> diagnostic.mjs
echo } >> diagnostic.mjs

echo Running diagnostic...
node diagnostic.mjs

echo.
echo Running direct binding example...
node direct_binding_example.mjs

echo.
echo The repository may need to be rebuilt for Node.js v22.14.0.
echo Try downloading a pre-built version that's compatible with your Node.js version.
pause
