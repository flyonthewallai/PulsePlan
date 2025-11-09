# Development Documentation

**Essential guides and best practices for daily development work.**

## Documents in this Directory

### [`WEB_RULES.md`](./WEB_RULES.md) ⭐ **NEW**

**Critical rules for web application development**

**Contents:**

- **Type Safety**: Zero `any` types policy, proper TypeScript patterns
- **Security**: sessionStorage vs localStorage, token handling, input validation
- **React Patterns**: Context over globals, custom hooks, proper dependency arrays
- **Component Organization**: File size limits, structure, duplicate extraction
- **Error Handling**: Error boundaries (required), try-catch patterns
- **Performance**: React.memo, useMemo, useCallback optimization
- **API Integration**: TanStack Query patterns, cache keys
- **Testing**: Component, hook, and utility tests
- **Quality Gates**: Linting, type-checking, build requirements

**When to use:** **Required reading for ALL web/frontend changes**

---

### [`SERVICE_LAYER_PATTERNS.md`](./SERVICE_LAYER_PATTERNS.md) 🏗️

**Service layer architecture and best practices**

**Contents:**

- Service layer responsibilities and patterns
- Service template with full example
- Dependency injection patterns (endpoints, tools, services)
- Error handling with ServiceError
- Common service patterns (list, get, create, update)
- Testing services with mocked repositories
- Migration checklist from repository to service layer
- Anti-patterns to avoid

**When to use:** Creating new services, refactoring direct repository access, understanding architecture layers

---

### [`TESTING.md`](./TESTING.md) 🧪

**Test strategy and coverage requirements**

**Contents:**

- Test categories (Unit, Integration, Guardrail)
- Coverage requirements by component
- Guardrail tests for critical invariants
- Test file conventions and directory structure
- Test patterns by layer (repository, service, API, agent)
- Test data and fixtures
- CI/CD integration
- Pre-commit hooks

**When to use:** Writing tests, setting up CI/CD, understanding test strategy

---

### [`EXAMPLES.md`](./EXAMPLES.md) 📚

**Reference implementation patterns**

**Contents:**

- Repository pattern with complete example
- Service pattern with business logic
- API endpoint pattern with FastAPI
- Agent tool pattern
- Agent workflow pattern with LangGraph
- Intent classification pattern
- Scheduling pattern
- Test patterns (unit, integration)

**When to use:** Implementing new features, learning patterns, copy-paste reference

---

### [`PITFALLS.md`](./PITFALLS.md) ⚠️

**Common mistakes and known issues**

**Contents:**

- Intent classification pitfalls
- OR-Tools constraint issues
- Context fetching problems
- Database operation mistakes
- Calendar sync issues
- Authentication & security pitfalls
- Agent workflow issues
- Frontend/API integration problems
- Known bugs fixed (with dates)

**When to use:** Debugging issues, avoiding common mistakes, understanding edge cases

---

### [`STYLES.md`](./STYLES.md) 🎨

**Frontend design system and styling guide**

**Contents:**

- Design tokens system (colors, typography, spacing)
- Component styling patterns
- Tailwind CSS configuration
- Color accessibility guidelines
- Responsive design patterns
- Animation utilities
- UI component library reference
- Design system best practices

**When to use:** Building UI components, ensuring consistent styling, frontend development

---

## Development Workflow

### Before Writing Code:

**Backend:**

1. Read [RULES.md](../02-architecture/RULES.md) for enforcement rules
2. Check [`EXAMPLES.md`](./EXAMPLES.md) for existing patterns
3. Review [`PITFALLS.md`](./PITFALLS.md) for common mistakes
4. Plan tests using [`TESTING.md`](./TESTING.md)

**Frontend:**

1. **Read [`WEB_RULES.md`](./WEB_RULES.md)** - **REQUIRED** for all web changes
2. Review [`STYLES.md`](./STYLES.md) for design system tokens
3. Check [`EXAMPLES.md`](./EXAMPLES.md) for patterns
4. Review [`PITFALLS.md`](./PITFALLS.md) for common mistakes

### While Writing Code:

**Backend:**

1. Follow patterns from [`EXAMPLES.md`](./EXAMPLES.md)
2. Use service layer per [`SERVICE_LAYER_PATTERNS.md`](./SERVICE_LAYER_PATTERNS.md)
3. Write tests per [`TESTING.md`](./TESTING.md)
4. Avoid pitfalls from [`PITFALLS.md`](./PITFALLS.md)

**Frontend:**

1. **Follow [`WEB_RULES.md`](./WEB_RULES.md)** patterns strictly
2. Use design tokens from [`STYLES.md`](./STYLES.md)
3. Write tests per [`TESTING.md`](./TESTING.md)
4. Avoid pitfalls from [`PITFALLS.md`](./PITFALLS.md)

### Before Committing:

**Backend:**

```bash
cd backend
ruff check .      # Linting
black .           # Formatting
mypy .            # Type checking
pytest            # All tests
```

**Frontend:**

```bash
cd web
npm run lint        # ESLint - MUST PASS
npm run type-check  # TypeScript - MUST PASS
npm run test        # Vitest - MUST PASS
npm run build       # Build check - MUST PASS
```

All quality gates **MUST PASS** before committing.

---

## Quick Reference

### Backend

| Task             | Read This                                                | Pattern File                 |
| ---------------- | -------------------------------------------------------- | ---------------------------- |
| New API endpoint | [RULES.md](../02-architecture/RULES.md)                  | [EXAMPLES.md](./EXAMPLES.md) |
| New service      | [SERVICE_LAYER_PATTERNS.md](./SERVICE_LAYER_PATTERNS.md) | [EXAMPLES.md](./EXAMPLES.md) |
| New repository   | [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)    | [EXAMPLES.md](./EXAMPLES.md) |
| Agent tool       | [RULES.md](../02-architecture/RULES.md)                  | [EXAMPLES.md](./EXAMPLES.md) |
| Tests            | [TESTING.md](./TESTING.md)                               | [EXAMPLES.md](./EXAMPLES.md) |

### Frontend

| Task               | Read This                             | Pattern File                             |
| ------------------ | ------------------------------------- | ---------------------------------------- |
| **Any web change** | **[WEB_RULES.md](./WEB_RULES.md)** ⭐ | **Required**                             |
| New component      | [WEB_RULES.md](./WEB_RULES.md)        | Section 4                                |
| Type safety        | [WEB_RULES.md](./WEB_RULES.md)        | Section 1                                |
| Security           | [WEB_RULES.md](./WEB_RULES.md)        | Section 2                                |
| Performance        | [WEB_RULES.md](./WEB_RULES.md)        | Section 6                                |
| Styling            | [STYLES.md](./STYLES.md)              | Design tokens                            |
| Tests              | [TESTING.md](./TESTING.md)            | [WEB_RULES.md](./WEB_RULES.md) Section 8 |

---

## For AI Assistants

### Critical Reading

1. **Backend**: [RULES.md](../02-architecture/RULES.md) + [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)
2. **Frontend**: [WEB_RULES.md](./WEB_RULES.md) - **MANDATORY for all web changes**
3. **Quick ref**: [CLAUDE.md](../03-ai-agents/CLAUDE.md)

### Web Changes Enforcement

**BEFORE making ANY web change:**

- ✅ Read [WEB_RULES.md](./WEB_RULES.md)
- ✅ Verify zero `any` types
- ✅ Check security patterns (no localStorage for tokens)
- ✅ Follow React patterns (Context, not globals)
- ✅ Run quality gates

**These patterns are MANDATORY** - See WEB_RULES.md for complete enforcement.

---

## Recently Updated

- **2025-11-06**: Added [WEB_RULES.md](./WEB_RULES.md) - Critical web development standards
- **2025-11-05**: Updated repository organization patterns
- **2025-11-05**: Added SERVICE_LAYER_PATTERNS.md

---

**Last Updated:** 2025-11-06
