import NodeCache from 'node-cache';
import { LRUCache } from 'lru-cache';
import redisClient, { isRedisHealthy } from '../config/redis';

// Cache configuration
export const CACHE_CONFIG = {
  // TTL values in seconds
  TTL: {
    USER_INFO: 5 * 60, // 5 minutes - user profile data changes infrequently
    USER_CONNECTED_ACCOUNTS: 10 * 60, // 10 minutes - OAuth tokens
    USER_PREFERENCES: 15 * 60, // 15 minutes - settings change rarely  
    USER_SUBSCRIPTION: 30 * 60, // 30 minutes - subscription status
    CALENDAR_EVENTS: 2 * 60, // 2 minutes - calendar data changes frequently
    TASKS: 3 * 60, // 3 minutes - tasks change frequently
    USER_SESSION: 60 * 60, // 1 hour - session data
    HEALTH_CHECK: 30, // 30 seconds - health status
  },
  
  // Memory cache limits
  MEMORY: {
    MAX_ITEMS: 1000,
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
  },
  
  // Cache key prefixes
  KEYS: {
    USER_INFO: 'user:info',
    USER_CONNECTED_ACCOUNTS: 'user:accounts', 
    USER_PREFERENCES: 'user:prefs',
    USER_SUBSCRIPTION: 'user:sub',
    CALENDAR_EVENTS: 'calendar:events',
    TASKS: 'tasks',
    USER_SESSION: 'session',
    HEALTH: 'health',
  }
};

// Cache statistics for monitoring
interface CacheStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  errors: number;
}

export class CacheService {
  private memoryCache: LRUCache<string, any>;
  private nodeCache: NodeCache;
  private stats: { memory: CacheStats; redis: CacheStats };
  private isRedisAvailable: boolean = true;

  constructor() {
    // Initialize in-memory cache with LRU eviction
    this.memoryCache = new LRUCache({
      max: CACHE_CONFIG.MEMORY.MAX_ITEMS,
      maxSize: CACHE_CONFIG.MEMORY.MAX_SIZE,
      sizeCalculation: (value) => JSON.stringify(value).length,
      ttl: 5 * 60 * 1000, // 5 minutes default TTL
    });

    // Initialize NodeCache for simple TTL management
    this.nodeCache = new NodeCache({
      stdTTL: 5 * 60, // 5 minutes default
      checkperiod: 60, // Check for expired keys every minute
      deleteOnExpire: true,
    });

    // Initialize statistics
    this.stats = {
      memory: { hits: 0, misses: 0, sets: 0, deletes: 0, errors: 0 },
      redis: { hits: 0, misses: 0, sets: 0, deletes: 0, errors: 0 }
    };

    // Monitor Redis connection
    this.monitorRedis();
  }

  /**
   * Monitor Upstash Redis availability
   */
  private monitorRedis(): void {
    // Check Upstash Redis health periodically
    const checkHealth = async () => {
      this.isRedisAvailable = await isRedisHealthy();
      if (!this.isRedisAvailable) {
        console.log('❌ Cache Service: Upstash Redis unavailable, using memory cache only');
      }
    };

    // Initial health check
    checkHealth();

    // Periodic health checks every 30 seconds
    setInterval(checkHealth, 30000);
  }

  /**
   * Generate cache key with proper namespace
   */
  private generateKey(prefix: string, identifier: string, suffix?: string): string {
    const key = `pulseplan:${prefix}:${identifier}`;
    return suffix ? `${key}:${suffix}` : key;
  }

  /**
   * Get data from cache (memory first, then Redis)
   */
  async get<T>(prefix: string, identifier: string, suffix?: string): Promise<T | null> {
    const key = this.generateKey(prefix, identifier, suffix);
    
    try {
      // Try memory cache first
      const memoryResult = this.memoryCache.get(key) || this.nodeCache.get<T>(key);
      if (memoryResult !== undefined) {
        this.stats.memory.hits++;
        console.log(`📝 Cache HIT (Memory): ${key}`);
        return memoryResult;
      }
      this.stats.memory.misses++;

      // Try Upstash Redis if available
      if (this.isRedisAvailable) {
        const redisResult = await redisClient.get(key);
        if (redisResult && redisResult !== null) {
          let parsedResult: T;
          
          // Handle both string and already parsed responses from Upstash
          if (typeof redisResult === 'string') {
            parsedResult = JSON.parse(redisResult) as T;
          } else {
            parsedResult = redisResult as T;
          }
          
          // Populate memory cache with Redis result
          this.memoryCache.set(key, parsedResult);
          this.stats.redis.hits++;
          console.log(`📝 Cache HIT (Upstash Redis): ${key}`);
          return parsedResult;
        }
        this.stats.redis.misses++;
      }

      console.log(`📝 Cache MISS: ${key}`);
      return null;
    } catch (error) {
      console.error(`❌ Cache GET error for key ${key}:`, error);
      this.stats.memory.errors++;
      return null;
    }
  }

  /**
   * Set data in cache (both memory and Redis)
   */
  async set(
    prefix: string, 
    identifier: string, 
    data: any, 
    ttlSeconds?: number,
    suffix?: string
  ): Promise<void> {
    const key = this.generateKey(prefix, identifier, suffix);
    const ttl = ttlSeconds || 300; // 5 minutes default
    
    try {
      // Set in memory cache
      this.memoryCache.set(key, data, { ttl: ttl * 1000 });
      this.nodeCache.set(key, data, ttl);
      this.stats.memory.sets++;

      // Set in Upstash Redis if available
      if (this.isRedisAvailable) {
        await redisClient.setex(key, ttl, JSON.stringify(data));
        this.stats.redis.sets++;
      }

      console.log(`📝 Cache SET: ${key} (TTL: ${ttl}s)`);
    } catch (error) {
      console.error(`❌ Cache SET error for key ${key}:`, error);
      this.stats.memory.errors++;
    }
  }

  /**
   * Delete from cache
   */
  async delete(prefix: string, identifier: string, suffix?: string): Promise<void> {
    const key = this.generateKey(prefix, identifier, suffix);
    
    try {
      // Delete from memory
      this.memoryCache.delete(key);
      this.nodeCache.del(key);
      this.stats.memory.deletes++;

      // Delete from Upstash Redis if available
      if (this.isRedisAvailable) {
        await redisClient.del(key);
        this.stats.redis.deletes++;
      }

      console.log(`📝 Cache DELETE: ${key}`);
    } catch (error) {
      console.error(`❌ Cache DELETE error for key ${key}:`, error);
      this.stats.memory.errors++;
    }
  }

  /**
   * Delete all cache entries for a user (useful for logout/data changes)
   */
  async deleteUserCache(userId: string): Promise<void> {
    const patterns = [
      this.generateKey(CACHE_CONFIG.KEYS.USER_INFO, userId),
      this.generateKey(CACHE_CONFIG.KEYS.USER_CONNECTED_ACCOUNTS, userId),
      this.generateKey(CACHE_CONFIG.KEYS.USER_PREFERENCES, userId),
      this.generateKey(CACHE_CONFIG.KEYS.USER_SUBSCRIPTION, userId),
      this.generateKey(CACHE_CONFIG.KEYS.TASKS, userId),
    ];

    for (const pattern of patterns) {
      await this.delete('', '', pattern);
    }
    
    console.log(`📝 Cache: Cleared all data for user ${userId}`);
  }

  /**
   * Invalidate cache by pattern (Upstash Redis only, memory cache uses TTL)
   */
  async invalidatePattern(pattern: string): Promise<void> {
    if (!this.isRedisAvailable) return;

    try {
      const keys = await redisClient.keys(`pulseplan:${pattern}*`);
      if (keys.length > 0) {
        await redisClient.del(...keys);
        console.log(`📝 Cache: Invalidated ${keys.length} keys matching pattern: ${pattern}`);
      }
    } catch (error) {
      console.error(`❌ Cache pattern invalidation error:`, error);
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): typeof this.stats & { redisAvailable: boolean } {
    return {
      ...this.stats,
      redisAvailable: this.isRedisAvailable
    };
  }

  /**
   * Reset cache statistics
   */
  resetStats(): void {
    this.stats = {
      memory: { hits: 0, misses: 0, sets: 0, deletes: 0, errors: 0 },
      redis: { hits: 0, misses: 0, sets: 0, deletes: 0, errors: 0 }
    };
  }

  /**
   * Health check for cache service
   */
  async healthCheck(): Promise<{
    memory: boolean;
    redis: boolean;
    stats: { memory: CacheStats; redis: CacheStats };
  }> {
    let redisHealth = false;
    
    if (this.isRedisAvailable) {
      try {
        const result = await redisClient.ping();
        redisHealth = !!result;
      } catch (error) {
        redisHealth = false;
      }
    }

    return {
      memory: true, // Memory cache is always available
      redis: redisHealth,
      stats: this.stats
    };
  }

  /**
   * Clear all caches
   */
  async clearAll(): Promise<void> {
    // Clear memory caches
    this.memoryCache.clear();
    this.nodeCache.flushAll();
    
    // Clear Upstash Redis if available
    if (this.isRedisAvailable) {
      const keys = await redisClient.keys('pulseplan:*');
      if (keys.length > 0) {
        await redisClient.del(...keys);
      }
    }
    
    console.log('📝 Cache: Cleared all caches');
  }
}

// Export singleton instance
export const cacheService = new CacheService(); 