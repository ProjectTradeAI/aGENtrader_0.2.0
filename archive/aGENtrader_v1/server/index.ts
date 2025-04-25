import Fastify from 'fastify';
import FastifyStatic from '@fastify/static';
import FastifyCors from '@fastify/cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs/promises';
import apiPlugin from './api';
import healthRoutes from './health';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize Fastify with logging
const fastify = Fastify({
  logger: {
    level: 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname',
      }
    }
  }
});

// Register plugins
const start = async () => {
  try {
    // Register CORS with specific configuration
    await fastify.register(FastifyCors, {
      origin: ['http://localhost:3000', 'http://0.0.0.0:3000'],
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
      credentials: true
    });

    // Register API routes
    await fastify.register(apiPlugin, { prefix: '/api' });

    // Register health routes
    await fastify.register(healthRoutes);

    // Development mode setup
    if (process.env.NODE_ENV !== 'production') {
      // Check for direct access via Replit URL
      const isDirectAccess = (request: any) => {
        return request.headers.host && 
               (request.headers.host.includes('.repl.co') || 
                request.headers.host.includes('.replit.dev'));
      };
      
      // Create a handler for generating HTML for direct access
      const generateDirectAccessHTML = (pageTitle: string) => {
        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>${pageTitle} | Trading Bot Platform</title>
          <style>
            body {
              font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
              background-color: #f9fafb;
              color: #111827;
              margin: 0;
              padding: 0;
              display: flex;
              flex-direction: column;
              min-height: 100vh;
            }
            header {
              background-color: #374151;
              color: white;
              padding: 1rem;
              text-align: center;
            }
            nav {
              background-color: #1f2937;
              padding: 0.5rem 1rem;
              display: flex;
              justify-content: center;
              gap: 1rem;
            }
            nav a {
              color: #e5e7eb;
              text-decoration: none;
              padding: 0.5rem 1rem;
              border-radius: 0.25rem;
              transition: background-color 0.2s;
            }
            nav a:hover {
              background-color: #4b5563;
            }
            nav a.active {
              background-color: #4b5563;
              font-weight: bold;
            }
            .container {
              max-width: 1200px;
              margin: 0 auto;
              padding: 2rem;
              flex-grow: 1;
            }
            .card {
              background-color: white;
              border-radius: 0.5rem;
              box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
              padding: 1.5rem;
              margin-bottom: 1.5rem;
            }
            h1, h2, h3 {
              color: #1f2937;
            }
            .grid {
              display: grid;
              grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
              gap: 1.5rem;
              margin-top: 2rem;
            }
            footer {
              background-color: #1f2937;
              color: #9ca3af;
              text-align: center;
              padding: 1rem;
              margin-top: auto;
            }
          </style>
        </head>
        <body>
          <header>
            <h1>Trading Bot Platform</h1>
          </header>
          <nav>
            <a href="/" class="${pageTitle === 'Dashboard' ? 'active' : ''}">Dashboard</a>
            <a href="/market-analysis" class="${pageTitle === 'Market Analysis' ? 'active' : ''}">Market Analysis</a>
            <a href="/agent-comms" class="${pageTitle === 'Agent Communications' ? 'active' : ''}">Agent Communications</a>
            <a href="/trading-ws" class="${pageTitle === 'Live Trading' ? 'active' : ''}">Live Trading</a>
            <a href="/trades" class="${pageTitle === 'Trades' ? 'active' : ''}">Trades</a>
            <a href="/settings" class="${pageTitle === 'Settings' ? 'active' : ''}">Settings</a>
          </nav>
          <div class="container">
            <div class="card">
              <h2>${pageTitle}</h2>
              <p>An AI-powered trading system with multi-agent architecture for enhanced market analysis and decision making.</p>
              <p>This page is a placeholder for the direct-access version of the application. Please visit the development server at <a href="http://localhost:3000">http://localhost:3000</a> for the full interactive experience.</p>
            </div>
            
            <div class="grid">
              <div class="card">
                <h3>Market Analysis</h3>
                <p>Advanced technical and fundamental analysis of cryptocurrency markets.</p>
              </div>
              <div class="card">
                <h3>Agent Communications</h3>
                <p>Monitor interactions between specialized trading agents.</p>
              </div>
              <div class="card">
                <h3>Live Trading</h3>
                <p>Real-time updates on trading decisions and market movements.</p>
              </div>
            </div>
          </div>
          <footer>
            <p>© 2025 Trading Bot Platform</p>
          </footer>
        </body>
        </html>
        `;
      };

      // Add routes that handle both Vite dev server and direct access
      // Create route handler function
      const createRouteHandler = (pageTitle: string, path: string) => {
        return async (request: any, reply: any) => {
          if (isDirectAccess(request)) {
            // Serve HTML for direct access
            reply.type('text/html').send(generateDirectAccessHTML(pageTitle));
          } else {
            // Redirect to Vite dev server
            reply.redirect(`http://localhost:3000${path}`);
          }
        };
      };

      // Register all routes
      fastify.get('/', createRouteHandler('Dashboard', '/'));
      fastify.get('/dashboard', createRouteHandler('Dashboard', '/dashboard'));
      fastify.get('/market-analysis', createRouteHandler('Market Analysis', '/market-analysis'));
      fastify.get('/agent-comms', createRouteHandler('Agent Communications', '/agent-comms'));
      fastify.get('/trading-ws', createRouteHandler('Live Trading', '/trading-ws'));
      fastify.get('/trades', createRouteHandler('Trades', '/trades'));
      fastify.get('/settings', createRouteHandler('Settings', '/settings'));

      console.log('Development mode: Redirecting to Vite frontend server');
    } else {
      // Production mode - serve static files
      const publicPath = path.join(__dirname, '../dist/public');
      await fastify.register(FastifyStatic, {
        root: publicPath,
        prefix: '/'
      });

      // SPA fallback for client-side routing
      fastify.setNotFoundHandler(async (request, reply) => {
        if (!request.url.startsWith('/api')) {
          try {
            const indexPath = path.join(publicPath, 'index.html');
            const content = await fs.readFile(indexPath, 'utf8');
            reply.type('text/html').send(content);
          } catch (err) {
            request.log.error(err);
            reply.code(500).send({ error: 'Internal Server Error' });
          }
        }
      });
    }

    // Start the server
    const PORT = parseInt(process.env.PORT || '5000', 10);
    await fastify.listen({ port: PORT, host: '0.0.0.0' });
    console.log(`Server running at http://0.0.0.0:${PORT}`);

  } catch (err) {
    console.error('Fatal server error:', err);
    process.exit(1);
  }
};

start();

export default fastify;