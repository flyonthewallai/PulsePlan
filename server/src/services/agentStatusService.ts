import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import { 
  AgentStatusUpdate, 
  AgentStatusQueueItem, 
  UserAgentStatus, 
  AgentStatusEventType 
} from '../types/agentStatus';

class AgentStatusService extends EventEmitter {
  private statusQueue: Map<string, AgentStatusQueueItem[]> = new Map();
  private userStatuses: Map<string, UserAgentStatus> = new Map();
  private processingQueue: Set<string> = new Set();
  private readonly maxQueueSize = 50;
  private readonly maxHistorySize = 20;
  private readonly processingDelay = 100; // ms between queue processing

  constructor() {
    super();
    this.setMaxListeners(100); // Allow many WebSocket connections
  }

  /**
   * Add a status update to the queue for processing
   */
  async addStatusUpdate(update: AgentStatusUpdate): Promise<void> {
    const { userId } = update;
    
    // Create queue item
    const queueItem: AgentStatusQueueItem = {
      ...update,
      id: uuidv4(),
      timestamp: update.timestamp || new Date().toISOString(),
      retryCount: 0,
    };

    // Initialize user queue if needed
    if (!this.statusQueue.has(userId)) {
      this.statusQueue.set(userId, []);
    }

    const userQueue = this.statusQueue.get(userId)!;
    
    // Add to queue (with size limit)
    userQueue.push(queueItem);
    if (userQueue.length > this.maxQueueSize) {
      userQueue.shift(); // Remove oldest item
    }

    console.log(`📊 Agent status queued for user ${userId}: ${update.tool} - ${update.status}`);

    // Process queue if not already processing
    if (!this.processingQueue.has(userId)) {
      this.processUserQueue(userId);
    }
  }

  /**
   * Process the status queue for a specific user
   */
  private async processUserQueue(userId: string): Promise<void> {
    if (this.processingQueue.has(userId)) {
      return; // Already processing
    }

    this.processingQueue.add(userId);
    
    try {
      const userQueue = this.statusQueue.get(userId);
      if (!userQueue || userQueue.length === 0) {
        return;
      }

      while (userQueue.length > 0) {
        const item = userQueue.shift()!;
        await this.processStatusUpdate(item);
        
        // Small delay to prevent overwhelming
        if (userQueue.length > 0) {
          await new Promise(resolve => setTimeout(resolve, this.processingDelay));
        }
      }
    } catch (error) {
      console.error(`Error processing status queue for user ${userId}:`, error);
    } finally {
      this.processingQueue.delete(userId);
    }
  }

  /**
   * Process a single status update
   */
  private async processStatusUpdate(item: AgentStatusQueueItem): Promise<void> {
    const { userId, tool, status, timestamp, message, metadata } = item;

    // Get or create user status
    let userStatus = this.userStatuses.get(userId);
    if (!userStatus) {
      userStatus = {
        userId,
        status: 'idle',
        lastUpdate: timestamp,
        toolHistory: [],
      };
      this.userStatuses.set(userId, userStatus);
    }

    // Update user status
    const previousTool = userStatus.currentTool;
    const previousStatus = userStatus.status;

    userStatus.currentTool = status === 'idle' ? undefined : tool;
    userStatus.status = status === 'completed' ? 'idle' : status;
    userStatus.lastUpdate = timestamp;

    // Add to history
    userStatus.toolHistory.unshift({
      tool,
      status,
      timestamp,
      message,
    });

    // Limit history size
    if (userStatus.toolHistory.length > this.maxHistorySize) {
      userStatus.toolHistory = userStatus.toolHistory.slice(0, this.maxHistorySize);
    }

    // Determine event type
    let eventType: AgentStatusEventType = 'status_update';
    if (previousTool !== tool && status === 'active') {
      eventType = 'tool_change';
    } else if (status === 'idle' && previousStatus !== 'idle') {
      eventType = 'agent_idle';
    } else if (status === 'error') {
      eventType = 'agent_error';
    }

    // Emit event for WebSocket broadcasting
    this.emit('statusUpdate', {
      userId,
      eventType,
      userStatus,
      update: item,
    });

    console.log(`🔄 Agent status updated for user ${userId}: ${tool} - ${status} (${eventType})`);
  }

  /**
   * Get current status for a user
   */
  getUserStatus(userId: string): UserAgentStatus | null {
    return this.userStatuses.get(userId) || null;
  }

  /**
   * Get all user statuses (for admin/debugging)
   */
  getAllUserStatuses(): Map<string, UserAgentStatus> {
    return new Map(this.userStatuses);
  }

  /**
   * Clear status for a user (e.g., when they disconnect)
   */
  clearUserStatus(userId: string): void {
    this.userStatuses.delete(userId);
    this.statusQueue.delete(userId);
    this.processingQueue.delete(userId);
    console.log(`🗑️ Cleared agent status for user ${userId}`);
  }

  /**
   * Get queue stats for monitoring
   */
  getQueueStats(): {
    totalUsers: number;
    totalQueuedItems: number;
    processingUsers: number;
    activeUsers: number;
  } {
    let totalQueuedItems = 0;
    let activeUsers = 0;

    for (const [userId, queue] of this.statusQueue) {
      totalQueuedItems += queue.length;
    }

    for (const [userId, status] of this.userStatuses) {
      if (status.status === 'active') {
        activeUsers++;
      }
    }

    return {
      totalUsers: this.userStatuses.size,
      totalQueuedItems,
      processingUsers: this.processingQueue.size,
      activeUsers,
    };
  }

  /**
   * Cleanup old statuses (run periodically)
   */
  cleanup(maxAgeHours: number = 24): void {
    const cutoffTime = new Date(Date.now() - maxAgeHours * 60 * 60 * 1000);
    let cleanedCount = 0;

    for (const [userId, status] of this.userStatuses) {
      if (new Date(status.lastUpdate) < cutoffTime) {
        this.clearUserStatus(userId);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      console.log(`🧹 Cleaned up ${cleanedCount} old agent statuses`);
    }
  }
}

// Export singleton instance
export const agentStatusService = new AgentStatusService();

// Start cleanup interval (every hour)
setInterval(() => {
  agentStatusService.cleanup();
}, 60 * 60 * 1000); 