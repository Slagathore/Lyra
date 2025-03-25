import path from "path";
import {getLlama, LlamaChatSession} from "node-llama-cpp";

// Define model path
const MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf';

async function main() {
  try {
    console.log("Loading model...");
    // Get the llama interface
    const llama = await getLlama();
    
    // Load the model
    console.log(`Loading model from: ${MODEL_PATH}`);
    const model = await llama.loadModel({
      modelPath: MODEL_PATH,
      // Optional GPU settings - remove if causing issues
      gpuLayers: -1  // Use all available GPU memory
    });
    
    console.log("Creating context...");
    const context = await model.createContext();
    
    // Create a chat session
    const session = new LlamaChatSession({
      contextSequence: context.getSequence()
    });
    
    // First prompt
    const question1 = "Hi there, who are you? Please introduce yourself.";
    console.log("\nUser: " + question1);
    
    console.log("AI: ");
    const answer1 = await session.prompt(question1, {
      onToken: (token) => process.stdout.write(token)
    });
    console.log("\n");
    
    // Follow-up question
    const question2 = "Can you write a short poem about artificial intelligence?";
    console.log("\nUser: " + question2);
    
    console.log("AI: ");
    const answer2 = await session.prompt(question2, {
      onToken: (token) => process.stdout.write(token)
    });
    console.log("\n");
    
    console.log("Chat session completed successfully!");
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
