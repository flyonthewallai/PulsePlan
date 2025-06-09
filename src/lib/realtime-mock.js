// Mock implementation of @supabase/realtime-js for React Native compatibility
// This prevents WebSocket-related errors while providing expected APIs

class MockRealtimeClient {
  constructor(endpointURL, options = {}) {
    this.endpointURL = endpointURL;
    this.options = options;
    this.channels = [];
    this.connected = false;
    console.log(
      'MockRealtimeClient: Created (realtime disabled for React Native)'
    );
  }

  connect() {
    console.log('MockRealtimeClient: Connect called (no-op)');
    this.connected = true;
    return Promise.resolve();
  }

  disconnect() {
    console.log('MockRealtimeClient: Disconnect called (no-op)');
    this.connected = false;
    return Promise.resolve();
  }

  channel(topic, params = {}) {
    console.log('MockRealtimeClient: Channel created for topic:', topic);
    const channel = new MockRealtimeChannel(topic, params, this);
    this.channels.push(channel);
    return channel;
  }

  removeChannel(channel) {
    console.log('MockRealtimeClient: Remove channel called (no-op)');
    const index = this.channels.indexOf(channel);
    if (index > -1) {
      this.channels.splice(index, 1);
    }
    return Promise.resolve('ok');
  }

  removeAllChannels() {
    console.log('MockRealtimeClient: Remove all channels called (no-op)');
    this.channels = [];
    return Promise.resolve('ok');
  }

  getChannels() {
    return this.channels;
  }
}

class MockRealtimeChannel {
  constructor(topic, params = {}, socket = null) {
    this.topic = topic;
    this.params = params;
    this.socket = socket;
    this.state = 'closed';
    this.bindings = [];
    console.log('MockRealtimeChannel: Created for topic:', topic);
  }

  subscribe(callback) {
    console.log('MockRealtimeChannel: Subscribe called (no-op)');
    this.state = 'joined';
    if (callback) {
      // Simulate successful subscription
      setTimeout(() => callback('SUBSCRIBED', null), 0);
    }
    return {
      unsubscribe: () => this.unsubscribe(),
    };
  }

  unsubscribe() {
    console.log('MockRealtimeChannel: Unsubscribe called (no-op)');
    this.state = 'closed';
    return Promise.resolve('ok');
  }

  on(type, filter, callback) {
    console.log('MockRealtimeChannel: Event listener added for:', type);
    this.bindings.push({ type, filter, callback });
    return this;
  }

  off(type, filter) {
    console.log('MockRealtimeChannel: Event listener removed for:', type);
    this.bindings = this.bindings.filter(
      (binding) => binding.type !== type || binding.filter !== filter
    );
    return this;
  }

  send(payload) {
    console.log('MockRealtimeChannel: Send called (no-op)');
    return Promise.resolve('ok');
  }
}

// Constants that @supabase/realtime-js exports
const REALTIME_POSTGRES_CHANGES_LISTEN_EVENT = {
  ALL: '*',
  INSERT: 'INSERT',
  UPDATE: 'UPDATE',
  DELETE: 'DELETE',
};

const REALTIME_LISTEN_TYPES = {
  POSTGRES_CHANGES: 'postgres_changes',
  BROADCAST: 'broadcast',
  PRESENCE: 'presence',
};

const REALTIME_SUBSCRIBE_STATES = {
  SUBSCRIBED: 'SUBSCRIBED',
  TIMED_OUT: 'TIMED_OUT',
  CLOSED: 'CLOSED',
  CHANNEL_ERROR: 'CHANNEL_ERROR',
};

// Export all the expected exports from @supabase/realtime-js
export { MockRealtimeClient as RealtimeClient };
export { MockRealtimeChannel as RealtimeChannel };
export { REALTIME_POSTGRES_CHANGES_LISTEN_EVENT };
export { REALTIME_LISTEN_TYPES };
export { REALTIME_SUBSCRIBE_STATES };

// Default export
export default MockRealtimeClient;
