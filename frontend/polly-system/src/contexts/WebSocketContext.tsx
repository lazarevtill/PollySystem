import React, { createContext, useContext, useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/use-websocket';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
  lastMessage: any;
  sendMessage: (data: unknown) => void;
  isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [wsUrl, setWsUrl] = useState<string>('');

  useEffect(() => {
    if (isAuthenticated) {
      // Convert HTTP to WS protocol
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsEndpoint = `${protocol}//${window.location.host}/api/ws`;
      setWsUrl(wsEndpoint);
    }
  }, [isAuthenticated]);

  const { lastMessage, readyState, sendMessage } = useWebSocket(wsUrl);

  return (
    <WebSocketContext.Provider
      value={{
        lastMessage,
        sendMessage,
        isConnected: readyState === WebSocket.OPEN,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

