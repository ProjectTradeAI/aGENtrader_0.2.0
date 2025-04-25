import { log } from '../vite';
import { fetchWithTimeout } from '../utils';

interface DeepseekResponse {
  response: string;
  mode: 'deepseek';
}

export async function generateDeepseekResponse(message: string): Promise<DeepseekResponse> {
  try {
    const response = await fetchWithTimeout('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.DEEPSEK_API_KEY}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          {
            role: 'system',
            content: 'You are a helpful trading assistant that can analyze markets and provide insights.'
          },
          {
            role: 'user',
            content: message
          }
        ],
        temperature: 0.7,
        max_tokens: 1000
      }),
      timeout: 30000,
    });

    if (!response.ok) {
      const errorData = await response.text();
      log(`Deepseek API error: ${response.status} - ${errorData}`, 'error');
      throw new Error(`Deepseek API error: ${response.status}`);
    }

    const data = await response.json();
    log(`Deepseek response generated`, 'llm');

    return {
      response: data.choices[0].message.content,
      mode: 'deepseek'
    };
  } catch (error) {
    log(`Deepseek error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    throw error;
  }
}
