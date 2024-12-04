import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketHook {
  lastMessage: MessageEvent | null;
  readyState: number;
  sendMessage: (data: unknown) => void;
}

export function useWebSocket(url: string): WebSocketHook {
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const ws = useRef<WebSocket | null>(null);

  const sendMessage = useCallback(
    (data: unknown) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(data));
      }
    },
    []
  );

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setReadyState(WebSocket.OPEN);
    };

    ws.current.onclose = () => {
      setReadyState(WebSocket.CLOSED);
    };

    ws.current.onmessage = (event: MessageEvent) => {
      setLastMessage(event);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  return { lastMessage, readyState, sendMessage };
}
