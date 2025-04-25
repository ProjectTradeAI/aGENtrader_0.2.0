import { useState } from 'react';
import { useWebSocket } from '@/hooks/use-websocket';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function WebSocketTest() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<string[]>([]);

  const { isConnected, error, sendMessage } = useWebSocket({
    path: '/ws-test',
    onMessage: (data) => {
      setMessages(prev => [...prev, `Received: ${typeof data === 'string' ? data : JSON.stringify(data)}`]);
    },
    onOpen: () => {
      setMessages(prev => [...prev, 'WebSocket connected successfully']);
    },
    onClose: () => {
      setMessages(prev => [...prev, 'WebSocket connection closed']);
    }
  });

  const handleSend = () => {
    if (message.trim()) {
      sendMessage(message);
      setMessages(prev => [...prev, `Sent: ${message}`]);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">WebSocket Test</h1>

      <div className={`p-3 mb-4 rounded ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
        Status: {isConnected ? 'Connected' : 'Disconnected'}
        {error && <div className="text-red-600 mt-1">Error: {error}</div>}
      </div>

      <div className="mb-4 flex gap-2">
        <Input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={!isConnected}
          placeholder="Type a message..."
          className="flex-1"
        />
        <Button
          onClick={handleSend}
          disabled={!isConnected || !message.trim()}
          variant="default"
        >
          Send
        </Button>
      </div>

      <div className="border rounded p-4 h-[400px] overflow-y-auto">
        {messages.map((msg, i) => (
          <div key={i} className="py-1">
            <span className="text-gray-500 text-sm">
              {new Date().toLocaleTimeString()}
            </span>
            : {msg}
          </div>
        ))}
      </div>
    </div>
  );
}