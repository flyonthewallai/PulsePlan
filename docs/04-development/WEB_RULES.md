# PulsePlan – Web Application Development Rules

**Last Updated:** 11/06/25

> **Enforcement Level: CRITICAL** - All AI agents must follow these patterns for web development. This document defines type safety, security, performance, and code quality standards for the React/TypeScript frontend.

> **Every web change must follow these rules.** These patterns are production-proven and enforce security, type safety, and maintainability.

---

## Table of Contents

1. [Type Safety (Zero `any` Policy)](#1-type-safety-zero-any-policy)
2. [Security Requirements](#2-security-requirements)
3. [State Management Patterns](#3-state-management-patterns)
4. [Component Organization](#4-component-organization)
5. [Code Deduplication](#5-code-deduplication)
6. [Performance Requirements](#6-performance-requirements)
7. [Data Fetching & Caching](#7-data-fetching--caching)
8. [Testing Requirements](#8-testing-requirements)
9. [Prohibited Anti-Patterns](#9-prohibited-anti-patterns)
10. [Search Patterns for Audits](#10-search-patterns-for-audits)

---

## 0. Purpose

Keep PulsePlan web app **secure, type-safe, and maintainable**.

- ✅ **Zero `any` types** - Full TypeScript safety
- ✅ **Secure storage** - sessionStorage for temporary, never localStorage for tokens
- ✅ **Proper React patterns** - Context over globals, hooks over classes
- ✅ **Component size limits** - <500 lines per file
- ✅ **Error boundaries** - All major pages protected
- ✅ **Performance** - React.memo for lists, proper memoization

---

## 1. Type Safety (CRITICAL)

### 1.1 NO `any` Types - EVER

**❌ PROHIBITED:**

```typescript
// WRONG - Eliminates TypeScript benefits
function handleData(data: any) {
  return data.value;
}

interface Message {
  metadata?: any; // WRONG
  data?: any; // WRONG
}
```

**✅ REQUIRED:**

```typescript
// CORRECT - Full type safety
interface MessageMetadata {
  operation?: string;
  entity_type?: string;
  task_count?: number;
  [key: string]: unknown; // Use unknown for dynamic keys
}

interface Message {
  id: string;
  metadata?: MessageMetadata;
  data?: Record<string, unknown>;
}

function handleData(data: Record<string, unknown>) {
  return data.value as string;
}
```

### 1.2 Proper Generic Constraints

**❌ WRONG:**

```typescript
async function fetchData<T = any>(url: string): Promise<T> {
  return fetch(url).then((r) => r.json());
}
```

**✅ CORRECT:**

```typescript
async function fetchData<T = unknown>(url: string): Promise<T> {
  return fetch(url).then((r) => r.json());
}

// Better: Provide specific type
interface Task {
  id: string;
  title: string;
}

async function fetchTasks(): Promise<Task[]> {
  return fetchData<Task[]>("/api/tasks");
}
```

### 1.3 WebSocket Event Types

**✅ REQUIRED PATTERN:**

Define strict types for all WebSocket events:

```typescript
// Define event data structures
interface TaskCreatedEvent {
  task: Task;
  timestamp: string;
  workflow_id?: string;
}

interface WorkflowCompletionEvent {
  workflow_id: string;
  success: boolean;
  result?: {
    data?: {
      task?: Task;
    };
  };
}

// Use in socket handlers
socket.on("task_created", (data: TaskCreatedEvent) => {
  // Full type safety here
  console.log(data.task.id);
});
```

**Example**: See `web/src/contexts/TaskSuccessContext.tsx` for comprehensive WebSocket typing.

---

## 2. Security (CRITICAL)

### 2.1 Storage Rules

**NEVER store sensitive data in localStorage** - it persists and is vulnerable to XSS.

#### ✅ sessionStorage - For Temporary Cross-Window Data

```typescript
// CORRECT - Temporary OAuth window communication
const result = {
  type: "oauth-success",
  provider: "google",
  timestamp: Date.now(),
};
sessionStorage.setItem("oauth_result", JSON.stringify(result));

// Clear immediately after use
sessionStorage.removeItem("oauth_result");
```

#### ❌ localStorage - NEVER for Auth/Tokens

```typescript
// WRONG - Persists indefinitely, XSS vulnerable
localStorage.setItem("access_token", token); // NEVER DO THIS
localStorage.setItem("oauth_result", JSON.stringify({ token })); // NEVER
```

#### ✅ Proper Token Storage

Tokens are already stored securely via Supabase httpOnly cookies. **Never** handle tokens directly in JavaScript:

```typescript
// CORRECT - Tokens in httpOnly cookies (automatic)
const {
  data: { session },
} = await supabase.auth.getSession();
const token = session?.access_token; // Only access when needed for headers
```

### 2.2 Remove Debug Logging in Production

**❌ PROHIBITED in Production:**

```typescript
// WRONG - Exposes configuration
console.log("Supabase URL:", config.supabase.url);
console.log("API Key:", config.apiKey);
console.log("User data:", userData);
```

**✅ ALLOWED:**

```typescript
// OK - Generic errors only
console.error("Failed to load data");

// Better - Use proper error tracking
if (import.meta.env.DEV) {
  console.debug("Debug info:", data);
}
```

### 2.3 Input Validation

**✅ REQUIRED:**

Use Zod or validators for all user input:

```typescript
import { z } from "zod";

const taskSchema = z.object({
  title: z.string().min(1).max(200),
  due_date: z.string().datetime().optional(),
  priority: z.enum(["low", "medium", "high"]),
});

type TaskInput = z.infer<typeof taskSchema>;

function createTask(input: unknown) {
  const validated = taskSchema.parse(input); // Throws if invalid
  return api.post("/tasks", validated);
}
```

---

## 3. React Patterns (CRITICAL)

### 3.1 Context Over Global Variables

**❌ PROHIBITED - Module-Level Globals:**

```typescript
// WRONG - Anti-pattern, memory leaks, not testable
let globalHandler: ((data: any) => void) | null = null;

export function setGlobalHandler(fn: (data: any) => void) {
  globalHandler = fn;
}

// Component
useEffect(() => {
  setGlobalHandler(myHandler);
}, []);
```

**✅ REQUIRED - Proper React Context with useRef:**

```typescript
// CORRECT - React Context with refs
interface MyContextType {
  registerHandler: (handler: (data: SomeType) => void) => void;
}

export function MyProvider({ children }: { children: ReactNode }) {
  const handlerRef = useRef<((data: SomeType) => void) | null>(null);

  const registerHandler = useCallback((handler: (data: SomeType) => void) => {
    handlerRef.current = handler;
  }, []);

  // Use handlerRef.current when needed
  useEffect(() => {
    if (handlerRef.current) {
      handlerRef.current(someData);
    }
  }, [someData]);

  return (
    <MyContext.Provider value={{ registerHandler }}>
      {children}
    </MyContext.Provider>
  );
}

// Usage
export function useMyContext() {
  const context = useContext(MyContext);
  if (!context) {
    throw new Error("useMyContext must be used within MyProvider");
  }
  return context;
}
```

**Example**: See `web/src/contexts/TaskSuccessContext.tsx` for full implementation.

### 3.2 Custom Hooks for Data Fetching

**❌ WRONG - Logic in Components:**

```typescript
function MyComponent() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  // ...complex logic
}
```

**✅ CORRECT - Extract to Custom Hook:**

```typescript
// hooks/useMyData.ts
export function useMyData(userId: string) {
  return useQuery({
    queryKey: ["myData", userId],
    queryFn: () => api.get<MyData[]>(`/data/${userId}`),
  });
}

// Component
function MyComponent({ userId }: Props) {
  const { data, isLoading, error } = useMyData(userId);

  if (isLoading) return <Loader />;
  if (error) return <Error error={error} />;

  return <DataView data={data} />;
}
```

### 3.3 Proper Dependency Arrays

**❌ WRONG:**

```typescript
// Missing dependencies
useEffect(() => {
  fetchData(userId);
}, []); // userId should be in deps

// Unnecessary dependencies
const memoized = useMemo(() => {
  return data.map((item) => item.id);
}, [data, userId, formatDate]); // formatDate unnecessary
```

**✅ CORRECT:**

```typescript
// All dependencies included
useEffect(() => {
  fetchData(userId);
}, [userId]);

// Only necessary dependencies
const memoized = useMemo(() => {
  return data.map((item) => item.id);
}, [data]);

// Stabilize function dependencies with useCallback
const handleClick = useCallback(() => {
  doSomething(userId);
}, [userId]);
```

---

## 4. Component Organization

### 4.1 File Size Limits

**HARD LIMITS:**

- **500 lines maximum** per component file
- **300 lines target** for most components

**When approaching limit:**

1. Extract subcomponents
2. Extract hooks
3. Extract utilities
4. Create feature modules

**Example:**

```
// Before (1,638 lines)
components/SettingsModal.tsx

// After
components/settings/
├── SettingsModal.tsx          (200 lines) - Shell
├── ProfileSection.tsx         (150 lines)
├── NotificationsSection.tsx   (120 lines)
├── CoursesSection.tsx         (200 lines)
├── SubscriptionSection.tsx    (150 lines)
├── useSettingsForm.ts         (150 lines)
└── types.ts                   (50 lines)
```

### 4.2 Component Structure

**✅ REQUIRED ORDER:**

```typescript
// 1. Imports
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { MyComponent } from "./MyComponent";
import type { Props } from "./types";

// 2. Type definitions
interface MyProps {
  userId: string;
  onComplete: () => void;
}

// 3. Constants
const DEFAULT_PAGE_SIZE = 20;

// 4. Helper functions (outside component)
function formatDate(date: Date): string {
  return date.toLocaleDateString();
}

// 5. Component
export function MyFeature({ userId, onComplete }: MyProps) {
  // 5a. Hooks (in order: state, context, queries, effects)
  const [isOpen, setIsOpen] = useState(false);
  const { user } = useAuth();
  const { data, isLoading } = useData(userId);

  useEffect(() => {
    // Side effects
  }, []);

  // 5b. Event handlers
  const handleClick = () => {
    setIsOpen(true);
  };

  // 5c. Render logic
  if (isLoading) return <Loader />;

  return <div>{/* JSX */}</div>;
}
```

### 4.3 Extract Duplicate Logic

**❌ WRONG - Duplicated Utilities:**

```typescript
// In ComponentA.tsx
const formatCourseCode = (code: string) => {
  const match = code.match(/^([A-Za-z]+)\s*(\d{4})/);
  return match ? `${match[1]} ${match[2]}` : code;
};

// In ComponentB.tsx
const formatCourseCode = (code: string) => {
  const match = code.match(/^([A-Za-z]+)\s*(\d{4})/);
  return match ? `${match[1]} ${match[2]}` : code;
};
```

**✅ CORRECT - Shared Utility:**

```typescript
// lib/utils/formatters.ts
export function formatCourseCode(courseCode: string): string {
  const match4 = courseCode.match(/^([A-Za-z]+)\s*(\d{4})/);
  if (match4) return `${match4[1]} ${match4[2]}`;

  const match3 = courseCode.match(/^([A-Za-z]+)\s*(\d{3})/);
  if (match3) return `${match3[1]} ${match3[2]}`;

  return courseCode;
}

// Both components import
import { formatCourseCode } from "@/lib/utils/formatters";
```

**Example**: See `web/src/lib/utils/formatters.ts`.

---

## 5. Error Handling

### 5.1 Error Boundaries (REQUIRED)

**Every major page must have an error boundary:**

```typescript
// components/ui/ErrorBoundary.tsx
import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    // Send to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}

// Usage in pages
export function MyPage() {
  return (
    <ErrorBoundary fallback={<PageError />}>
      <PageContent />
    </ErrorBoundary>
  );
}
```

### 5.2 Try-Catch for Async Operations

**✅ REQUIRED:**

```typescript
async function handleSubmit(data: FormData) {
  try {
    setLoading(true);
    await api.post("/endpoint", data);
    toast.success("Success!");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    toast.error(`Failed: ${message}`);
    console.error("Submit failed:", error);
  } finally {
    setLoading(false);
  }
}
```

---

## 6. Performance Optimization

### 6.1 React.memo for List Items

**❌ WRONG - Re-renders Every Item on Any Change:**

```typescript
function TaskList({ tasks }: Props) {
  return (
    <div>
      {tasks.map((task) => (
        <div key={task.id}>{/* Complex task item */}</div>
      ))}
    </div>
  );
}
```

**✅ CORRECT - Memoized List Items:**

```typescript
interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
}

const TaskItem = memo(
  ({ task, onToggle }: TaskItemProps) => {
    return <div>{/* Complex task item */}</div>;
  },
  (prev, next) => {
    // Custom comparison - only re-render if these changed
    return (
      prev.task.id === next.task.id &&
      prev.task.status === next.task.status &&
      prev.task.title === next.task.title
    );
  }
);

function TaskList({ tasks, onToggle }: Props) {
  return (
    <div>
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} onToggle={onToggle} />
      ))}
    </div>
  );
}
```

### 6.2 useMemo and useCallback

**✅ When to Use:**

```typescript
// useMemo - Expensive computations
const expensiveValue = useMemo(() => {
  return tasks
    .filter(t => t.status === 'active')
    .sort((a, b) => a.priority - b.priority)
}, [tasks])  // Only recompute when tasks change

// useCallback - Functions passed to child components
const handleUpdate = useCallback((id: string) => {
  updateTask(id, { status: 'completed' })
}, [updateTask])  // Stable function reference

// Pass to memoized child
<TaskItem task={task} onUpdate={handleUpdate} />
```

**❌ Don't Overuse:**

```typescript
// WRONG - Unnecessary, simple operation
const name = useMemo(() => user.firstName + " " + user.lastName, [user]);

// CORRECT - Just compute directly
const name = user.firstName + " " + user.lastName;

// WRONG - No child components use this
const handleClick = useCallback(() => {
  console.log("clicked");
}, []);

// CORRECT - Just define normally
const handleClick = () => {
  console.log("clicked");
};
```

### 6.3 Avoid Heavy Dependencies

**❌ WRONG:**

```typescript
const filtered = useMemo(() => {
  return tasks.filter((t) => isValid(t));
}, [tasks, today, tomorrow, endOfWeek, formatDate, formatTime, formatCourse]);
// Too many dependencies - will recalculate often
```

**✅ CORRECT:**

```typescript
// Stabilize utility functions outside component or with useCallback
const formatters = useMemo(
  () => ({
    formatDate,
    formatTime,
    formatCourse,
  }),
  []
); // Stable reference

const filtered = useMemo(() => {
  return tasks.filter((t) => isValid(t));
}, [tasks]); // Minimal dependencies
```

---

## 7. API Integration

### 7.1 Use TanStack Query (React Query)

**✅ REQUIRED PATTERN:**

```typescript
// hooks/useTasks.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export function useTasks(userId: string) {
  return useQuery({
    queryKey: ["tasks", userId],
    queryFn: () => api.get<Task[]>(`/tasks?user_id=${userId}`),
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (task: TaskCreate) => api.post<Task>("/tasks", task),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

// Usage
function TaskList({ userId }: Props) {
  const { data: tasks, isLoading } = useTasks(userId);
  const createTask = useCreateTask();

  const handleCreate = async (task: TaskCreate) => {
    await createTask.mutateAsync(task);
  };

  // ...
}
```

### 7.2 Proper Cache Keys

**✅ HIERARCHICAL KEYS:**

```typescript
// Good cache key structure
export const CACHE_KEYS = {
  TASKS: ["tasks"],
  TASK: (id: string) => ["tasks", id],
  USER_TASKS: (userId: string) => ["tasks", "user", userId],

  TODOS: ["todos"],
  TODO: (id: string) => ["todos", id],
};

// Invalidate all tasks
queryClient.invalidateQueries({ queryKey: CACHE_KEYS.TASKS });

// Invalidate specific task
queryClient.invalidateQueries({ queryKey: CACHE_KEYS.TASK(taskId) });
```

---

## 8. Testing

### 8.1 Required Tests

**Every feature must have:**

- ✅ Component tests (Vitest + Testing Library)
- ✅ Hook tests
- ✅ Utility function tests

**Example:**

```typescript
// MyComponent.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MyComponent } from "./MyComponent";

describe("MyComponent", () => {
  it("renders correctly", () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("calls onSubmit when submitted", async () => {
    const onSubmit = vi.fn();
    render(<MyComponent onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(onSubmit).toHaveBeenCalled();
  });
});
```

---

## 9. Quality Gates

**Before EVERY commit, run:**

```bash
cd web

# Linting
npm run lint        # Must pass with 0 errors

# Type checking
npm run type-check  # Must pass with 0 errors

# Tests
npm run test        # All tests must pass

# Build
npm run build       # Must build successfully
```

---

## 10. Common Anti-Patterns to Avoid

### ❌ useState for Derived State

```typescript
// WRONG
const [total, setTotal] = useState(0);
useEffect(() => {
  setTotal(items.reduce((sum, item) => sum + item.price, 0));
}, [items]);

// CORRECT
const total = items.reduce((sum, item) => sum + item.price, 0);
```

### ❌ useEffect for Event Handlers

```typescript
// WRONG
useEffect(() => {
  if (shouldSubmit) {
    handleSubmit();
  }
}, [shouldSubmit]);

// CORRECT
const handleClick = () => {
  handleSubmit();
};
```

### ❌ Props Drilling

```typescript
// WRONG - Passing through 5 levels
<A user={user}>
  <B user={user}>
    <C user={user}>
      <D user={user}>
        <E user={user} />  // Finally used here
```

// CORRECT - Use Context
const UserContext = createContext<User | null>(null)

<UserContext.Provider value={user}>
<A>
<B>
<C>
<D>
<E /> // useContext(UserContext) inside

````

---

## 11. Migration Checklist

**When updating old code:**

- [ ] Remove all `any` types
- [ ] Check localStorage usage - migrate to sessionStorage if temporary
- [ ] Replace global variables with Context
- [ ] Add error boundaries
- [ ] Extract duplicate utilities
- [ ] Add React.memo to list items
- [ ] Run quality gates
- [ ] Update tests

---

## 12. Quick Reference

| Problem | Solution | Example File |
|---------|----------|--------------|
| `any` types | Define proper interfaces | `TaskSuccessContext.tsx` |
| Global variables | React Context with useRef | `TaskSuccessContext.tsx` |
| localStorage tokens | Use httpOnly cookies (Supabase) | `OAuthSuccessPage.tsx` |
| Duplicate formatters | Extract to shared utility | `lib/utils/formatters.ts` |
| Large components | Split into subcomponents | See section 4.1 |
| No error boundaries | Add ErrorBoundary wrapper | See section 5.1 |
| Slow list rendering | React.memo for items | See section 6.1 |
| Debug logging | Remove or gate with DEV check | `AuthPage.tsx` |

---

## 13. Search Patterns (Ripgrep)

```bash
# Find any types
rg ":\s*any\b" --type ts --type tsx web/src

# Find localStorage usage
rg "localStorage\." --type ts --type tsx web/src

# Find console.log in production code
rg "console\.(log|warn|info)" --type ts --type tsx web/src/pages web/src/components

# Find large components
find web/src -name "*.tsx" -exec wc -l {} \; | sort -rn | head -20

# Find components without error boundaries
rg "export (function|const)" web/src/pages --type tsx | grep -v ErrorBoundary
````

---

## 14. Enforcement

**AI Agents MUST:**

1. ✅ Run quality gates before committing
2. ✅ Follow these patterns exactly
3. ✅ Reference this document in PRs
4. ✅ Update this document if patterns evolve

**Reviewers MUST:**

1. ✅ Verify zero `any` types
2. ✅ Check for security issues
3. ✅ Confirm error boundaries exist
4. ✅ Validate component sizes
5. ✅ Ensure quality gates passed

---

## 15. Examples of Correct Implementation

### ✅ Complete Feature Example

See `web/src/contexts/TaskSuccessContext.tsx` for a fully compliant implementation:

- Zero `any` types (11 instances fixed)
- Proper TypeScript interfaces
- React Context with useRef pattern (no globals)
- Comprehensive WebSocket event typing
- Helper functions for data extraction
- Clean registration pattern for handlers

### ✅ Security Example

See `web/src/pages/OAuthSuccessPage.tsx` and `IntegrationsPage.tsx` for correct OAuth handling:

- sessionStorage for temporary window communication
- No tokens in JavaScript storage
- Supabase httpOnly cookies for auth
- Cleaned up console.log statements

### ✅ Shared Utilities Example

See `web/src/lib/utils/formatters.ts` for proper code extraction:

- Single source of truth
- Comprehensive documentation
- Exported for reuse
- Type-safe implementations

---

## Questions?

- **Type safety examples**: See `TaskSuccessContext.tsx`
- **Security patterns**: See `OAuthSuccessPage.tsx`, `IntegrationsPage.tsx`
- **Component structure**: See section 4.2
- **Performance**: See section 6
- **More patterns**: Search codebase for existing examples

**Remember: Security and type safety are non-negotiable.**

---

**Document Updated**: 2025-11-06  
**Based on**: Production fixes implementing zero-`any`, proper Context patterns, and security hardening  
**Next Review**: When new patterns emerge or standards evolve
