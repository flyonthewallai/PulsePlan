import { RateLimiter } from '../../src/types/scheduler';
import { logger } from './logger';

class RequestRateLimiter implements RateLimiter {
  private requestTimes: number[] = [];
  private readonly maxRequestsPerSecond: number;
  private readonly windowSizeMs: number;

  constructor(maxRequestsPerSecond: number = 5) {
    this.maxRequestsPerSecond = maxRequestsPerSecond;
    this.windowSizeMs = 1000; // 1 second
  }

  async wait(): Promise<void> {
    const now = Date.now();
    
    // Remove old requests outside the window
    this.requestTimes = this.requestTimes.filter(
      time => now - time < this.windowSizeMs
    );

    // If we're at the limit, wait until we can make another request
    if (this.requestTimes.length >= this.maxRequestsPerSecond) {
      const oldestRequest = Math.min(...this.requestTimes);
      const waitTime = this.windowSizeMs - (now - oldestRequest);
      
      if (waitTime > 0) {
        logger.logRateLimit(waitTime);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    // Record this request
    this.requestTimes.push(Date.now());
  }

  // Get current request count in the window
  getCurrentRequestCount(): number {
    const now = Date.now();
    this.requestTimes = this.requestTimes.filter(
      time => now - time < this.windowSizeMs
    );
    return this.requestTimes.length;
  }

  // Reset the rate limiter
  reset(): void {
    this.requestTimes = [];
  }
}

export const rateLimiter = new RequestRateLimiter(5); // 5 requests per second 