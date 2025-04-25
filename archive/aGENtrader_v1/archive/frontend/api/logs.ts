import { FastifyPluginAsync } from 'fastify';
import fs from 'fs';
import path from 'path';
import { log } from '../vite';

interface AgentMessage {
  id: string;
  timestamp: string;
  type: string;
  symbol?: string;
  message: string;
  category?: string;
  analysis?: any; 
  decision?: any;
  agent?: string;
  executive_summary?: {
    timestamp: string;
    meeting_type: string;
    market_overview: {
      market_trend: {
        direction: string;
        strength: number;
        timeframe: string;
      };
      key_indicators: {
        moving_averages: string;
        rsi: string;
        volume: string;
      };
      sentiment: string;
      key_levels: {
        nearest_support: number;
        nearest_resistance: number;
      };
    };
    trading_recommendation: {
      action: string;
      confidence: number;
      timeframe: string;
      key_reasons: string[];
      risk_profile: {
        position_size: number;
        stop_loss: number;
        take_profit: number;
      };
    };
    key_metrics: {
      participants: number;
      analysis_points: number;
      decisions_made: number;
    };
  };
}

const plugin: FastifyPluginAsync = async (fastify) => {
  const generateId = () => Math.random().toString(36).substr(2, 9);

  fastify.get('/agent-messages', async (request, reply) => {
    try {
      console.log('[Logs API] Handling GET /agent-messages request');

      // Read from meetings/summaries directory
      const summariesPath = path.join(process.cwd(), 'data', 'meetings', 'summaries');
      await fs.promises.mkdir(summariesPath, { recursive: true });

      const messages: AgentMessage[] = [];

      if (fs.existsSync(summariesPath)) {
        const files = fs.readdirSync(summariesPath)
          .filter(file => file.startsWith('meeting_summary_'))
          .sort()
          .reverse();

        console.log(`[Logs API] Found ${files.length} meeting summary files`);

        for (const file of files) {
          try {
            const content = fs.readFileSync(path.join(summariesPath, file), 'utf8');
            const data = JSON.parse(content);

            if (data.executive_summary) {
              messages.push({
                id: generateId(),
                timestamp: data.timestamp,
                type: 'summary',
                symbol: data.discussions?.[0]?.symbol || 'BTCUSDT',
                message: JSON.stringify(data.executive_summary),
                category: 'executive_summary',
                executive_summary: data.executive_summary
              });
            } else {
              console.log(`[Logs API] No executive summary found in file ${file}`);
            }
          } catch (parseError) {
            console.error(`[Logs API] Error parsing file ${file}: ${parseError}`);
            console.error(parseError);
            continue;
          }
        }
      } else {
        console.log('[Logs API] Creating summaries directory as it does not exist');
      }

      messages.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );

      console.log(`[Logs API] Returning ${messages.length} messages with full executive summaries`);
      return messages;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`[Logs API] Error in /agent-messages: ${errorMessage}`);
      log(`Error in /agent-messages: ${errorMessage}`, 'error');
      reply.status(500).send({ error: 'Failed to fetch agent messages' });
    }
  });
};

export default plugin;