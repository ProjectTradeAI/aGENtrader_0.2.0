// Simple health check server to validate application status
import express from 'express';
import { log } from './vite.ts';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Set a global variable to track the active port across the application
global.activePort = null;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function setupHealthRoutes(app) {
  // Basic health route to check if server is responsive
  app.get('/api/health', (req, res) => {
    try {
      // Check for various potential issues
      const healthInfo = {
        status: 'ok',
        timestamp: new Date().toISOString(),
        serverInfo: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          nodeVersion: process.version,
          activePort: global.activePort || process.env.PORT || '(unknown)'
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
          healthInfo.marketData.details = err.message;
        }
      } else {
        healthInfo.marketData.status = 'No heartbeat file found';
      }

      // Check if client build exists
      const clientDistPath = path.resolve(__dirname, '../dist/public');
      if (fs.existsSync(clientDistPath)) {
        try {
          const files = fs.readdirSync(clientDistPath);
          healthInfo.clientInfo.buildExists = true;
          healthInfo.clientInfo.fileCount = files.length;
        } catch (err) {
          healthInfo.clientInfo.buildExists = false;
          healthInfo.clientInfo.buildError = err.message;
        }
      } else {
        healthInfo.clientInfo.buildExists = false;
      }

      res.json(healthInfo);
    } catch (err) {
      // Log the error
      log(`Health check error: ${err.message}`, 'health');
      // Return a 500 status with error details
      res.status(500).json({
        status: 'error',
        message: err.message,
        stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
      });
    }
  });

  log('Health check routes configured', 'health');
}