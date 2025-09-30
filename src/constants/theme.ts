export const colors = {
  backgroundDark: '#0A0A1F',
  primaryBlue: '#4F8CFF',
  accentPurple: '#8E6FFF',
  textPrimary: '#FFFFFF',
  textSecondary: '#C6C6D9',
  premiumThemeName: 'rgba(255, 255, 255, 0.5)',
  taskColors: {
    high: '#E53E3E',
    medium: '#FFC043',
    low: '#4CD964',
    default: '#8E6FFF',
  },
  success: '#4CD964',
  warning: '#FFC043',
  error: '#E53E3E',
};

export const shadows = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  large: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 6,
  },
};

export const gradients = {
  primary: {
    colors: [colors.primaryBlue, colors.accentPurple],
    start: { x: 0, y: 0 },
    end: { x: 1, y: 1 },
  },
  success: {
    colors: [colors.success, colors.primaryBlue],
    start: { x: 0, y: 0 },
    end: { x: 1, y: 1 },
  },
  warning: {
    colors: [colors.warning, colors.primaryBlue],
    start: { x: 0, y: 0 },
    end: { x: 1, y: 1 },
  },
  error: {
    colors: [colors.error, colors.primaryBlue],
    start: { x: 0, y: 0 },
    end: { x: 1, y: 1 },
  },
}; 