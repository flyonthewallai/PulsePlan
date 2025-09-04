import { Image } from 'react-native';
import { Asset } from 'expo-asset';

// Define all image assets for preloading
export const IMAGE_ASSETS = {
  // App icons
  icon: require('@/assets/images/icon.png'),
  pulselogo: require('@/assets/images/pulselogo.png'),
  
  // Integration icons
  applecalendar: require('@/assets/images/applecalendar.png'),
  applecontacts: require('@/assets/images/applecontacts.webp'),
  canvas: require('@/assets/images/canvas.png'),
  gmail: require('@/assets/images/gmail.png'),
  googlecalendar: require('@/assets/images/googlecalendar.png'),
  googlecontacts: require('@/assets/images/googlecontacts.webp'),
  notion: require('@/assets/images/notion.png'),
} as const;

// Cache for preloaded images
const imageCache = new Map<string, any>();

class ImageCacheService {
  private isInitialized = false;
  private preloadPromise: Promise<void> | null = null;

  /**
   * Initialize the image cache by preloading all images
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    if (this.preloadPromise) {
      return this.preloadPromise;
    }

    this.preloadPromise = this.preloadAllImages();
    await this.preloadPromise;
    this.isInitialized = true;
  }

  /**
   * Preload all images defined in IMAGE_ASSETS
   */
  private async preloadAllImages(): Promise<void> {
    console.log('🖼️ Preloading images...');
    
    const preloadPromises = Object.entries(IMAGE_ASSETS).map(async ([key, asset]) => {
      try {
        // Preload the image
        await Asset.loadAsync(asset);
        
        // Store in cache
        imageCache.set(key, asset);
        
        console.log(`✅ Preloaded: ${key}`);
      } catch (error) {
        console.error(`❌ Failed to preload ${key}:`, error);
      }
    });

    await Promise.all(preloadPromises);
    console.log('🎉 All images preloaded successfully');
  }

  /**
   * Get a cached image asset
   */
  getImage(key: keyof typeof IMAGE_ASSETS): any {
    if (!this.isInitialized) {
      console.warn('ImageCache not initialized, returning direct asset');
      return IMAGE_ASSETS[key];
    }
    
    return imageCache.get(key) || IMAGE_ASSETS[key];
  }

  /**
   * Check if an image is cached
   */
  isCached(key: keyof typeof IMAGE_ASSETS): boolean {
    return imageCache.has(key);
  }

  /**
   * Get cache status
   */
  getStatus(): { isInitialized: boolean; cachedCount: number; totalCount: number } {
    return {
      isInitialized: this.isInitialized,
      cachedCount: imageCache.size,
      totalCount: Object.keys(IMAGE_ASSETS).length,
    };
  }

  /**
   * Clear the cache (useful for memory management)
   */
  clearCache(): void {
    imageCache.clear();
    this.isInitialized = false;
    this.preloadPromise = null;
  }
}

// Export singleton instance
export const imageCacheService = new ImageCacheService();

// Export the assets for direct use if needed
export { IMAGE_ASSETS }; 