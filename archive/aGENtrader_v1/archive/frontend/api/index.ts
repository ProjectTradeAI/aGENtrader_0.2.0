import { FastifyPluginAsync } from 'fastify';
import { log } from '../vite';
import * as path from 'path';
import * as fs from 'fs/promises';

const apiPlugin: FastifyPluginAsync = async (fastify) => {
  // Request logging
  fastify.addHook('onRequest', async (request) => {
    request.requestStartTime = Date.now();
    log(`[API] ${request.method} ${request.url}`, 'api');
  });

  fastify.addHook('onResponse', async (request, reply) => {
    const duration = Date.now() - request.requestStartTime;
    log(`[API] Response ${reply.statusCode} (${duration}ms)`, 'api');
  });

  // Test endpoint
  fastify.get('/test', async () => {
    log('[API] Test endpoint accessed', 'api');
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      message: 'API is working'
    };
  });

  // Agent messages endpoint
  fastify.get('/logs/agent-messages', async () => {
    try {
      log('[Logs API] Handling GET /agent-messages request', 'api');

      const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');
      await fs.mkdir(meetingsDir, { recursive: true });

      const files = await fs.readdir(meetingsDir);
      const summaryFiles = files
        .filter(f => f.startsWith('meeting_summary_'))
        .sort((a, b) => b.localeCompare(a))
        .slice(0, 5);

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
          log(`[Logs API] Error reading meeting file ${file}: ${err instanceof Error ? err.message : 'Unknown error'}`, 'api');
        }
      }

      log(`[Logs API] Returning ${messages.length} messages`, 'api');
      return messages;

    } catch (err) {
      log(`[Logs API] Error: ${err instanceof Error ? err.message : 'Unknown error'}`, 'api');
      throw err;
    }
  });

  // Configure existing route handlers here
  fastify.get('/meetings', async () => {
    const startTime = Date.now();
    try {
      const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');
      await fs.mkdir(meetingsDir, { recursive: true });

      const files = await fs.readdir(meetingsDir);
      const meetings = await Promise.all(
        files
          .filter(file => file.startsWith('meeting_summary_'))
          .map(async (file) => {
            const data = await fs.readFile(path.join(meetingsDir, file), 'utf8');
            const meeting = JSON.parse(data);
            return {
              id: file.replace('meeting_summary_', '').replace('.json', ''),
              timestamp: meeting.timestamp
            };
          })
      );

      meetings.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      log(`[${new Date().toISOString()}] /meetings completed in ${Date.now() - startTime}ms`, 'api');
      return meetings;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`[${new Date().toISOString()}] Error in /meetings: ${errorMessage}`, 'error');
      throw new Error('Failed to retrieve meetings list');
    }
  });

  // Latest meeting endpoint
  fastify.get('/meetings/latest', async () => {
    const startTime = Date.now();
    try {
      const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');
      await fs.mkdir(meetingsDir, { recursive: true });

      const files = await fs.readdir(meetingsDir);
      const stats = await Promise.all(
        files
          .filter(file => file.startsWith('meeting_summary_'))
          .map(async (file) => {
            const filePath = path.join(meetingsDir, file);
            const stat = await fs.stat(filePath);
            return { path: filePath, mtime: stat.mtime };
          })
      );

      const sorted = stats.sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

      if (sorted.length === 0) {
        throw new Error('No meetings available');
      }

      const latestMeetingData = await fs.readFile(sorted[0].path, 'utf8');
      log(`[${new Date().toISOString()}] /meetings/latest completed in ${Date.now() - startTime}ms`, 'api');
      return JSON.parse(latestMeetingData);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`[${new Date().toISOString()}] Error in /meetings/latest: ${errorMessage}`, 'error');
      throw new Error('Failed to retrieve latest meeting');
    }
  });

  // Get meeting by ID
  fastify.get('/meetings/:id', async (request, reply) => {
    const startTime = Date.now();
    const { id } = request.params as { id: string };
    try {
      const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');
      await fs.mkdir(meetingsDir, {recursive: true});
      const meetingPath = path.join(meetingsDir, `meeting_summary_${id}.json`);
      const meetingData = await fs.readFile(meetingPath, 'utf8');
      log(`[${new Date().toISOString()}] /meetings/:id completed in ${Date.now() - startTime}ms`, 'api');
      return JSON.parse(meetingData);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`[${new Date().toISOString()}] Error in /meetings/:id: ${errorMessage}`, 'error');
      reply.code(404);
      throw new Error('Meeting not found');
    }
  });

  // Trigger new meeting
  fastify.post('/meetings/trigger', async () => {
    const startTime = Date.now();
    try {
      const { spawn } = require('child_process');
      const pythonProcess = spawn('python', ['main.py', '--trigger-meeting']);

      return new Promise((resolve, reject) => {
        let output = '';
        let errorOutput = '';

        pythonProcess.stdout.on('data', (data: Buffer) => {
          output += data.toString();
          log(`Meeting process output: ${data.toString().trim()}`, 'api');
        });

        pythonProcess.stderr.on('data', (data: Buffer) => {
          errorOutput += data.toString();
          log(`Meeting process error: ${data.toString().trim()}`, 'api');
        });

        pythonProcess.on('close', (code: number) => {
          if (code === 0) {
            log(`[${new Date().toISOString()}] /meetings/trigger completed in ${Date.now() - startTime}ms`, 'api');
            resolve({
              success: true,
              message: 'Meeting triggered successfully',
              output
            });
          } else {
            log(`[${new Date().toISOString()}] Error in /meetings/trigger: ${errorOutput}`, 'error');
            reject(new Error(`Failed to trigger meeting: ${errorOutput}`));
          }
        });
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`[${new Date().toISOString()}] Error in /meetings/trigger: ${errorMessage}`, 'error');
      throw new Error('Failed to trigger meeting');
    }
  });
};

export default apiPlugin;

// Add TypeScript interface for extended request type
declare module 'fastify' {
  interface FastifyRequest {
    requestStartTime: number;
  }
}