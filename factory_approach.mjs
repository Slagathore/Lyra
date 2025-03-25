/**
 * This example tries using the factory pattern approach with LLama
 */
import llamaModule from '@llama-node/llama-cpp';
import util from 'util';

const MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf';

async function inspectLLama() {
  const { LLama, InferenceResultType } = llamaModule;
  
  console.log('=== Deep inspection of LLama object ===');
  console.log('Type:', typeof LLama);
  
  // More detailed inspection
  console.log('\nDetailed inspection:');
  console.log(util.inspect(LLama, { depth: 2, showHidden: true }));
  
  // Check properties and prototype
  if (typeof LLama === 'object') {
    console.log('\nProperties:', Object.keys(LLama));
    console.log('Own property names:', Object.getOwnPropertyNames(LLama));
    console.log('Prototype methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(LLama) || {}));
    
    // Try to find a way to create an instance
    console.log('\nLooking for factory methods...');
    const factoryMethodNames = ['create', 'getInstance', 'new', 'init', 'createInstance', 'build'];
    for (const name of factoryMethodNames) {
      if (typeof LLama[name] === 'function') {
        console.log(`Found potential factory method: ${name}`);
      }
    }
  }
  
  // Check if there's a static method that returns a Promise
  const promiseReturningMethods = [];
  for (const key of Object.keys(LLama)) {
    if (typeof LLama[key] === 'function') {
      try {
        const result = LLama[key]();
        if (result instanceof Promise) {
          promiseReturningMethods.push(key);
        }
      } catch (e) {
        // Ignore errors when calling without arguments
      }
    }
  }
  
  if (promiseReturningMethods.length > 0) {
    console.log('\nFound methods that return Promises:', promiseReturningMethods);
  }
}

async function main() {
  try {
    await inspectLLama();
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
