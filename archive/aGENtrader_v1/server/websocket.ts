import { WebSocketServer, WebSocket } from 'ws';
import { Server } from 'http';
import { log } from './vite';

export function setupWebSocketServer(httpServer: Server) {
  log("Setting up WebSocket server...", "websocket");

  try {
    // Create WebSocket servers for different endpoints with distinct paths
    const tradingWss = new WebSocketServer({
      server: httpServer,
      path: '/ws/trading'  // Changed path to be more specific
    });

    const agentWss = new WebSocketServer({
      server: httpServer,
      path: '/ws/agent'  // Separate path for agent communications
    });

    log("WebSocket servers created successfully", "websocket");

    // Handle trading connections
    tradingWss.on('connection', (ws: WebSocket, req) => {
      log(`New trading WebSocket connection from ${req.socket.remoteAddress}`, "websocket");

      ws.send(JSON.stringify({
        type: 'connection_status',
        status: 'connected',
        message: 'Connected to Trading WebSocket Server'
      }));

      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          log(`Received trading message: ${JSON.stringify(message)}`, "websocket");

          switch (message.type) {
            case 'subscribe':
              // Handle subscription requests
              ws.send(JSON.stringify({
                type: 'subscription_confirmed',
                data: message.data
              }));
              break;

            case 'request_analysis':
              // Handle analysis requests
              if (message.symbol) {
                ws.send(JSON.stringify({
                  type: 'analysis_update',
                  data: {
                    symbol: message.symbol,
                    timestamp: new Date().toISOString(),
                    // Add more analysis data as needed
                  }
                }));
              }
              break;

            default:
              log(`Unknown message type: ${message.type}`, "websocket");
              ws.send(JSON.stringify({
                type: 'error',
                message: 'Unknown message type'
              }));
          }
        } catch (error) {
          log(`Error processing trading message: ${error}`, "error");
          ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to process message'
          }));
        }
      });

      setupWebSocketEventHandlers(ws, 'trading');
    });

    // Handle agent communications
    agentWss.on('connection', (ws: WebSocket, req) => {
      log(`New agent WebSocket connection from ${req.socket.remoteAddress}`, "websocket");

      ws.send(JSON.stringify({
        type: 'connection_status',
        status: 'connected',
        message: 'Connected to Agent Communication Server'
      }));

      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          log(`Received agent message: ${JSON.stringify(message)}`, "websocket");

          // Broadcast message to all connected agents
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
          ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to process message'
          }));
        }
      });

      setupWebSocketEventHandlers(ws, 'agent');
    });

    // Setup heartbeat interval
    const heartbeatInterval = setInterval(() => {
      const sendHeartbeat = (wss: WebSocketServer) => {
        wss.clients.forEach((client) => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({ type: 'heartbeat' }));
          }
        });
      };

      sendHeartbeat(tradingWss);
      sendHeartbeat(agentWss);
    }, 30000);

    // Clear interval on server shutdown
    httpServer.on('close', () => {
      clearInterval(heartbeatInterval);
    });

    return { tradingWss, agentWss };
  } catch (error) {
    log(`Failed to setup WebSocket server: ${error}`, "error");
    throw error;
  }
}

function setupWebSocketEventHandlers(ws: WebSocket, type: string) {
  ws.on('close', () => {
    log(`${type} WebSocket connection closed`, "websocket");
  });

  ws.on('error', (error) => {
    log(`${type} WebSocket error: ${error}`, "error");
  });

  // Add ping/pong monitoring
  ws.on('pong', () => {
    (ws as any).isAlive = true;
  });
}

// Mock data generation for testing
export function startMockTradeUpdates(wss: WebSocketServer) {
  setInterval(() => {
    const mockData = {
      symbol: 'BTCUSDT',
      price: Math.random() * 1000 + 45000,
      volume: Math.random() * 100,
      timestamp: new Date().toISOString()
    };

    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({
          type: 'market_update',
          data: mockData
        }));
      }
    });
  }, 5000);
}