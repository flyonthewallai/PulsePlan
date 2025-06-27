import { Server as HttpServer } from 'http';
import { Server as SocketIOServer, Socket } from 'socket.io';
import { agentStatusService } from './agentStatusService';
import { UserAgentStatus } from '../types/agentStatus';

interface AuthenticatedSocket extends Socket {
  userId?: string;
  userEmail?: string;
}

class WebSocketService {
  private io: SocketIOServer | null = null;
  private connectedUsers: Map<string, Set<string>> = new Map(); // userId -> Set of socket IDs

  /**
   * Initialize WebSocket server
   */
  initialize(httpServer: HttpServer): void {
    this.io = new SocketIOServer(httpServer, {
      cors: {
        origin: "*", // Allow all origins for development
        methods: ["GET", "POST"],
        credentials: true,
      },
      transports: ['websocket', 'polling'],
    });

    this.setupEventHandlers();
    this.setupAgentStatusListener();
    
    console.log('🔌 WebSocket service initialized');
  }

  /**
   * Setup Socket.IO event handlers
   */
  private setupEventHandlers(): void {
    if (!this.io) return;

    this.io.on('connection', (socket: AuthenticatedSocket) => {
      console.log(`🔗 Client connected: ${socket.id}`);

      // Handle authentication
      socket.on('authenticate', (data: { userId: string; userEmail?: string }) => {
        const { userId, userEmail } = data;
        
        if (!userId) {
          socket.emit('auth_error', { error: 'User ID is required' });
          return;
        }

        // Store user info on socket
        socket.userId = userId;
        socket.userEmail = userEmail;

        // Track connected user
        if (!this.connectedUsers.has(userId)) {
          this.connectedUsers.set(userId, new Set());
        }
        this.connectedUsers.get(userId)!.add(socket.id);

        // Send current agent status
        const currentStatus = agentStatusService.getUserStatus(userId);
        socket.emit('agent_status', currentStatus || {
          userId,
          status: 'idle',
          currentTool: null,
          lastUpdate: new Date().toISOString(),
          toolHistory: [],
        });

        socket.emit('authenticated', { userId, timestamp: new Date().toISOString() });
        console.log(`✅ User authenticated: ${userId} (${socket.id})`);
      });

      // Handle agent status requests
      socket.on('get_agent_status', () => {
        if (!socket.userId) {
          socket.emit('auth_error', { error: 'Not authenticated' });
          return;
        }

        const status = agentStatusService.getUserStatus(socket.userId);
        socket.emit('agent_status', status);
      });

      // Handle disconnection
      socket.on('disconnect', () => {
        console.log(`🔌 Client disconnected: ${socket.id}`);
        
        if (socket.userId) {
          const userSockets = this.connectedUsers.get(socket.userId);
          if (userSockets) {
            userSockets.delete(socket.id);
            if (userSockets.size === 0) {
              this.connectedUsers.delete(socket.userId);
              console.log(`👋 User fully disconnected: ${socket.userId}`);
            }
          }
        }
      });

      // Handle errors
      socket.on('error', (error) => {
        console.error(`❌ Socket error for ${socket.id}:`, error);
      });
    });
  }

  /**
   * Setup listener for agent status updates
   */
  private setupAgentStatusListener(): void {
    agentStatusService.on('statusUpdate', (data: {
      userId: string;
      eventType: string;
      userStatus: UserAgentStatus;
      update: any;
    }) => {
      this.broadcastToUser(data.userId, 'agent_status_update', {
        eventType: data.eventType,
        status: data.userStatus,
        update: data.update,
        timestamp: new Date().toISOString(),
      });
    });
  }

  /**
   * Broadcast message to all sockets for a specific user
   */
  private broadcastToUser(userId: string, event: string, data: any): void {
    const userSockets = this.connectedUsers.get(userId);
    if (!userSockets || userSockets.size === 0) {
      return; // User not connected
    }

    userSockets.forEach(socketId => {
      const socket = this.io?.sockets.sockets.get(socketId);
      if (socket) {
        socket.emit(event, data);
      }
    });

    console.log(`📡 Broadcasted ${event} to ${userSockets.size} socket(s) for user ${userId}`);
  }

  /**
   * Broadcast message to all connected clients
   */
  broadcastToAll(event: string, data: any): void {
    if (!this.io) return;
    
    this.io.emit(event, data);
    console.log(`📢 Broadcasted ${event} to all connected clients`);
  }

  /**
   * Send message to specific user
   */
  sendToUser(userId: string, event: string, data: any): void {
    this.broadcastToUser(userId, event, data);
  }

  /**
   * Get connection statistics
   */
  getStats(): {
    totalConnections: number;
    authenticatedUsers: number;
    connectionsByUser: Record<string, number>;
  } {
    const connectionsByUser: Record<string, number> = {};
    
    for (const [userId, sockets] of this.connectedUsers) {
      connectionsByUser[userId] = sockets.size;
    }

    return {
      totalConnections: this.io?.sockets.sockets.size || 0,
      authenticatedUsers: this.connectedUsers.size,
      connectionsByUser,
    };
  }

  /**
   * Get Socket.IO instance (for advanced usage)
   */
  getIO(): SocketIOServer | null {
    return this.io;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService(); 