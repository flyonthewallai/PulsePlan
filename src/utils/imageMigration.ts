// Utility to help migrate existing Image components to CachedImage
// This provides a mapping of require statements to image keys

export const IMAGE_MIGRATION_MAP = {
  // App icons
  '@/assets/images/icon.png': 'icon',
  '@/assets/images/pulselogo.png': 'pulselogo',
  
  // Integration icons
  '@/assets/images/applecalendar.png': 'applecalendar',
  '@/assets/images/applecontacts.webp': 'applecontacts',
  '@/assets/images/canvas.png': 'canvas',
  '@/assets/images/gmail.png': 'gmail',
  '@/assets/images/googlecalendar.png': 'googlecalendar',
  '@/assets/images/googlecontacts.webp': 'googlecontacts',
  '@/assets/images/notion.png': 'notion',
} as const;

/**
 * Get the image key for a require statement
 */
export function getImageKey(requirePath: string): keyof typeof IMAGE_MIGRATION_MAP | null {
  return IMAGE_MIGRATION_MAP[requirePath as keyof typeof IMAGE_MIGRATION_MAP] || null;
}

/**
 * Migration guide for converting Image components to CachedImage
 */
export const MIGRATION_GUIDE = {
  // Before:
  // <Image source={require('@/assets/images/icon.png')} style={styles.icon} />
  
  // After:
  // <CachedImage imageKey="icon" style={styles.icon} />
  
  // Steps:
  // 1. Import CachedImage: import { CachedImage } from '@/components/CachedImage';
  // 2. Replace Image with CachedImage
  // 3. Replace source={require('...')} with imageKey="key"
  // 4. Remove the require statement
} as const; 