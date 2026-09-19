import { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';

interface WSMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

interface WebSocketContextType {
  isConnected: boolean;
  subscribeToTrain: (trainId: number) => void;
  unsubscribeFromTrain: (trainId: number) => void;
  onTrainUpdate: (callback: (data: unknown) => void) => () => void;
  onAlert: (callback: (data: unknown) => void) => () => void;
  onCongestionUpdate: (callback: (data: unknown) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setInterval>>();
  const trainSubscriptionsRef = useRef<Set<number>>(new Set());
  const handlersRef = useRef<Map<string, Set<(data: unknown) => void>>>(new Map());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const channel = user?.role === 'PASSENGER' ? 'trains' : 'control-room';
    const ws = new WebSocket(`${WS_URL}/ws/${channel}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
      trainSubscriptionsRef.current.forEach((trainId) => {
        ws.send(JSON.stringify({ type: 'subscribe_train', train_id: trainId }));
      });
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        const handlers = handlersRef.current.get(message.type);
        if (handlers) {
          handlers.forEach((handler) => handler(message.data));
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }, [user?.role]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const subscribeToTrain = useCallback((trainId: number) => {
    trainSubscriptionsRef.current.add(trainId);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe_train', train_id: trainId }));
    }
  }, []);

  const unsubscribeFromTrain = useCallback((trainId: number) => {
    trainSubscriptionsRef.current.delete(trainId);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe_train', train_id: trainId }));
    }
  }, []);

  const subscribe = useCallback((type: string, handler: (data: unknown) => void) => {
    if (!handlersRef.current.has(type)) {
      handlersRef.current.set(type, new Set());
    }
    handlersRef.current.get(type)!.add(handler);
    return () => {
      handlersRef.current.get(type)?.delete(handler);
    };
  }, []);

  const onTrainUpdate = useCallback((callback: (data: unknown) => void) => subscribe('train_update', callback), [subscribe]);
  const onAlert = useCallback((callback: (data: unknown) => void) => subscribe('alert', callback), [subscribe]);
  const onCongestionUpdate = useCallback((callback: (data: unknown) => void) => subscribe('congestion_update', callback), [subscribe]);

  return (
    <WebSocketContext.Provider value={{ isConnected, subscribeToTrain, unsubscribeFromTrain, onTrainUpdate, onAlert, onCongestionUpdate }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}