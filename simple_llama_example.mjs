/**
 * Simple example focusing just on the getLlama functionality
 * Make sure to run this from the node-llama-project directory
 */
import * as llamaModule from '@llama-node/llama-cpp';

const MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf';

async function main() {
  console.log('Starting simple llama example...');
  console.log('Available exports:', Object.keys(llamaModule));
  
  try {
    // Check if getLlama exists
    if (typeof llamaModule.getLlama === 'function') {
      console.log('Found getLlama function, awaiting result...');
      const llama = await llamaModule.getLlama();
      console.log('llama instance:', llama);
      console.log('llama methods:', Object.keys(llama));
      
      // Try the Llama class if it exists
      if (llamaModule.Llama) {
        console.log('\nFound Llama class, creating instance...');
        const llamaInstance = new llamaModule.Llama({
          modelPath: MODEL_PATH
        });
        console.log('Llama instance created, methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(llamaInstance)));
      }
    }
    
  } catch (error) {
    console.error('Error:', error);
  }
}

main().catch(console.error);
