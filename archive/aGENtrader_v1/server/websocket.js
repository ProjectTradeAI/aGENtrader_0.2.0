import { WebSocketServer, WebSocket } from 'ws';
import { Server } from 'http';

// Simple logging utility
function log(message, source = "websocket") {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`${timestamp} [${source}] ${message}`);
}

export function setupWebSocketServer(httpServer) {
  log("Setting up WebSocket server");

  try {
    // Create WebSocket server for trading updates
    const tradingWss = new WebSocketServer({ 
      server: httpServer,
      path: '/ws/trading'
    });

    // Create WebSocket server for agent communications
    const agentWss = new WebSocketServer({
      server: httpServer,
      path: '/ws/agent'
    });

    log("WebSocket servers created successfully");

    // Handle trading connections
    tradingWss.on('connection', (ws, req) => {
      log(`New trading WebSocket connection from ${req.socket.remoteAddress}`);

      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connection_status',
        status: 'connected',
        message: 'Connected to Trading WebSocket Server'
      }));

      // Handle messages
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          log(`Received trading message: ${JSON.stringify(message)}`);

          // Echo message back for testing
          ws.send(JSON.stringify({
            type: 'echo',
            data: message
          }));
        } catch (error) {
          log(`Error processing trading message: ${error}`, "error");
        }
      });

      // Handle connection close
      ws.on('close', () => {
        log("Trading WebSocket connection closed");
      });

      // Handle errors
      ws.on('error', (error) => {
        log(`Trading WebSocket error: ${error}`, "error");
      });
    });

    // Handle agent communications
    agentWss.on('connection', (ws, req) => {
      log(`New agent WebSocket connection from ${req.socket.remoteAddress}`);

      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connection_status',
        status: 'connected',
        message: 'Connected to Agent Communication Server'
      }));

      // Handle messages
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          log(`Received agent message: ${JSON.stringify(message)}`);

          // Broadcast message to all connected clients
          agentWss.clients.forEach((client) => {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify({
                type: 'agent_message',
                data: message
              }));
            }
          });
        } catch (error) {
          log(`Error processing agent message: ${error}`, "error");
        }
      });

      // Handle connection close
      ws.on('close', () => {
        log("Agent WebSocket connection closed");
      });

      // Handle errors
      ws.on('error', (error) => {
        log(`Agent WebSocket error: ${error}`, "error");
      });
    });

    // Heartbeat to keep connections alive
    setInterval(() => {
      const sendHeartbeat = (wss) => {
        wss.clients.forEach((client) => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type: 'heartbeat' }));
          }
        });
      };

      sendHeartbeat(tradingWss);
      sendHeartbeat(agentWss);
    }, 30000);

    return { tradingWss, agentWss };
  } catch (error) {
    log(`Failed to setup WebSocket server: ${error}`, "error");
    throw error;
  }
}

// Mock trading updates for testing
export function startMockTradeUpdates(wss) {
  setInterval(() => {
    const mockPrice = 45000 + Math.random() * 1000 - 500;
    const mockVolume = Math.random() * 5000;

    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({
          type: 'price_update',
          data: {
            symbol: 'BTCUSDT',
            price: mockPrice,
            volume: mockVolume,
            timestamp: new Date().toISOString()
          }
        }));
      }
    });
  }, 5000);
}