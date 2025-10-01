import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import io, { Socket } from 'socket.io-client';
import { API_BASE_URL } from '../config/api';
import { supabase } from '../lib/supabase';

interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  error: string | null;
  userId: string | null;
  setUserId: (userId: string | null) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      return;
    }

    console.log('🔌 Initializing WebSocket connection...');
    console.log('API_BASE_URL:', API_BASE_URL);
    console.log('👤 User ID:', userId);
    
    // Create socket connection 
    const newSocket = io(API_BASE_URL, {
      transports: ['websocket', 'polling'],
      timeout: 10000,              // Increased timeout
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      forceNew: true,               // Force new connection
    });

    setSocket(newSocket);

    // Connection events
    newSocket.on('connect', async () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
      setError(null);
      
      // Get Supabase session token for authentication
      try {
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          console.error('Error getting Supabase session:', sessionError);
          setError('Failed to get authentication session');
          return;
        }

        if (session?.access_token && session?.user?.id) {
          console.log('🔐 Authenticating WebSocket with token...');
          // Authenticate with the server using Supabase token
          newSocket.emit('authenticate', {
            userId: session.user.id,
            token: session.access_token
          });
        } else {
          console.warn('No Supabase session token available for WebSocket authentication');
          setError('No authentication token available - please log in');
        }
      } catch (authError) {
        console.error('Authentication error:', authError);
        setError('Authentication failed');
      }
    });

    newSocket.on('disconnect', () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);
    });

    newSocket.on('connect_error', (err) => {
      console.error('❌ WebSocket connection error:', err);
      setError('Failed to connect to WebSocket service');
      setIsConnected(false);
    });

    // Authentication events
    newSocket.on('authenticated', (data) => {
      console.log('🔐 WebSocket authenticated:', data);
    });

    newSocket.on('auth_error', (err) => {
      console.error('❌ WebSocket auth error:', err);
      setError('WebSocket authentication failed');
    });

    // Cleanup on unmount or userId change
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      newSocket.disconnect();
      setSocket(null);
      setIsConnected(false);
      setError(null);
    };
  }, [userId]);

  const value: WebSocketContextType = {
    socket,
    isConnected,
    error,
    userId,
    setUserId,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}
