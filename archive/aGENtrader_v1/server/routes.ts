import type { Express } from "express";
import express from 'express';
import { log } from './vite';
import cors from 'cors';
import { setupVite } from './vite';
import path from 'path';
import { fileURLToPath } from 'url';
import apiRouter from './api';
import { createServer } from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export async function registerRoutes(app: Express) {
  log("Starting routes registration", "server");

  // Create HTTP server instance
  const server = createServer(app);

  // Basic middleware
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  app.use(cors());

  // Request logging middleware
  app.use((req, _res, next) => {
    log(`[${req.method}] ${req.path} (Accept: ${req.get('Accept')})`, "route");
    next();
  });

  // Mount API routes explicitly
  app.use('/api', apiRouter);
  log("API routes mounted", "server");

  // Development mode setup
  if (process.env.NODE_ENV !== 'production') {
    log("Setting up Vite development server", "server");
    await setupVite(app, server);
  } else {
    // Production mode - serve static files
    const staticPath = path.resolve(__dirname, '../../dist/public');
    app.use(express.static(staticPath));

    // SPA fallback for client-side routing
    app.get('*', (req, res, next) => {
      if (!req.path.startsWith('/api')) {
        res.sendFile(path.join(staticPath, 'index.html'));
      } else {
        next();
      }
    });
  }

  log("Route registration completed successfully", "server");
  return { app, server };
}