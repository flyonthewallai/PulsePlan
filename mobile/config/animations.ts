// Animation configurations for smooth page transitions
export const navigationAnimations = {
  // Default slide animation for most screens
  slideFromRight: {
    animation: 'slide_from_right' as const,
    animationDuration: 300,
    animationTypeForReplace: 'push' as const,
  },
  
  // No animation for tab switches - standard for major apps
  noAnimation: {
    animation: 'none' as const,
  },
  
  // Smooth fade for quick transitions (deprecated for tabs)
  fade: {
    animation: 'fade' as const,
    animationDuration: 200,
    animationTypeForReplace: 'push' as const,
  },
  
  // Smooth slide from bottom for modals
  slideFromBottom: {
    animation: 'slide_from_bottom' as const,
    animationDuration: 350,
    animationTypeForReplace: 'push' as const,
  },
  
  // Fast fade for auth flows
  fastFade: {
    animation: 'fade' as const,
    animationDuration: 150,
    animationTypeForReplace: 'push' as const,
  },
  
  // Slower, more elegant slide for onboarding
  elegantSlide: {
    animation: 'slide_from_right' as const,
    animationDuration: 400,
    animationTypeForReplace: 'push' as const,
  },
};

// Timing configurations for consistent easing
export const animationTiming = {
  fast: 150,
  normal: 250,
  slow: 350,
  elegant: 400,
};

// Common easing curves
export const easingCurves = {
  smooth: 'ease-out',
  bouncy: 'spring',
  quick: 'ease-in-out',
  elegant: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
} as const; 