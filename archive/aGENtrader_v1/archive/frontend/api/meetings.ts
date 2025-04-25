import { Request, Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import { log } from '../vite';

interface MeetingSummary {
  id: string;
  timestamp: string;
}

export const getMeetingsList = async (_req: Request, res: Response) => {
  try {
    const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');

    // Create directory if it doesn't exist
    fs.mkdirSync(meetingsDir, { recursive: true });

    const files = fs.readdirSync(meetingsDir)
      .filter(file => file.startsWith('meeting_summary_'))
      .map(file => {
        const data = fs.readFileSync(path.join(meetingsDir, file), 'utf8');
        const meeting = JSON.parse(data);
        return {
          id: file.replace('meeting_summary_', '').replace('.json', ''),
          timestamp: meeting.timestamp
        };
      })
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    log(`Fetched ${files.length} meetings`, 'meetings');
    return res.status(200).json(files);
  } catch (error) {
    log(`Error getting meetings list: ${(error as Error).message}`, 'error');
    return res.status(500).json({ error: 'Failed to retrieve meetings list' });
  }
};

export const getMeetingById = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const meetingPath = path.join(process.cwd(), `data/meetings/summaries/meeting_summary_${id}.json`);

    if (!fs.existsSync(meetingPath)) {
      log(`Meeting not found: ${id}`, 'meetings');
      return res.status(404).json({ error: 'Meeting not found' });
    }

    const meetingData = fs.readFileSync(meetingPath, 'utf8');
    const meeting = JSON.parse(meetingData);

    log(`Fetched meeting: ${id}`, 'meetings');
    return res.status(200).json(meeting);
  } catch (error) {
    log(`Error getting meeting ${req.params.id}: ${(error as Error).message}`, 'error');
    return res.status(500).json({ error: 'Failed to retrieve meeting' });
  }
};

export const getLatestMeeting = async (_req: Request, res: Response) => {
  try {
    const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');

    // Create directory if it doesn't exist
    fs.mkdirSync(meetingsDir, { recursive: true });

    const files = fs.readdirSync(meetingsDir)
      .filter(file => file.startsWith('meeting_summary_'))
      .map(file => ({
        path: path.join(meetingsDir, file),
        mtime: fs.statSync(path.join(meetingsDir, file)).mtime
      }))
      .sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

    if (files.length === 0) {
      log('No meetings found', 'meetings');
      return res.status(404).json({ error: 'No meetings available' });
    }

    const latestMeetingData = fs.readFileSync(files[0].path, 'utf8');
    const meeting = JSON.parse(latestMeetingData);

    log('Fetched latest meeting', 'meetings');
    return res.status(200).json(meeting);
  } catch (error) {
    log(`Error getting latest meeting: ${(error as Error).message}`, 'error');
    return res.status(500).json({ error: 'Failed to retrieve latest meeting' });
  }
};

export const triggerMeeting = async (_req: Request, res: Response) => {
  try {
    const { spawn } = require('child_process');
    const pythonProcess = spawn('python', ['main.py', '--trigger-meeting']);

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data: Buffer) => {
      output += data.toString();
      log(`Meeting process output: ${data.toString().trim()}`, 'meetings');
    });

    pythonProcess.stderr.on('data', (data: Buffer) => {
      errorOutput += data.toString();
      log(`Meeting process error: ${data.toString().trim()}`, 'error');
    });

    pythonProcess.on('close', (code: number) => {
      if (code === 0) {
        log('Meeting triggered successfully', 'meetings');
        return res.status(200).json({ 
          success: true, 
          message: 'Meeting triggered successfully',
          output
        });
      } else {
        log(`Meeting process failed with code ${code}`, 'error');
        return res.status(500).json({ 
          error: 'Failed to trigger meeting', 
          errorDetails: errorOutput 
        });
      }
    });
  } catch (error) {
    log(`Error triggering meeting: ${(error as Error).message}`, 'error');
    return res.status(500).json({ error: 'Failed to trigger meeting' });
  }
};