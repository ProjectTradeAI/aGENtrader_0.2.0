import { Router } from 'express';
import { log } from '../vite';
import path from 'path';
import fs from 'fs/promises';

const apiRouter = Router();

// Error boundary middleware
const errorHandler = (err, _req, res, next) => {
  log(`API Error: ${err.message}`, 'error');
  if (res.headersSent) {
    return next(err);
  }
  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
};

// API request logging middleware
apiRouter.use((req, _res, next) => {
  log(`[${new Date().toISOString()}] API request: [${req.method}] ${req.path}`, 'api');
  next();
});

// Test endpoint for API health check
apiRouter.get('/test', (req, res) => {
  log(`[API] Test endpoint accessed: ${req.path}`, 'api');
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    message: 'API is working'
  });
});

// Agent messages endpoint
apiRouter.get('/logs/agent-messages', async (_req, res, next) => {
  try {
    log('[Logs API] Handling GET /agent-messages request', 'api');

    const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');
    await fs.mkdir(meetingsDir, { recursive: true });

    const files = await fs.readdir(meetingsDir);
    const summaryFiles = files
      .filter(f => f.startsWith('meeting_summary_'))
      .sort((a, b) => b.localeCompare(a)) // Sort by filename descending
      .slice(0, 5); // Get latest 5 files

    log(`[Logs API] Found ${summaryFiles.length} meeting summary files`, 'api');

    const messages = [];
    for (const file of summaryFiles) {
      try {
        const data = await fs.readFile(path.join(meetingsDir, file), 'utf8');
        const meeting = JSON.parse(data);

        if (meeting.executive_summary) {
          messages.push({
            timestamp: meeting.timestamp,
            agent: 'Market Analyst',
            executiveSummary: meeting.executive_summary
          });
        } else {
          log(`[Logs API] No executive summary found in file ${file}`, 'api');
        }
      } catch (err) {
        log(`[Logs API] Error reading meeting file ${file}: ${err.message}`, 'api');
        // Continue processing other files
      }
    }

    log(`[Logs API] Returning ${messages.length} messages with full executive summaries`, 'api');
    res.json(messages);
  } catch (err) {
    next(err);
  }
});

// Register error handler
apiRouter.use(errorHandler);

export default apiRouter;