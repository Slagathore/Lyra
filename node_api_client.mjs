/**
 * Example of calling the oobabooga API from Node.js
 * 
 * This demonstrates how you can use oobabooga from your Node.js applications
 * without dealing with the model loading and compatibility issues.
 */

import fetch from 'node-fetch';

// Base URL for the API
const API_URL = 'http://localhost:5000/v1';

/**
 * Generate text using the chat completions endpoint
 * @param {string} prompt - The user message
 * @param {string} systemPrompt - Optional system instructions
 * @param {boolean} stream - Whether to stream the response
 * @returns {Promise<string>} - The generated text
 */
async function generateText(prompt, systemPrompt = '', stream = false) {
  // Build messages array
  const messages = [];
  if (systemPrompt) {
    messages.push({ role: "system", content: systemPrompt });
  }
  messages.push({ role: "user", content: prompt });

  try {
    if (!stream) {
      // Regular non-streaming request
      const response = await fetch(`${API_URL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: "Qwen2.5",
          messages: messages,
          temperature: 0.7,
          max_tokens: 500
        }),
      });
      
      const data = await response.json();
      if (!data.choices || data.choices.length === 0) {
        throw new Error("Invalid response format");
      }
      
      return data.choices[0].message.content;
    } else {
      // Streaming request (returns async iterator)
      const response = await fetch(`${API_URL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: "Qwen2.5",
          messages: messages,
          temperature: 0.7,
          max_tokens: 500,
          stream: true
        }),
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      return {
        async *[Symbol.asyncIterator]() {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            // Process SSE data chunks
            const lines = chunk.split('\n').filter(line => line.trim().startsWith('data: '));
            
            for (const line of lines) {
              const jsonStr = line.replace('data: ', '').trim();
              if (jsonStr === '[DONE]') break;
              
              try {
                const data = JSON.parse(jsonStr);
                const content = data.choices[0]?.delta?.content;
                if (content) yield content;
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }
        }
      };
    }
  } catch (error) {
    console.error('Error generating text:', error);
    throw error;
  }
}

/**
 * Generate structured JSON output
 * @param {string} prompt - The user message
 * @returns {Promise<object>} - The parsed JSON response
 */
async function generateJSON(prompt, systemPrompt = 'You are a helpful assistant that outputs JSON.') {
  try {
    const response = await fetch(`${API_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: "Qwen2.5",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 500,
        response_format: { type: "json_object" }
      }),
    });
    
    const data = await response.json();
    if (!data.choices || data.choices.length === 0) {
      throw new Error("Invalid response format");
    }
    
    const jsonStr = data.choices[0].message.content;
    return JSON.parse(jsonStr);
  } catch (error) {
    console.error('Error generating JSON:', error);
    throw error;
  }
}

// Example usage
async function runExamples() {
  try {
    console.log('=== BASIC TEXT GENERATION ===');
    const poem = await generateText('Write a short poem about artificial intelligence.');
    console.log(poem);
    console.log('\n');
    
    console.log('=== JSON GENERATION ===');
    const scientists = await generateJSON('List three famous scientists and their contributions.');
    console.log(JSON.stringify(scientists, null, 2));
    console.log('\n');
    
    console.log('=== STREAMING EXAMPLE ===');
    console.log('Generating response: ');
    const stream = await generateText('Explain quantum computing in simple terms.', '', true);
    for await (const chunk of stream) {
      process.stdout.write(chunk);
    }
    console.log('\n');
    
  } catch (error) {
    console.error('Error in examples:', error);
  }
}

// Run the examples if this file is executed directly
if (process.argv[1] === new URL(import.meta.url).pathname) {
  console.log("Testing API client for oobabooga text-generation-webui");
  console.log("Make sure the server is running with the --api flag enabled");
  console.log("URL: http://localhost:5000/v1\n");
  
  runExamples();
}

// Export functions for use in other modules
export { generateText, generateJSON };
