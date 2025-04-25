import express from 'express';
import cors from 'cors';
import { log } from './vite';
import apiRouter from './api';
import path from 'path';
import { fileURLToPath } from 'url';
import { WebSocketServer } from 'ws';
import http from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Basic middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors({
  origin: true,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// API request logging
app.use((req, res, next) => {
  log(`API request: ${req.method} ${req.originalUrl}`, 'api');
  next();
});

// Mount API routes
app.use('/api', apiRouter);

// Serve static files in production
const staticPath = path.resolve(__dirname, '../dist/public');
app.use(express.static(staticPath));

// SPA fallback for client-side routing
app.get('*', (_req, res) => {
  res.sendFile(path.join(staticPath, 'index.html'));
});

const port = parseInt(process.env.PORT || '5000', 10);
if (isNaN(port)) {
  throw new Error('Invalid port number');
}

// Create HTTP server instance
const server = http.createServer(app);

// Create WebSocket server
const wss = new WebSocketServer({ noServer: true });

// Handle WebSocket connections
wss.on('connection', (ws, request) => {
  const url = new URL(request.url || '', `http://${request.headers.host}`);
  const pathname = url.pathname;

  log(`New WebSocket connection established on path: ${pathname}`, 'websocket');

  ws.on('message', (message) => {
    log(`Received message on ${pathname}: ${message}`, 'websocket');
    ws.send(message.toString());
  });

  ws.on('error', (error) => {
    log(`WebSocket error on ${pathname}: ${error}`, 'error');
  });

  ws.on('close', () => {
    log(`WebSocket connection closed on ${pathname}`, 'websocket');
  });
});

// Enable WebSocket upgrade
server.on('upgrade', (request, socket, head) => {
  const url = new URL(request.url || '', `http://${request.headers.host}`);
  const pathname = url.pathname;

  if (pathname.startsWith('/@vite')) {
    return;
  }

  if (pathname === '/ws-test' || pathname === '/trading-ws') {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
    return;
  }

  socket.destroy();
});

// Start the server
server.listen(port, '0.0.0.0', () => {
  log(`Server running on port ${port}`);
});

export { app, server };