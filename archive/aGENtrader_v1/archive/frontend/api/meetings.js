import { Request, Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import { log } from '../vite.ts';

const getMeetingsList = async (_req, res) => {
  try {
    console.log('[meetings] Attempting to fetch meetings list');
    const meetingsDir = path.join(process.cwd(), 'data/meetings/summaries');

    // Create directory if it doesn't exist
    fs.mkdirSync(meetingsDir, { recursive: true });
    console.log(`[meetings] Checking directory: ${meetingsDir}`);

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

    console.log(`[meetings] Found ${files.length} meetings`);
    return res.status(200).json(files);
  } catch (error) {
    console.error(`[meetings] Error getting meetings list: ${error.message}`);
    return res.status(500).json({ error: 'Failed to retrieve meetings list' });
  }
};

const getMeetingById = async (req, res) => {
  try {
    const { id } = req.params;
    console.log(`[meetings] Fetching meeting with ID: ${id}`);
    const meetingPath = path.join(process.cwd(), `data/meetings/summaries/meeting_summary_${id}.json`);

    if (!fs.existsSync(meetingPath)) {
      console.log(`[meetings] Meeting not found: ${id}`);
      return res.status(404).json({ error: 'Meeting not found' });
    }

    const meetingData = fs.readFileSync(meetingPath, 'utf8');
    const meeting = JSON.parse(meetingData);

    console.log(`[meetings] Successfully fetched meeting: ${id}`);
    return res.status(200).json(meeting);
  } catch (error) {
    console.error(`[meetings] Error getting meeting ${req.params.id}: ${error.message}`);
    return res.status(500).json({ error: 'Failed to retrieve meeting' });
  }
};

const getLatestMeeting = async (_req, res) => {
  try {
    console.log('[meetings] Attempting to fetch latest meeting');
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
      console.log('[meetings] No meetings found');
      return res.status(404).json({ error: 'No meetings available' });
    }

    const latestMeetingData = fs.readFileSync(files[0].path, 'utf8');
    const meeting = JSON.parse(latestMeetingData);

    console.log('[meetings] Successfully fetched latest meeting');
    return res.status(200).json(meeting);
  } catch (error) {
    console.error(`[meetings] Error getting latest meeting: ${error.message}`);
    return res.status(500).json({ error: 'Failed to retrieve latest meeting' });
  }
};

const triggerMeeting = async (_req, res) => {
  try {
    console.log('[meetings] Attempting to trigger new meeting');
    const { spawn } = require('child_process');
    const pythonProcess = spawn('python', ['main.py', '--trigger-meeting']);

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
      console.log(`[meetings] Process output: ${data.toString().trim()}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
      console.error(`[meetings] Process error: ${data.toString().trim()}`);
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        console.log('[meetings] Meeting triggered successfully');
        return res.status(200).json({ 
          success: true, 
          message: 'Meeting triggered successfully',
          output
        });
      } else {
        console.error(`[meetings] Process failed with code ${code}`);
        return res.status(500).json({ 
          error: 'Failed to trigger meeting', 
          errorDetails: errorOutput 
        });
      }
    });
  } catch (error) {
    console.error(`[meetings] Error triggering meeting: ${error.message}`);
    return res.status(500).json({ error: 'Failed to trigger meeting' });
  }
};

export {
  getMeetingsList,
  getMeetingById,
  getLatestMeeting,
  triggerMeeting
};
