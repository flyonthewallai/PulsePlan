import { Router, Request, Response } from 'express';
import { authenticate } from '../middleware/authenticate';
import { cacheService } from '../services/cacheService';
import { invalidateCache } from '../middleware/cacheInvalidation';

const router = Router();

interface AuthenticatedRequest extends Request {
  user?: { id: string; email?: string };
  body: any;
  params: any;
}

/**
 * GET /cache/stats - Get cache statistics (admin only in production)
 */
router.get('/stats', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const stats = cacheService.getStats();
    const health = await cacheService.healthCheck();
    
    res.json({
      stats,
      health,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error getting cache stats:', error);
    res.status(500).json({ error: 'Failed to get cache statistics' });
  }
});

/**
 * POST /cache/clear - Clear all cache (admin only)
 */
router.post('/clear', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    // In production, you might want to add admin role check here
    if (process.env.NODE_ENV === 'production') {
      // Add admin check logic here
      // const isAdmin = await checkAdminRole(req.user?.id);
      // if (!isAdmin) {
      //   return res.status(403).json({ error: 'Admin access required' });
      // }
    }
    
    await cacheService.clearAll();
    res.json({ 
      message: 'All caches cleared successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error clearing cache:', error);
    res.status(500).json({ error: 'Failed to clear cache' });
  }
});

/**
 * DELETE /cache/user/:userId - Clear cache for specific user
 */
router.delete('/user/:userId', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { userId } = req.params;
    const requestingUserId = req.user?.id;
    
    // Users can only clear their own cache, unless admin
    if (userId !== requestingUserId) {
      // In production, add admin role check
      if (process.env.NODE_ENV === 'production') {
        return res.status(403).json({ error: 'Can only clear your own cache' });
      }
    }
    
    await invalidateCache.allUserCache(userId);
    res.json({ 
      message: `Cache cleared for user ${userId}`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error clearing user cache:', error);
    res.status(500).json({ error: 'Failed to clear user cache' });
  }
});

/**
 * POST /cache/invalidate - Manual cache invalidation for specific data types
 */
router.post('/invalidate', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { userId, cacheTypes } = req.body;
    const requestingUserId = req.user?.id;
    
    if (!userId || !cacheTypes || !Array.isArray(cacheTypes)) {
      return res.status(400).json({ 
        error: 'userId and cacheTypes array are required' 
      });
    }
    
    // Users can only invalidate their own cache
    if (userId !== requestingUserId) {
      return res.status(403).json({ error: 'Can only invalidate your own cache' });
    }
    
    const validCacheTypes = [
      'userInfo', 
      'userAccounts', 
      'userSubscription', 
      'userPreferences', 
      'userTasks', 
      'calendarEvents'
    ];
    
    const invalidCacheTypes = cacheTypes.filter((type: string) => 
      !validCacheTypes.includes(type)
    );
    
    if (invalidCacheTypes.length > 0) {
      return res.status(400).json({ 
        error: `Invalid cache types: ${invalidCacheTypes.join(', ')}`,
        validTypes: validCacheTypes
      });
    }
    
    const results: { type: string; success: boolean; error?: string }[] = [];
    
    for (const cacheType of cacheTypes) {
      try {
        await invalidateCache[cacheType as keyof typeof invalidateCache](userId);
        results.push({ type: cacheType, success: true });
      } catch (error) {
        results.push({ 
          type: cacheType, 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
    
    res.json({
      message: 'Cache invalidation completed',
      results,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error invalidating cache:', error);
    res.status(500).json({ error: 'Failed to invalidate cache' });
  }
});

/**
 * GET /cache/health - Cache health check
 */
router.get('/health', async (req: Request, res: Response) => {
  try {
    const health = await cacheService.healthCheck();
    const stats = cacheService.getStats();
    const httpStatus = health.memory && health.redis ? 200 : 503;
    
    const totalRequests = stats.memory.hits + stats.memory.misses + stats.redis.hits + stats.redis.misses;
    const totalHits = stats.memory.hits + stats.redis.hits;
    const hitRatio = totalRequests > 0 ? ((totalHits / totalRequests) * 100).toFixed(2) : '0';
    
    res.status(httpStatus).json({
      ...health,
      provider: 'Upstash Redis',
      environment: process.env.NODE_ENV || 'development',
      redisUrl: process.env.UPSTASH_REDIS_REST_URL ? 
        process.env.UPSTASH_REDIS_REST_URL.replace(/https:\/\/.*@/, 'https://***@') : 
        'Not configured',
      performance: {
        totalHits,
        totalMisses: stats.memory.misses + stats.redis.misses,
        hitRatio: hitRatio + '%',
        memoryHits: stats.memory.hits,
        redisHits: stats.redis.hits
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error checking cache health:', error);
    res.status(503).json({ 
      memory: false,
      redis: false,
      provider: 'Upstash Redis',
      error: 'Cache health check failed',
      timestamp: new Date().toISOString()
    });
  }
});

export default router; 