import { getLlama, LlamaChatSession, LlamaJsonSchemaGrammar } from "node-llama-cpp";

// Model path
const MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf';

async function main() {
  try {
    console.log("Loading model...");
    const llama = await getLlama();
    
    const model = await llama.loadModel({
      modelPath: MODEL_PATH
    });
    
    const context = await model.createContext();
    const session = new LlamaChatSession({
      contextSequence: context.getSequence()
    });

    // Define a JSON schema for structured output
    const schema = {
      type: "object",
      properties: {
        data: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              field: { type: "string" },
              contribution: { type: "string" }
            },
            required: ["name", "contribution"]
          }
        }
      },
      required: ["data"]
    };

    console.log("Generating JSON response...");
    
    const response = await session.prompt(
      "List three famous scientists and their contributions. Respond in JSON format.", 
      {
        responseFormat: {
          type: "json_object",
          schema: schema
        }
      }
    );

    console.log("\nJSON Response:");
    console.log(response);
    
    // Parse and use the JSON
    try {
      const parsed = JSON.parse(response);
      console.log("\nParsed Scientists:");
      
      parsed.data.forEach((scientist, index) => {
        console.log(`\n${index + 1}. ${scientist.name}`);
        console.log(`   Field: ${scientist.field || "Unknown"}`);
        console.log(`   Contribution: ${scientist.contribution}`);
      });
    } catch (parseError) {
      console.error("Error parsing JSON:", parseError);
      console.log("Raw response:", response);
    }
    
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
