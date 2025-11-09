import React, { useState, useEffect } from 'react';
import { Image, ImageProps, ActivityIndicator, View, StyleSheet } from 'react-native';
import { imageCacheService, IMAGE_ASSETS } from '@/services/imageCacheService';

interface CachedImageProps extends Omit<ImageProps, 'source'> {
  imageKey: keyof typeof IMAGE_ASSETS;
  fallbackSource?: any;
  showLoadingIndicator?: boolean;
  loadingIndicatorColor?: string;
  loadingIndicatorSize?: 'small' | 'large';
}

export const CachedImage: React.FC<CachedImageProps> = ({
  imageKey,
  fallbackSource,
  showLoadingIndicator = false,
  loadingIndicatorColor = '#007AFF',
  loadingIndicatorSize = 'small',
  style,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [imageSource, setImageSource] = useState<any>(null);

  useEffect(() => {
    const loadImage = async () => {
      try {
        setIsLoading(true);
        setHasError(false);

        // Get the cached image
        const cachedImage = imageCacheService.getImage(imageKey);
        setImageSource(cachedImage);

        // If cache is not initialized, wait for it
        if (!imageCacheService.isInitialized) {
          await imageCacheService.initialize();
          const finalImage = imageCacheService.getImage(imageKey);
          setImageSource(finalImage);
        }

        setIsLoading(false);
      } catch (error) {
        console.error(`Failed to load cached image ${imageKey}:`, error);
        setHasError(true);
        setIsLoading(false);
      }
    };

    loadImage();
  }, [imageKey]);

  // Show loading indicator if requested and loading
  if (isLoading && showLoadingIndicator) {
    return (
      <View style={[styles.loadingContainer, style]}>
        <ActivityIndicator 
          size={loadingIndicatorSize} 
          color={loadingIndicatorColor} 
        />
      </View>
    );
  }

  // Show fallback or error state
  if (hasError || !imageSource) {
    if (fallbackSource) {
      return <Image source={fallbackSource} style={style} {...props} />;
    }
    return null;
  }

  return (
    <Image
      source={imageSource}
      style={style}
      onLoad={() => setIsLoading(false)}
      onError={() => {
        setHasError(true);
        setIsLoading(false);
      }}
      {...props}
    />
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
});

// Export a hook for checking cache status
export const useImageCacheStatus = () => {
  const [status, setStatus] = useState(imageCacheService.getStatus());

  useEffect(() => {
    const checkStatus = () => {
      setStatus(imageCacheService.getStatus());
    };

    // Check status periodically
    const interval = setInterval(checkStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  return status;
}; 