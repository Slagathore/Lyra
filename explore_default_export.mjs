/**
 * This script explores the default export of @llama-node/llama-cpp
 */
import llamaExport from '@llama-node/llama-cpp';

console.log('Exploring @llama-node/llama-cpp default export...');

function inspectObject(obj, name = 'default', depth = 0, maxDepth = 2) {
  if (depth > maxDepth) return;
  
  const indent = '  '.repeat(depth);
  console.log(`${indent}${name} (${typeof obj}):`);
  
  if (obj === null || obj === undefined) {
    console.log(`${indent}  ${obj}`);
    return;
  }
  
  if (typeof obj === 'object' && !Array.isArray(obj)) {
    const keys = Object.keys(obj);
    console.log(`${indent}  ${keys.length} properties: ${keys.join(', ')}`);
    
    keys.forEach(key => {
      const value = obj[key];
      if (typeof value === 'function') {
        console.log(`${indent}  ${key}: [Function]`);
      } else if (typeof value === 'object' && value !== null) {
        inspectObject(value, key, depth + 1, maxDepth);
      } else {
        console.log(`${indent}  ${key}: ${value}`);
      }
    });
  } else if (typeof obj === 'function') {
    try {
      console.log(`${indent}  [Function: ${obj.name}]`);
      console.log(`${indent}  Prototype methods:`, 
        Object.getOwnPropertyNames(obj.prototype || {})
          .filter(name => name !== 'constructor')
      );
    } catch (e) {
      console.log(`${indent}  [Function: inspection error]`);
    }
  } else {
    console.log(`${indent}  Value: ${JSON.stringify(obj)}`);
  }
}

// Explore the default export
inspectObject(llamaExport);

// Try to create a model if possible
console.log('\nTrying to use the default export if it looks like a constructor or factory...');
if (typeof llamaExport === 'function') {
  try {
    const instance = llamaExport({
      modelPath: 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf'
    });
    console.log('Successfully created an instance!', instance);
  } catch (error) {
    console.log('Could not create an instance:', error.message);
  }
}
