import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Simple logging utility
function log(message, source = "server") {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`${timestamp} [${source}] ${message}`);
}

const app = express();

// Basic middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors());

// Request logging
app.use((req, res, next) => {
  log(`${req.method} ${req.path}`, 'request');
  next();
});

// Health check endpoint
app.get('/api/health', (_req, res) => {
  res.json({ 
    status: 'ok',
    timestamp: new Date().toISOString()
  });
});

// Test endpoint
app.get('/api/test', (_req, res) => {
  res.json({
    message: 'API is working',
    timestamp: new Date().toISOString()
  });
});

// Error handling
app.use((err, req, res, next) => {
  log(`Error: ${err.message}`, 'error');
  res.status(500).json({ error: 'Internal server error' });
});

// Serve static files in production
if (process.env.NODE_ENV === 'production') {
  const staticPath = path.resolve(__dirname, '../dist/public');
  app.use(express.static(staticPath));

  // SPA fallback 
  app.get('*', (_req, res) => {
    res.sendFile(path.join(staticPath, 'index.html'));
  });
}

// Start server with proper error handling
const port = parseInt(process.env.PORT || "5000", 10);

const server = app.listen(port, "0.0.0.0", () => {
  log(`Server started on port ${port}`);
}).on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    log(`Port ${port} is already in use`, 'error');
  }
  process.exit(1);
});

export default app;