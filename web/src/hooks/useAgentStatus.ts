import { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

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
  const { socket, isConnected, error } = useWebSocket();

  useEffect(() => {
    if (!socket || !isConnected || !userId) {
      return;
    }

    console.log('📊 Setting up agent status listeners on shared WebSocket...');

    // Agent status events (using the already authenticated shared socket)
    socket.on('agent_status', (data: AgentStatus) => {
      console.log('📊 Initial agent status:', data);
      setStatus(data);
    });

    socket.on('agent_status_update', (data: AgentStatusUpdate) => {
      console.log('🔄 Agent status update:', data);
      setStatus(data.status);
    });

    // Cleanup on unmount - remove event listeners only
    return () => {
      console.log('🧹 Cleaning up agent status listeners');
      socket.off('agent_status');
      socket.off('agent_status_update');
    };
  }, [socket, isConnected, userId]);

  // Method to manually refresh status
  const refreshStatus = () => {
    if (socket && isConnected) {
      socket.emit('get_agent_status');
    }
  };

  return {
    status,
    isConnected,
    error,
    refreshStatus,
  };
};

