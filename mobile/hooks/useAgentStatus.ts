import { useState, useEffect, useRef } from 'react';
import io, { Socket } from 'socket.io-client';
import { API_BASE_URL } from '../config/api';

export interface AgentStatus {
  userId: string;
  currentTool?: string;
  status: 'idle' | 'active' | 'error';
  lastUpdate: string;
  toolHistory: Array<{
    tool: string;
    status: string;
    timestamp: string;
    message?: string;
  }>;
}

export interface AgentStatusUpdate {
  eventType: 'status_update' | 'tool_change' | 'agent_idle' | 'agent_error';
  status: AgentStatus;
  update: {
    tool: string;
    status: string;
    message?: string;
    timestamp: string;
  };
  timestamp: string;
}

export const useAgentStatus = (userId: string | null) => {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!userId) {
      return;
    }

    console.log('🔌 Connecting to agent status WebSocket...');

    // Create socket connection
    const socket = io(API_BASE_URL, {
      transports: ['websocket', 'polling'],
      timeout: 5000,
    });

    socketRef.current = socket;

    // Connection events
    socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
      setError(null);

      // Authenticate with the server
      socket.emit('authenticate', { userId });
    });

    socket.on('disconnect', () => {
      console.log('🔌 WebSocket disconnected');
      setIsConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.error('❌ WebSocket connection error:', err);
      setError('Failed to connect to status service');
      setIsConnected(false);
    });

    // Authentication events
    socket.on('authenticated', (data) => {
      console.log('🔐 WebSocket authenticated:', data);
    });

    socket.on('auth_error', (err) => {
      console.error('❌ WebSocket auth error:', err);
      setError('Authentication failed');
    });

    // Agent status events
    socket.on('agent_status', (data: AgentStatus) => {
      console.log('📊 Initial agent status:', data);
      setStatus(data);
    });

    socket.on('agent_status_update', (data: AgentStatusUpdate) => {
      console.log('🔄 Agent status update:', data);
      setStatus(data.status);
    });

    // Cleanup on unmount
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      socket.disconnect();
      socketRef.current = null;
    };
  }, [userId]);

  // Method to manually refresh status
  const refreshStatus = () => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('get_agent_status');
    }
  };

  return {
    status,
    isConnected,
    error,
    refreshStatus,
  };
}; 