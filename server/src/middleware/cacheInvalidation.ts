import { Request, Response, NextFunction } from 'express';
import { cacheService, CACHE_CONFIG } from '../services/cacheService';

interface AuthenticatedRequest extends Request {
  user?: { id: string; email?: string };
  body: any;
  params: any;
}

/**
 * Cache invalidation strategies for different data types
 */
export const CacheInvalidationStrategies = {
  /**
   * Invalidate user info cache when user profile is updated
   */
  invalidateUserInfo: (userId: string) => async () => {
    await cacheService.delete(CACHE_CONFIG.KEYS.USER_INFO, userId);
    console.log(`🗑️ Invalidated user info cache for user: ${userId}`);
  },

  /**
   * Invalidate user connected accounts cache
   */
  invalidateUserAccounts: (userId: string) => async () => {
    await cacheService.delete(CACHE_CONFIG.KEYS.USER_CONNECTED_ACCOUNTS, userId);
    console.log(`🗑️ Invalidated connected accounts cache for user: ${userId}`);
  },

  /**
   * Invalidate user subscription cache
   */
  invalidateUserSubscription: (userId: string) => async () => {
    await cacheService.delete(CACHE_CONFIG.KEYS.USER_SUBSCRIPTION, userId);
    console.log(`🗑️ Invalidated subscription cache for user: ${userId}`);
  },

  /**
   * Invalidate user preferences cache
   */
  invalidateUserPreferences: (userId: string) => async () => {
    await cacheService.delete(CACHE_CONFIG.KEYS.USER_PREFERENCES, userId);
    console.log(`🗑️ Invalidated preferences cache for user: ${userId}`);
  },

  /**
   * Invalidate user tasks cache
   */
  invalidateUserTasks: (userId: string) => async () => {
    await cacheService.delete(CACHE_CONFIG.KEYS.TASKS, userId);
    console.log(`🗑️ Invalidated tasks cache for user: ${userId}`);
  },

  /**
   * Invalidate all user-related cache
   */
  invalidateAllUserCache: (userId: string) => async () => {
    await cacheService.deleteUserCache(userId);
    console.log(`🗑️ Invalidated all cache for user: ${userId}`);
  },

  /**
   * Invalidate calendar events cache
   */
  invalidateCalendarEvents: (userId: string) => async () => {
    await cacheService.delete(CACHE_CONFIG.KEYS.CALENDAR_EVENTS, userId);
    console.log(`🗑️ Invalidated calendar events cache for user: ${userId}`);
  }
};

/**
 * Middleware factory for cache invalidation
 */
export const createCacheInvalidationMiddleware = (
  strategy: (userId: string) => () => Promise<void>
) => {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    const userId = req.user?.id || req.body.userId || req.params.userId;
    
    if (!userId) {
      return next();
    }

    // Store original response methods
    const originalSend = res.send;
    const originalJson = res.json;

    // Override response methods to trigger cache invalidation on successful operations
    res.send = function(body: any) {
      // Only invalidate on successful operations (2xx status codes)
      if (res.statusCode >= 200 && res.statusCode < 300) {
        strategy(userId)().catch(error => {
          console.error('Cache invalidation error:', error);
        });
      }
      return originalSend.call(this, body);
    };

    res.json = function(body: any) {
      // Only invalidate on successful operations (2xx status codes)
      if (res.statusCode >= 200 && res.statusCode < 300) {
        strategy(userId)().catch(error => {
          console.error('Cache invalidation error:', error);
        });
      }
      return originalJson.call(this, body);
    };

    next();
  };
};

/**
 * Pre-built middleware for common scenarios
 */
export const invalidateUserInfoCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateUserInfo
);

export const invalidateUserAccountsCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateUserAccounts
);

export const invalidateUserSubscriptionCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateUserSubscription
);

export const invalidateUserPreferencesCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateUserPreferences
);

export const invalidateUserTasksCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateUserTasks
);

export const invalidateAllUserCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateAllUserCache
);

export const invalidateCalendarEventsCache = createCacheInvalidationMiddleware(
  CacheInvalidationStrategies.invalidateCalendarEvents
);

/**
 * Manual cache invalidation utilities for use in controllers
 */
export const invalidateCache = {
  userInfo: (userId: string) => CacheInvalidationStrategies.invalidateUserInfo(userId)(),
  userAccounts: (userId: string) => CacheInvalidationStrategies.invalidateUserAccounts(userId)(),
  userSubscription: (userId: string) => CacheInvalidationStrategies.invalidateUserSubscription(userId)(),
  userPreferences: (userId: string) => CacheInvalidationStrategies.invalidateUserPreferences(userId)(),
  userTasks: (userId: string) => CacheInvalidationStrategies.invalidateUserTasks(userId)(),
  allUserCache: (userId: string) => CacheInvalidationStrategies.invalidateAllUserCache(userId)(),
  calendarEvents: (userId: string) => CacheInvalidationStrategies.invalidateCalendarEvents(userId)(),
};

/**
 * Webhook middleware for external system updates (e.g., Apple Pay notifications)
 */
export const handleWebhookCacheInvalidation = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  // This will be called after successful webhook processing
  // The webhook handler should set req.cacheInvalidation with user IDs and strategies
  const cacheInvalidation = (req as any).cacheInvalidation;
  
  if (cacheInvalidation) {
    for (const { userId, strategy } of cacheInvalidation) {
      try {
        await strategy(userId)();
      } catch (error) {
        console.error(`Webhook cache invalidation error for user ${userId}:`, error);
      }
    }
  }
  
  next();
}; 