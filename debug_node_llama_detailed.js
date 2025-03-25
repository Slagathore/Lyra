// Comprehensive debug script for node-llama-cpp issues

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Log system info
console.log('=== SYSTEM INFORMATION ===');
console.log(`OS: ${os.platform()} ${os.release()} (${os.arch()})`);
console.log(`Node.js version: ${process.version}`);
console.log(`CPU: ${os.cpus()[0].model} x ${os.cpus().length}`);
console.log(`Memory: ${Math.round(os.totalmem() / (1024 * 1024 * 1024))} GB`);
console.log(`Free memory: ${Math.round(os.freemem() / (1024 * 1024 * 1024))} GB`);

// Check GPU info on Windows
if (os.platform() === 'win32') {
  try {
    console.log('\n=== GPU INFORMATION ===');
    const gpuInfo = execSync('nvidia-smi', { encoding: 'utf8' });
    console.log(gpuInfo);
  } catch (e) {
    console.log('NVIDIA GPU information not available');
    console.log('Make sure NVIDIA drivers are installed if you have an NVIDIA GPU');
  }
}

// Package inspection
console.log('\n=== PACKAGE INSPECTION ===');
const projectDir = path.join(__dirname, 'node-llama-project');
const packageJsonPath = path.join(projectDir, 'package.json');

if (!fs.existsSync(projectDir)) {
  console.error(`Project directory not found: ${projectDir}`);
  process.exit(1);
}

if (!fs.existsSync(packageJsonPath)) {
  console.error(`package.json not found in: ${projectDir}`);
} else {
  const packageJson = require(packageJsonPath);
  console.log('Package dependencies:', packageJson.dependencies || 'None');
}

// Check for the module
const modulePath = path.join(projectDir, 'node_modules', '@llama-node', 'llama-cpp');
if (!fs.existsSync(modulePath)) {
  console.error('\nERROR: @llama-node/llama-cpp package not installed');
  console.log('Try reinstalling with: npm install @llama-node/llama-cpp');
  process.exit(1);
}

// Check native bindings
console.log('\n=== NATIVE MODULE BINDINGS ===');
const bindingPath = path.join(modulePath, 'dist', 'binding');
if (fs.existsSync(bindingPath)) {
  const files = fs.readdirSync(bindingPath);
  console.log('Binding files:', files);
  
  // Check for .node files which contain the native code
  const nodeFiles = files.filter(f => f.endsWith('.node'));
  if (nodeFiles.length === 0) {
    console.error('No .node binary files found! Native bindings may be missing.');
  } else {
    console.log('Native bindings found:', nodeFiles);
  }
} else {
  console.error('Binding directory not found!');
}

// Try to load the module
console.log('\n=== MODULE LOADING TEST ===');
try {
  const llamaNode = require('@llama-node/llama-cpp');
  console.log('Module successfully loaded!');
  console.log('Available exports:', Object.keys(llamaNode));
  
  if (llamaNode.createLlama) {
    console.log('createLlama function found, checking available methods:');
    console.log(Object.keys(llamaNode.createLlama));
    console.log('\nGPU support methods:', 
      Object.keys(llamaNode.createLlama).filter(k => k.toLowerCase().includes('gpu')));
  } else {
    console.error('ERROR: createLlama function not found in the module');
  }
} catch (error) {
  console.error('ERROR loading module:', error.message);
  console.error(error.stack);
  
  if (error.message.includes('node_modules/@llama-node/llama-cpp')) {
    console.log('\nThis looks like a native module binding issue!');
    console.log('Possible causes:');
    console.log('1. Missing C++ build tools - install Visual Studio Build Tools');
    console.log('2. Node.js version mismatch - the binding might be built for a different Node.js version');
    console.log('3. Architecture mismatch - make sure you\'re using a 64-bit Node.js');
  }
}

// Model checking
console.log('\n=== MODEL FILE CHECK ===');
const testFilePath = path.join(projectDir, 'test_llama_complete.js');
if (fs.existsSync(testFilePath)) {
  const content = fs.readFileSync(testFilePath, 'utf8');
  const modelPathMatch = content.match(/modelPath:[^']*'([^']+)'/);
  if (modelPathMatch) {
    const modelPath = modelPathMatch[1];
    console.log('Model path from script:', modelPath);
    
    if (fs.existsSync(modelPath)) {
      console.log('✓ Model file exists');
      const stats = fs.statSync(modelPath);
      console.log(`Model size: ${(stats.size / (1024 * 1024)).toFixed(2)} MB`);
    } else {
      console.error('✗ Model file NOT FOUND at path:', modelPath);
    }
  } else {
    console.error('Could not extract model path from test script');
  }
} else {
  console.error('Test file not found:', testFilePath);
}

console.log('\n=== RECOMMENDATIONS ===');
console.log('If you\'re having issues:');
console.log('1. Try installing with: npm install @llama-node/llama-cpp@latest --build-from-source');
console.log('2. Make sure you have Visual Studio Build Tools installed (for Windows)');
console.log('3. Check if your model file exists and is accessible');
console.log('4. Consider using a smaller model for initial testing');

console.log('\n=== END OF DIAGNOSTIC INFO ===');
