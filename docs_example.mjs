// Based on official node-llama-cpp documentation
import { LlamaModel, LlamaContext, LlamaTokenType } from "node-llama-cpp";

const MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf';

async function main() {
  console.log('Loading model from documentation example...');
  const model = new LlamaModel({
    modelPath: MODEL_PATH,
    threads: 4,
    contextSize: 4096
  });

  const context = new LlamaContext({ model });
  const prompt = "Write a short poem about artificial intelligence:";

  console.log(`Generating completion for prompt: ${prompt}`);
  const completion = await context.completion({
    prompt,
    maxTokens: 128,
    temperature: 0.7,
    topP: 0.95,
    stream: true,
  });

  let resultText = "";
  for await (const chunk of completion) {
    process.stdout.write(chunk.token);
    resultText += chunk.token;
  }

  console.log("\nFull text generated:", resultText);
}

main().catch(console.error);
