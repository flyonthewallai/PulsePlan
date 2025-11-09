# STYLES.md - Frontend Design System

**Last Updated:** 11/05/25
**Purpose:** Define the standardized design system and styling patterns for PulsePlan frontend

---

## Overview

PulsePlan uses a **design tokens system** to ensure consistent UI/UX across the application. All styling is centralized in [`web/src/lib/design-tokens.ts`](../../web/src/lib/design-tokens.ts) and should be referenced instead of using arbitrary Tailwind classes.

### Tech Stack
- **Framework**: React + TypeScript + Vite
- **Styling**: Tailwind CSS v3
- **Design System**: Centralized design tokens
- **Font**: Inter (Google Fonts)
- **Theme**: Dark mode only

---

## Design Tokens Location

**File:** `web/src/lib/design-tokens.ts`

```typescript
import { typography, colors, spacing, components, layout, animation } from '@/lib/design-tokens';
```

---

## Color System

### Base Colors (from `tailwind.config.js`)

```javascript
colors: {
  background: "#0f0f0f",    // Main page background
  primary: "#4F8CFF",        // Primary brand color (blue)
  accent: "#8E6FFF",         // Accent color (purple)
  active: "#4F8CFF",         // Active state color
  surface: "#1A1A2E",        // Surface/card backgrounds
  card: "#262638",           // Card component backgrounds
  textPrimary: "#FFFFFF",    // Primary text
  textSecondary: "#C6C6D9",  // Secondary text
  success: "#4CD964",        // Success states
  warning: "#FFC043",        // Warning states
  error: "#E53E3E",          // Error states
}
```

### Task Priority Colors

```javascript
taskColors: {
  high: "#E53E3E",      // Red
  medium: "#FFC043",    // Orange/Yellow
  low: "#4CD964",       // Green
  default: "#8E6FFF",   // Purple
}
```

### Neutral Palette

```javascript
neutral: {
  50: "#fafafa",
  100: "#f5f5f5",
  200: "#e5e5e5",
  300: "#d4d4d4",
  400: "#a3a3a3",
  500: "#737373",
  600: "#525252",
  700: "#404040",
  750: "#2A2A2A",   // Custom shade
  800: "#262626",
  900: "#171717",
  950: "#0A0A0A",
}
```

### Design Token Color Classes

From `design-tokens.ts`:

```typescript
// Background colors
colors.bg.page              // bg-[#0f0f0f]
colors.bg.card              // bg-neutral-800/40
colors.bg.cardHover         // bg-neutral-800/60
colors.bg.modal             // bg-[#121212]
colors.bg.input             // bg-neutral-800/40
colors.bg.inputFocus        // bg-neutral-800/60
colors.bg.buttonPrimary     // bg-white
colors.bg.buttonSecondary   // bg-neutral-800/40

// Text colors
colors.text.primary         // text-white
colors.text.secondary       // text-gray-400
colors.text.tertiary        // text-gray-500
colors.text.muted           // text-gray-600
colors.text.success         // text-green-400
colors.text.warning         // text-yellow-400
colors.text.error           // text-red-400

// Border colors
colors.border.default       // border-gray-700/50
colors.border.subtle        // border-gray-700/30
colors.border.focus         // border-gray-600
colors.border.error         // border-red-500/50
```

---

## Typography System

### Font Configuration

**Font Family:** Inter (weights: 300, 400, 500, 600, 700)

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

### Typography Tokens

```typescript
// Headings
typography.pageTitle           // text-2xl font-bold
typography.sectionTitle        // text-xl font-semibold
typography.subsectionTitle     // text-base font-semibold
typography.cardLabel           // text-xs font-semibold uppercase tracking-wider

// Body text
typography.body.default        // text-sm font-medium
typography.body.large          // text-base font-medium
typography.body.small          // text-xs font-normal

// Interactive elements
typography.button.primary      // text-sm font-semibold
typography.button.secondary    // text-sm font-medium

// Form elements
typography.input.label         // text-sm font-medium
typography.input.helper        // text-xs
typography.input.placeholder   // text-sm
```

### Usage Example

```tsx
<h1 className={typography.pageTitle}>Dashboard</h1>
<h2 className={typography.sectionTitle}>Tasks</h2>
<p className={typography.body.default}>Task description</p>
<span className={typography.cardLabel}>UPCOMING</span>
```

---

## Spacing System

### Spacing Tokens

```typescript
// Card padding
spacing.card.padding           // p-5
spacing.card.paddingX          // px-5
spacing.card.paddingY          // py-5

// Modal padding
spacing.modal.padding          // p-6
spacing.modal.header           // px-6 py-4
spacing.modal.content          // px-6 py-4
spacing.modal.footer           // px-6 py-4

// Gap spacing (flex/grid)
spacing.gap.xs                 // gap-1.5
spacing.gap.sm                 // gap-2
spacing.gap.md                 // gap-3
spacing.gap.lg                 // gap-4
spacing.gap.xl                 // gap-6

// Stack spacing (vertical)
spacing.stack.xs               // space-y-1.5
spacing.stack.sm               // space-y-2
spacing.stack.md               // space-y-4
spacing.stack.lg               // space-y-6
spacing.stack.xl               // space-y-8

// Section spacing
spacing.section.marginBottom   // mb-6
spacing.section.marginTop      // mt-6
```

---

## Component Patterns

### Card Component

```typescript
components.card.base           // Full card styling
components.card.header         // Card header text
components.card.content        // Card content text
```

**Example:**
```tsx
<div className={components.card.base}>
  <h3 className={components.card.header}>UPCOMING TASKS</h3>
  <p className={components.card.content}>Task content here</p>
</div>
```

### Modal Component

```typescript
components.modal.overlay       // Modal backdrop
components.modal.container     // Modal box
components.modal.header        // Header section
components.modal.title         // Title text
components.modal.content       // Content section
components.modal.footer        // Footer with buttons
components.modal.closeButton   // Close button
```

**Example:**
```tsx
<div className={components.modal.overlay}>
  <div className={components.modal.container}>
    <div className={components.modal.header}>
      <h2 className={components.modal.title}>Edit Task</h2>
    </div>
    <div className={components.modal.content}>
      {/* Modal content */}
    </div>
    <div className={components.modal.footer}>
      <button className={cn(components.button.base, components.button.primary)}>
        Save
      </button>
    </div>
  </div>
</div>
```

### Button Component

```typescript
components.button.base         // Base button styles
components.button.primary      // White button (primary action)
components.button.secondary    // Outlined button
components.button.danger       // Red button (destructive)
components.button.ghost        // Transparent hover button
```

**Example:**
```tsx
import { components, cn } from '@/lib/design-tokens';

<button className={cn(components.button.base, components.button.primary)}>
  Save Changes
</button>

<button className={cn(components.button.base, components.button.secondary)}>
  Cancel
</button>

<button className={cn(components.button.base, components.button.danger)}>
  Delete
</button>
```

### Input Component

```typescript
components.input.base          // Input field styling
components.input.error         // Error state styling
components.input.label         // Label styling
components.input.helper        // Helper text styling
```

**Example:**
```tsx
<div>
  <label className={components.input.label}>Task Title</label>
  <input
    type="text"
    className={components.input.base}
    placeholder="Enter task title"
  />
  <p className={components.input.helper}>This will be visible to all members</p>
</div>
```

### Badge Component

```typescript
components.badge.base          // Base badge styling
components.badge.default       // Gray badge
components.badge.primary       // Blue badge
components.badge.success       // Green badge
components.badge.warning       // Yellow badge
components.badge.danger        // Red badge
```

**Example:**
```tsx
<span className={cn(components.badge.base, components.badge.success)}>
  Completed
</span>

<span className={cn(components.badge.base, components.badge.warning)}>
  In Progress
</span>
```

### Other Components

```typescript
// Select/Dropdown
components.select.base

// Textarea
components.textarea.base

// Divider
components.divider.horizontal  // Horizontal line
components.divider.vertical    // Vertical line

// Connection Item (OAuth accounts)
components.connectionItem.base
components.connectionItem.iconContainer
components.connectionItem.text.primary
components.connectionItem.text.secondary

// Setting Item
components.settingItem.base
components.settingItem.interactive  // Clickable settings

// Icon Button
components.iconButton.small
```

---

## Layout Utilities

### Container Widths

```typescript
layout.container.sm            // max-w-md
layout.container.md            // max-w-2xl
layout.container.lg            // max-w-4xl
layout.container.xl            // max-w-6xl
layout.container.full          // max-w-full
```

### Flexbox Utilities

```typescript
layout.flex.center             // flex items-center justify-center
layout.flex.between            // flex items-center justify-between
layout.flex.start              // flex items-start
layout.flex.end                // flex items-end
```

### Grid Utilities

```typescript
layout.grid.cols2              // grid grid-cols-2
layout.grid.cols3              // grid grid-cols-3
layout.grid.cols4              // grid grid-cols-4
```

---

## Animation Utilities

### Transitions

```typescript
animation.transition.fast      // transition-all duration-150
animation.transition.default   // transition-all duration-200
animation.transition.slow      // transition-all duration-300
```

### Hover Effects

```typescript
animation.hover.scale          // hover:scale-105 transition-transform
animation.hover.opacity        // hover:opacity-80 transition-opacity
```

### Custom Keyframes

From `tailwind.config.js`:

```javascript
keyframes: {
  flipTop: {
    "0%": { transform: "rotateX(0)" },
    "100%": { transform: "rotateX(-90deg)" },
  },
  flipBottom: {
    "0%": { transform: "rotateX(90deg)" },
    "100%": { transform: "rotateX(0)" },
  },
}

animation: {
  flipTop: "flipTop 0.5s ease forwards",
  flipBottom: "flipBottom 0.5s ease forwards",
}
```

Used in FlipClock component for Pomodoro timer.

---

## Custom Input Styling

### Datetime Input

Special styling for dark mode datetime inputs with custom calendar picker:

```css
input[type="datetime-local"] {
  color-scheme: dark;
}

/* Custom calendar picker icon */
input[type="datetime-local"]::-webkit-calendar-picker-indicator {
  filter: invert(1);
  opacity: 0.6;
  cursor: pointer;
}

/* Field focus states */
input[type="datetime-local"]::-webkit-datetime-edit-month-field:focus {
  background-color: rgba(59, 130, 246, 0.3);
  outline: none;
  border-radius: 4px;
}
```

### Number Input

```css
/* Hide spin buttons for cleaner look */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
```

### Time Input

Similar dark mode styling as datetime inputs.

---

## Border Radius

CSS variable system for consistent border radius:

```css
:root {
  --radius: 0.5rem;
}
```

Tailwind config:

```javascript
borderRadius: {
  lg: "var(--radius)",           // 0.5rem
  md: "calc(var(--radius) - 2px)",  // 0.375rem
  sm: "calc(var(--radius) - 4px)",  // 0.25rem
}
```

---

## Design Patterns & Best Practices

### ✅ DO: Use Design Tokens

```tsx
// ✅ GOOD
import { components } from '@/lib/design-tokens';

<button className={components.button.base, components.button.primary}>
  Save
</button>
```

### ❌ DON'T: Use Arbitrary Tailwind Classes

```tsx
// ❌ BAD
<button className="bg-white text-black hover:bg-gray-100 px-4 py-2 rounded-lg">
  Save
</button>
```

### ✅ DO: Combine Tokens with cn() Helper

```tsx
import { components, cn } from '@/lib/design-tokens';

<button 
  className={cn(
    components.button.base,
    isDestructive ? components.button.danger : components.button.primary,
    className // Allow prop-based overrides
  )}
>
  {label}
</button>
```

### ✅ DO: Create Reusable Components

```tsx
// components/ui/Button.tsx
import { components, cn } from '@/lib/design-tokens';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  children: React.ReactNode;
  className?: string;
}

export function Button({ variant = 'primary', children, className }: ButtonProps) {
  return (
    <button 
      className={cn(
        components.button.base,
        components.button[variant],
        className
      )}
    >
      {children}
    </button>
  );
}
```

### ✅ DO: Follow Naming Conventions

- Component files: `PascalCase.tsx`
- Utility files: `camelCase.ts`
- Style utilities: Use design tokens, not inline styles

### ❌ DON'T: Use Inline Styles

```tsx
// ❌ BAD
<div style={{ backgroundColor: '#1A1A2E', padding: '20px' }}>
  Content
</div>

// ✅ GOOD
<div className={cn(colors.bg.surface, spacing.card.padding)}>
  Content
</div>
```

---

## Existing UI Components

Located in `web/src/components/ui/`:

- `button.tsx` - Button component with variants
- `card.tsx` - Card container component
- `input.tsx` - Text input component
- `textarea.tsx` - Textarea component
- `badge.tsx` - Badge/tag component
- `tabs.tsx` - Tabs navigation
- `table.tsx` - Data table component
- `progress.tsx` - Progress bar
- `alert.tsx` - Alert/notification component
- `Toast.tsx` - Toast notification system
- `DateTimePicker.tsx` - Custom datetime picker
- `ProfilePicture.tsx` - User avatar component
- `ErrorBoundary.tsx` - Error boundary wrapper
- `InlineAlert.tsx` - Inline alert messages

---

## Color Accessibility

### Contrast Ratios

All color combinations meet WCAG AA standards:

- **White text on dark backgrounds**: 15:1+ ratio
- **Gray-400 text on dark backgrounds**: 7:1+ ratio
- **Primary blue on dark backgrounds**: 4.5:1+ ratio

### Color Blindness Considerations

- Task priorities use both color AND text labels
- Error states include icons, not just color
- Success/warning states clearly differentiated by hue

---

## Responsive Design

### Breakpoints

Using Tailwind's default breakpoints:

```javascript
sm: '640px'   // Mobile landscape
md: '768px'   // Tablet
lg: '1024px'  // Desktop
xl: '1280px'  // Large desktop
2xl: '1536px' // Extra large
```

### Mobile-First Approach

All styles are mobile-first, with larger breakpoints added as needed:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* Responsive grid */}
</div>
```

---

## Testing Checklist

When adding new styled components:

- [ ] Uses design tokens (not arbitrary Tailwind classes)
- [ ] Supports dark mode (already default)
- [ ] Responsive on mobile, tablet, desktop
- [ ] Accessible contrast ratios
- [ ] Keyboard navigable (for interactive elements)
- [ ] Consistent with existing components
- [ ] Reusable and composable
- [ ] TypeScript interfaces defined
- [ ] Hover/focus states included

---

## Updating the Design System

### When to Add New Tokens

Add new tokens to `design-tokens.ts` when:
- Creating a new reusable pattern used 3+ times
- Establishing a new component variant
- Defining new spacing/sizing standards

### When to Update Existing Tokens

Update tokens when:
- Changing brand colors
- Adjusting typography scale
- Modifying spacing system

**⚠️ IMPORTANT: Always update this document (STYLES.md) when modifying design-tokens.ts**

---

## Common Issues & Solutions

### Issue: `design-tokens.ts` is gitignored

**Problem:** The file is caught by `.gitignore` rule `lib/` (line 18) which is intended for Python libraries.

**Solution:** The `.gitignore` should be updated to exclude `web/src/lib/` from the Python `lib/` ignore pattern:

```gitignore
# Python libraries (exclude web frontend lib)
lib/
!web/src/lib/
```

**Status:** ⚠️ **design-tokens.ts is currently untracked and should be added to git**

### Issue: Inconsistent styling across components

**Solution:** Audit components to ensure all use design tokens. Run:
```bash
# Find components with hardcoded Tailwind classes
grep -r "className=\".*bg-\[#" web/src/components/
```

### Issue: Dark mode not working

**Solution:** Ensure root element has dark background:
```css
html, body, #root {
  background-color: #0f0f0f;
}
```

---

## Related Documentation

- **Component examples**: [EXAMPLES.md](./EXAMPLES.md) - Frontend component patterns
- **Architecture**: [../02-architecture/ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
- **Testing**: [TESTING.md](./TESTING.md) - Component testing strategy

---

**Last Updated:** 11/05/25
**Maintained By:** Development Team
**Design System File:** `web/src/lib/design-tokens.ts` (currently untracked - needs git add)
