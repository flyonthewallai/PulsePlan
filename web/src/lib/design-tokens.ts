/**
 * Design Tokens System for PulsePlan
 *
 * This file defines the standardized design system for consistent UI across the application.
 * All components should reference these tokens instead of using arbitrary Tailwind classes.
 *
 * Usage:
 * import { typography, colors, spacing, components } from '@/lib/design-tokens';
 * <h1 className={typography.pageTitle}>My Page</h1>
 * <div className={components.card}>Card content</div>
 */

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  // Page-level headings
  pageTitle: 'text-2xl font-bold',

  // Section headings (larger modals, major sections)
  sectionTitle: 'text-xl font-semibold',

  // Subsection headings (card headers, modal sections)
  subsectionTitle: 'text-base font-semibold',

  // Card label (uppercase labels like "TASKS", "UPCOMING")
  cardLabel: 'text-xs font-semibold uppercase tracking-wider',

  // Body text sizes
  body: {
    // Default body text (used in cards, compact views)
    default: 'text-sm font-medium',
    // Larger body text (used in modals, expanded views)
    large: 'text-base font-medium',
    // Small body text (captions, metadata)
    small: 'text-xs font-normal',
  },

  // Interactive elements
  button: {
    primary: 'text-sm font-semibold',
    secondary: 'text-sm font-medium',
  },

  // Form elements
  input: {
    label: 'text-sm font-medium',
    helper: 'text-xs',
    placeholder: 'text-sm',
  },
} as const;

// ============================================================================
// COLORS
// ============================================================================

export const colors = {
  // Background colors
  bg: {
    // Main page background
    page: 'bg-[#0f0f0f]',
    // Card backgrounds
    card: 'bg-neutral-800/40',
    cardHover: 'bg-neutral-800/60',
    // Modal backgrounds
    modal: 'bg-[#121212]',
    // Input/form field backgrounds
    input: 'bg-neutral-800/40',
    inputFocus: 'bg-neutral-800/60',
    // Button backgrounds
    buttonPrimary: 'bg-white',
    buttonPrimaryHover: 'bg-gray-100',
    buttonSecondary: 'bg-neutral-800/40',
    buttonSecondaryHover: 'bg-neutral-800/60',
    buttonDanger: 'bg-red-500/10',
    buttonDangerHover: 'bg-red-500/20',
  },

  // Text colors
  text: {
    primary: 'text-white',
    secondary: 'text-gray-400',
    tertiary: 'text-gray-500',
    // Button text colors
    buttonPrimary: 'text-black',
    buttonSecondary: 'text-white',
    buttonDanger: 'text-red-400',
    // Special states
    muted: 'text-gray-600',
    success: 'text-green-400',
    warning: 'text-yellow-400',
    error: 'text-red-400',
  },

  // Border colors
  border: {
    default: 'border-gray-700/50',
    subtle: 'border-gray-700/30',
    focus: 'border-gray-600',
    error: 'border-red-500/50',
  },
} as const;

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  // Card padding
  card: {
    padding: 'p-5',
    paddingX: 'px-5',
    paddingY: 'py-5',
  },

  // Modal padding
  modal: {
    padding: 'p-6',
    paddingX: 'px-6',
    paddingY: 'py-6',
    header: 'px-6 py-4',
    content: 'px-6 py-4',
    footer: 'px-6 py-4',
  },

  // Gap spacing (for flex/grid layouts)
  gap: {
    xs: 'gap-1.5',
    sm: 'gap-2',
    md: 'gap-3',
    lg: 'gap-4',
    xl: 'gap-6',
  },

  // Stack spacing (for vertical layouts with space-y)
  stack: {
    xs: 'space-y-1.5',
    sm: 'space-y-2',
    md: 'space-y-4',
    lg: 'space-y-6',
    xl: 'space-y-8',
  },

  // Section spacing (margins between major sections)
  section: {
    marginBottom: 'mb-6',
    marginTop: 'mt-6',
  },
} as const;

// ============================================================================
// COMPONENT STYLES
// ============================================================================

export const components = {
  // Card component
  card: {
    base: 'bg-neutral-800/40 border border-gray-700/50 rounded-xl p-5',
    header: 'text-xs font-semibold uppercase tracking-wider text-gray-400',
    content: 'text-sm font-medium text-white',
  },

  // Modal component
  modal: {
    overlay: 'fixed inset-0 bg-black/50 flex items-center justify-center z-50',
    container: 'bg-[#121212] border border-gray-700/50 rounded-2xl max-w-2xl w-full mx-4',
    header: 'px-6 py-4 border-b border-gray-700/30',
    title: 'text-xl font-semibold text-white',
    content: 'px-6 py-4',
    footer: 'px-6 py-4 border-t border-gray-700/30 flex items-center justify-end gap-3',
    closeButton: 'p-1.5 text-gray-400 hover:text-white hover:bg-neutral-800/40 rounded-lg transition-colors',
  },

  // Button component
  button: {
    base: 'rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#121212]',
    primary: 'bg-white text-black hover:bg-gray-100 focus:ring-white',
    secondary: 'border border-gray-700/50 text-white hover:bg-neutral-800/40 focus:ring-gray-600',
    danger: 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/50 focus:ring-red-500',
    ghost: 'text-gray-400 hover:text-white hover:bg-neutral-800/40',
  },

  // Input component
  input: {
    base: 'bg-neutral-800/40 border border-gray-700/50 rounded-lg px-3 py-2 text-white placeholder-gray-400 text-sm transition-colors focus:outline-none focus:border-gray-600',
    error: 'border-red-500/50 focus:border-red-500',
    label: 'block text-sm font-medium text-gray-400 mb-1.5',
    helper: 'text-xs text-gray-500 mt-1',
  },

  // Select/Dropdown component
  select: {
    base: 'bg-neutral-800/40 border border-gray-700/50 rounded-lg pl-3 pr-9 py-2 text-white text-sm transition-colors focus:outline-none focus:border-gray-600 appearance-none cursor-pointer [background-image:url("data:image/svg+xml,%3csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20fill=%27none%27%20viewBox=%270%200%2020%2020%27%3e%3cpath%20stroke=%27%239ca3af%27%20stroke-linecap=%27round%27%20stroke-linejoin=%27round%27%20stroke-width=%271.5%27%20d=%27M6%208l4%204%204-4%27/%3e%3c/svg%3e")] [background-position:right_0.5rem_center] [background-repeat:no-repeat] [background-size:1.5em_1.5em]',
  },

  // Textarea component
  textarea: {
    base: 'bg-neutral-800/40 border border-gray-700/50 rounded-lg px-3 py-2 text-white placeholder-gray-400 text-sm transition-colors focus:outline-none focus:border-gray-600 resize-none',
  },

  // Badge/Tag component
  badge: {
    base: 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
    default: 'bg-neutral-800/60 text-gray-300 border border-gray-700/50',
    primary: 'bg-blue-500/10 text-blue-400 border border-blue-500/50',
    success: 'bg-green-500/10 text-green-400 border border-green-500/50',
    warning: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/50',
    danger: 'bg-red-500/10 text-red-400 border border-red-500/50',
  },

  // Divider
  divider: {
    horizontal: 'border-t border-gray-700/30',
    vertical: 'border-l border-gray-700/30',
  },

  // Connection item (for connected account lists)
  connectionItem: {
    base: 'bg-neutral-800/40 border border-gray-700/50 rounded-lg p-3 flex items-center justify-between',
    iconContainer: 'w-8 h-8 rounded-lg bg-neutral-700 flex items-center justify-center overflow-hidden',
    icon: 'w-6 h-6 object-contain',
    text: {
      primary: 'text-white text-sm font-medium',
      secondary: 'text-gray-400 text-xs',
    },
    actionButton: 'p-1 hover:bg-neutral-700/50 rounded-lg transition-colors',
    dropdown: 'absolute right-0 top-8 bg-neutral-800 border border-gray-700/50 rounded-lg shadow-lg z-10 min-w-[160px]',
    dropdownItem: 'w-full px-3 py-2 text-left text-red-400 hover:bg-neutral-700/50 text-sm transition-colors',
  },

  // Setting item (for calendar settings, preferences, etc.)
  settingItem: {
    base: 'bg-neutral-800/40 border border-gray-700/50 rounded-lg p-3',
    // Interactive/clickable setting item with hover effect
    interactive: 'bg-neutral-800/40 border border-gray-700/50 rounded-lg p-3 cursor-pointer hover:bg-white/5 transition-colors',
    description: 'text-gray-400 text-sm',
  },

  // Small icon button (for attach, command triggers, etc.)
  iconButton: {
    small: 'p-1 rounded hover:bg-white/5 transition-colors',
  },
} as const;

// ============================================================================
// LAYOUT UTILITIES
// ============================================================================

export const layout = {
  // Container widths
  container: {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-full',
  },

  // Flexbox utilities
  flex: {
    center: 'flex items-center justify-center',
    between: 'flex items-center justify-between',
    start: 'flex items-start',
    end: 'flex items-end',
  },

  // Grid utilities
  grid: {
    cols2: 'grid grid-cols-2',
    cols3: 'grid grid-cols-3',
    cols4: 'grid grid-cols-4',
  },
} as const;

// ============================================================================
// ANIMATION UTILITIES
// ============================================================================

export const animation = {
  transition: {
    fast: 'transition-all duration-150',
    default: 'transition-all duration-200',
    slow: 'transition-all duration-300',
  },

  hover: {
    scale: 'hover:scale-105 transition-transform',
    opacity: 'hover:opacity-80 transition-opacity',
  },
} as const;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Combines multiple design token classes into a single className string
 * @param classes - Array of class strings to combine
 * @returns Combined className string
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Example usage:
 *
 * import { typography, components, spacing, cn } from '@/lib/design-tokens';
 *
 * <div className={components.card.base}>
 *   <h2 className={components.card.header}>UPCOMING</h2>
 *   <p className={components.card.content}>Card content here</p>
 * </div>
 *
 * <button className={cn(components.button.base, components.button.primary)}>
 *   Save Changes
 * </button>
 */
