# Development Workflow Guide

**Daily development commands, workflows, and best practices for PulsePlan.**

**Last Updated:** 11/05/25

---

## Quick Command Reference

### Backend Commands

```bash
cd backend

# Start development server
python main.py

# Run tests
pytest                          # All tests
pytest tests/unit/             # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m guardrail             # Critical invariant tests
pytest -v                       # Verbose output
pytest --cov=app               # With coverage

# Code quality
black .                         # Format code
ruff check .                    # Lint code
ruff check . --fix              # Lint and auto-fix
mypy app/                       # Type checking

# Database
python scripts/apply_migration.py   # Apply migrations
```

### Frontend Commands

```bash
cd web

# Start development server
npm run dev                     # Start Vite dev server
npm run dev -- --host          # Expose to network

# Build and preview
npm run build                   # Production build
npm run preview                 # Preview production build

# Code quality
npm run lint                    # Run ESLint
npm run lint:fix                # Fix ESLint issues
npm run format                  # Run Prettier
npm run type-check              # TypeScript check

# Testing
npm test                        # Run tests
npm test -- --watch            # Watch mode
npm test -- --coverage         # With coverage
```

---

## Development Server

### Starting the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```
Runs on: `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd web
npm run dev
```
Runs on: `http://localhost:5173`

**Terminal 3 - Redis (if needed):**
```bash
redis-server
```

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Uvicorn auto-reloads on file changes
- **Frontend**: Vite HMR (Hot Module Replacement)

---

## Testing

### Backend Testing Strategy

See [../04-development/TESTING.md](../04-development/TESTING.md) for complete strategy.

**Quick testing workflow:**

```bash
cd backend

# Before committing - run guardrail tests
pytest -m guardrail --maxfail=1

# Run specific test file
pytest tests/unit/test_task_repository.py

# Run specific test
pytest tests/unit/test_task_repository.py::test_create_task

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Frontend Testing

```bash
cd web

# Run all tests
npm test

# Watch mode (recommended during development)
npm test -- --watch

# Run specific test file
npm test -- TaskItem.test.tsx

# Coverage report
npm test -- --coverage
```

---

## Code Quality

### Before Every Commit

**Backend:**
```bash
cd backend
black .                    # Format
ruff check . --fix        # Lint and fix
pytest -m guardrail       # Critical tests
```

**Frontend:**
```bash
cd web
npm run lint:fix          # Fix linting issues
npm run format            # Format code
npm test                  # Run tests
```

### Pre-commit Checklist

- [ ] Code formatted (Black/Prettier)
- [ ] No linting errors (Ruff/ESLint)
- [ ] All tests pass
- [ ] **Guardrail tests pass** (backend)
- [ ] Type checking passes
- [ ] No `console.log` left in code (frontend)
- [ ] Followed [RULES.md](../02-architecture/RULES.md)

---

## Git Workflow

### Branch Naming

```
feature/add-task-scheduling
bugfix/calendar-sync-issue
hotfix/critical-auth-bug
docs/update-setup-guide
refactor/simplify-repository-layer
```

### Commit Messages

Follow conventional commits:

```
feat: add task scheduling optimization
fix: resolve calendar sync race condition
docs: update setup guide with Redis instructions
refactor: simplify repository pattern
test: add guardrail tests for scheduling
chore: update dependencies
```

### Typical Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-new-feature

# 2. Make changes and commit frequently
git add .
git commit -m "feat: add initial implementation"

# 3. Run quality checks before pushing
cd backend && black . && ruff check . --fix && pytest
cd ../web && npm run lint:fix && npm test

# 4. Push to remote
git push origin feature/my-new-feature

# 5. Create pull request on GitHub
```

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Create endpoint**: `backend/app/api/v1/endpoints/your_endpoint.py`
2. **Add route**: Register in `backend/app/api/v1/api.py`
3. **Create service**: `backend/app/services/your_service.py`
4. **Add tests**: `backend/tests/integration/api/test_your_endpoint.py`
5. **Update docs**: Document in relevant system docs

See [../04-development/EXAMPLES.md](../04-development/EXAMPLES.md) for patterns.

### Adding a New Repository

1. **Create file**: `backend/app/database/repositories/{domain}_repositories/your_repository.py`
2. **Extend BaseRepository**
3. **Add factory function** (if needed)
4. **Update `__init__.py`** in domain folder
5. **Update** `repositories/__init__.py`
6. **Document in** [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md)

### Adding a Frontend Component

1. **Create component**: `web/src/components/YourComponent.tsx`
2. **Use design tokens**: Import from `@/lib/design-tokens`
3. **Add tests**: `web/src/__tests__/unit/components/YourComponent.test.tsx`
4. **Follow patterns**: See [../04-development/STYLES.md](../04-development/STYLES.md)

### Adding a Database Migration

```bash
cd backend

# Create migration file
touch migrations/YYYYMMDD_HHMMSS_description.sql

# Write SQL migration
cat > migrations/20251105_120000_add_new_table.sql << 'SQL'
-- Add your migration SQL here
CREATE TABLE new_table (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
SQL

# Apply migration
python scripts/apply_migration.py
```

---

## Debugging

### Backend Debugging

**Print debugging:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"User context: {user_context}")
logger.error(f"Error occurred: {e}", exc_info=True)
```

**Interactive debugging (pdb):**
```python
import pdb; pdb.set_trace()  # Breakpoint
```

**VS Code debugger:**

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend",
      "env": {"PYTHONPATH": "${workspaceFolder}/backend"}
    }
  ]
}
```

### Frontend Debugging

**Browser DevTools:**
- `F12` or `Cmd+Option+I` to open
- Use React DevTools extension
- Check Network tab for API calls
- Use Console for errors

**React Query DevTools:**
Already installed - opens automatically in dev mode (bottom-left corner)

**VS Code debugger:**

In `launch.json`:
```json
{
  "name": "Chrome: Launch",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:5173",
  "webRoot": "${workspaceFolder}/web/src"
}
```

---

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Import errors:**
```bash
# Ensure you're in backend directory
cd backend
# Reinstall dependencies
pip install -r requirements.txt
```

**Database connection errors:**
```bash
# Check environment variables
cat .env | grep SUPABASE
# Test connection
python -c "from app.database.manager import get_db; import asyncio; asyncio.run(get_db())"
```

### Frontend Issues

**Module not found:**
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

**Vite build errors:**
```bash
# Clear Vite cache
rm -rf web/node_modules/.vite
npm run dev
```

**Type errors:**
```bash
npm run type-check
# Fix issues, then:
npm run dev
```

### Redis Issues

**Connection refused:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
docker start redis         # Docker
```

---

## Performance Tips

### Backend

- Use async/await throughout
- Leverage Redis caching for repeated queries
- Use connection pooling for database
- Profile with `cProfile` for slow endpoints

### Frontend

- Use React Query for data caching
- Lazy load components with `React.lazy()`
- Use design tokens (avoid arbitrary Tailwind classes)
- Monitor bundle size: `npm run build -- --stats`

---

## Environment-Specific Configurations

### Development

```env
# backend/.env
DEBUG=True
LOG_LEVEL=DEBUG

# web/.env
VITE_API_BASE_URL=http://localhost:8000
```

### Production

```env
# backend/.env
DEBUG=False
LOG_LEVEL=INFO

# web/.env
VITE_API_BASE_URL=https://api.pulseplan.com
```

---

## Daily Development Checklist

### Morning Routine

- [ ] Pull latest changes: `git pull origin main`
- [ ] Update dependencies: `pip install -r requirements.txt` / `npm install`
- [ ] Start dev servers
- [ ] Check if tests pass

### Before Lunch Break / End of Day

- [ ] Commit work in progress
- [ ] Push to remote branch
- [ ] Update ticket/issue status

### Before Creating PR

- [ ] Run full test suite
- [ ] Check code quality (Black, Ruff, ESLint)
- [ ] Review [../02-architecture/RULES.md](../02-architecture/RULES.md)
- [ ] Update documentation if needed
- [ ] Test feature end-to-end manually

---

## IDE Tips (VS Code)

### Useful Shortcuts

- `Cmd+P` / `Ctrl+P` - Quick file open
- `Cmd+Shift+F` / `Ctrl+Shift+F` - Search in files
- `F12` - Go to definition
- `Shift+F12` - Find all references
- `Cmd+.` / `Ctrl+.` - Quick fix
- `Cmd+Shift+P` / `Ctrl+Shift+P` - Command palette

### Multi-root Workspace

Create `pulseplan.code-workspace`:
```json
{
  "folders": [
    {"path": "./backend"},
    {"path": "./web"}
  ],
  "settings": {
    "python.defaultInterpreterPath": "./backend/venv/bin/python"
  }
}
```

---

## Resources

### Documentation
- [Architecture](../02-architecture/ARCHITECTURE.md) - System design
- [Rules](../02-architecture/RULES.md) - Coding standards
- [Examples](../04-development/EXAMPLES.md) - Code patterns
- [Testing](../04-development/TESTING.md) - Test strategy
- [Styles](../04-development/STYLES.md) - Design system

### External
- FastAPI: https://fastapi.tiangolo.com
- React: https://react.dev
- Vite: https://vitejs.dev
- Supabase: https://supabase.com/docs
- Tailwind CSS: https://tailwindcss.com

---

**Last Updated:** 11/05/25
**Questions?** Ask the team or check [README.md](./README.md)
