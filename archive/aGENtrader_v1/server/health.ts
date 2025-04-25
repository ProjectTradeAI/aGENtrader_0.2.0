import { FastifyInstance } from 'fastify';
import { log } from './vite';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default async function healthRoutes(fastify: FastifyInstance) {
  // Basic health route to check if server is responsive
  fastify.get('/health', async (req, reply) => {
    try {
      // Check for various potential issues
      const healthInfo = {
        status: 'ok',
        timestamp: new Date().toISOString(),
        serverInfo: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          nodeVersion: process.version,
          activePort: process.env.PORT || '5000'
        },
        clientInfo: {},
        marketData: {}
      };

      // Check market data collector status
      const heartbeatPath = path.resolve(__dirname, '../data/market_data/collection_heartbeat.json');
      if (fs.existsSync(heartbeatPath)) {
        try {
          const heartbeat = JSON.parse(fs.readFileSync(heartbeatPath, 'utf8'));
          const lastUpdate = new Date(heartbeat.timestamp);
          const now = new Date();
          const minutesSinceUpdate = (now - lastUpdate) / (1000 * 60);

          healthInfo.marketData = {
            ...heartbeat,
            isActive: minutesSinceUpdate < 5, // Consider stale if no update in 5 minutes
            minutesSinceUpdate
          };
        } catch (err) {
          healthInfo.marketData.error = 'Failed to parse heartbeat data';
          healthInfo.marketData.details = err instanceof Error ? err.message : 'Unknown error';
        }
      } else {
        healthInfo.marketData.status = 'No heartbeat file found';
      }

      reply.send(healthInfo);
    } catch (err) {
      // Log the error
      log(`Health check error: ${err instanceof Error ? err.message : 'Unknown error'}`, 'health');
      // Return a 500 status with error details
      reply.status(500).send({
        status: 'error',
        message: err instanceof Error ? err.message : 'Unknown error',
        stack: process.env.NODE_ENV === 'development' ? err instanceof Error ? err.stack : undefined : undefined
      });
    }
  });

  log('Health check routes configured', 'health');
}
