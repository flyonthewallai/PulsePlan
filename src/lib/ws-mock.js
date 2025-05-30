// Mock WebSocket implementation for React Native
// This prevents @supabase/realtime-js from trying to import Node.js modules

export default class MockWebSocket {
  constructor() {
    console.log('MockWebSocket: Created (realtime disabled for React Native)');
  }

  connect() {
    console.log('MockWebSocket: Connect called (no-op)');
  }

  disconnect() {
    console.log('MockWebSocket: Disconnect called (no-op)');
  }

  send() {
    console.log('MockWebSocket: Send called (no-op)');
  }

  addEventListener() {
    console.log('MockWebSocket: addEventListener called (no-op)');
  }

  removeEventListener() {
    console.log('MockWebSocket: removeEventListener called (no-op)');
  }
}

// Export as both default and named export for compatibility
export { MockWebSocket };
export const WebSocket = MockWebSocket;
