# Environment Setup Guide

**Complete guide to setting up PulsePlan development environment.**

**Last Updated:** 11/05/25

---

## Prerequisites

### Required Software

**Backend:**
- Python 3.11+
- pip (Python package manager)
- PostgreSQL (via Supabase)
- Redis (for caching)

**Frontend:**
- Node.js 18+ (LTS recommended)
- npm 9+ (comes with Node.js)

**Development Tools:**
- Git
- Code editor (VS Code recommended)
- Terminal/Command line

### Recommended Tools

- **ngrok** - For webhook development (Google Calendar webhooks)
- **Postman/Insomnia** - API testing
- **pgAdmin/DBeaver** - Database management (optional)

---

## 1. Clone the Repository

```bash
git clone <repository-url>
cd PulsePlan
```

---

## 2. Backend Setup

### Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Recommended:** Use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

Create `backend/.env` file:

```bash
# Copy example file
cp .env.example .env
```

**Required variables:**

```env
# AI & LLM
OPENAI_API_KEY=sk-...

# Database & Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
REDIS_URL=redis://localhost:6379

# OAuth & Integrations
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
CANVAS_API_KEY=...
CANVAS_BASE_URL=https://canvas.instructure.com

# Calendar Webhooks
GOOGLE_WEBHOOK_VERIFICATION_TOKEN=<generate-random-string>
API_BASE_URL=http://localhost:8000  # Use ngrok URL for webhooks

# Security
SECRET_KEY=<generate-random-string>
ENCRYPTION_KEY=<generate-via-encryption-service>
```

**Generate random strings:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 3. Database Setup (Supabase)

### Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Copy URL and service role key to `.env`

### Run Migrations

```bash
cd backend

# Apply all migrations
python -m scripts.apply_migration

# Or manually via Supabase dashboard:
# Go to SQL Editor → New Query → Paste schema from:
cat app/database/schemas/schema.sql
```

### Verify Tables Created

Check Supabase dashboard → Table Editor:
- `users`
- `tasks`, `todos`, `tags`
- `oauth_tokens`
- `calendar_calendars`, `calendar_events`, `calendar_links`
- `memory_entries`
- `canvas_courses`, `canvas_assignments`

---

## 4. Redis Setup

### Option A: Docker (Recommended)

```bash
docker run -d -p 6379:6379 redis:latest
```

### Option B: Install Locally

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows:**
Use Docker or WSL2

### Verify Redis

```bash
redis-cli ping
# Should return: PONG
```

---

## 5. Frontend Setup

### Install Dependencies

```bash
cd web
npm install
```

### Configure Environment Variables

Create `web/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

---

## 6. Start Development Servers

### Terminal 1: Backend

```bash
cd backend
python main.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Frontend

```bash
cd web
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Terminal 3: Redis (if not using Docker)

```bash
redis-server
```

---

## 7. Verification Steps

### Backend Health Check

```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Test Database Connection

```bash
cd backend
python -c "
from app.database.manager import get_db
import asyncio

async def test():
    db = await get_db()
    print('Database connected!')

asyncio.run(test())
"
```

### Frontend Access

Open browser: `http://localhost:5173`

Should see PulsePlan login page

### Run Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd web
npm test
```

---

## 8. Optional: Webhook Development

For Google Calendar webhooks (development only):

### Install ngrok

```bash
# macOS
brew install ngrok

# Or download from ngrok.com
```

### Start ngrok

```bash
ngrok http 8000
```

### Update Environment

In `backend/.env`:
```env
API_BASE_URL=https://your-ngrok-url.ngrok.io
```

Restart backend server.

---

## 9. IDE Setup (VS Code Recommended)

### Recommended Extensions

**Python:**
- Python (Microsoft)
- Pylance
- Black Formatter
- Ruff

**Frontend:**
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- TypeScript Vue Plugin (Volar)

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## 10. Verify Installation

Run the verification script:

```bash
cd backend
python -c "
import sys
import importlib.util

def check_package(name):
    spec = importlib.util.find_spec(name)
    return spec is not None

packages = [
    'fastapi', 'uvicorn', 'supabase', 'redis',
    'openai', 'ortools', 'langchain', 'langgraph'
]

print('Backend Dependencies:')
for pkg in packages:
    status = '✅' if check_package(pkg) else '❌'
    print(f'{status} {pkg}')

print(f'\n✅ Python version: {sys.version}')
"
```

```bash
cd web
npm list --depth=0
```

---

## Common Setup Issues

### Issue: ModuleNotFoundError

**Solution:** Reinstall dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Issue: Supabase connection failed

**Solution:** Check environment variables
```bash
# Verify .env file exists and has correct values
cat backend/.env | grep SUPABASE
```

### Issue: Redis connection refused

**Solution:** Start Redis server
```bash
# Check if Redis is running
redis-cli ping

# If not, start it
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### Issue: Port already in use

**Solution:** Kill process on port
```bash
# Find process on port 8000
lsof -ti:8000 | xargs kill -9

# Find process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Issue: npm install fails

**Solution:** Clear cache and retry
```bash
cd web
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

---

## Next Steps

✅ **Setup complete!** Now proceed to:

1. [DEVELOPMENT.md](./DEVELOPMENT.md) - Learn daily workflow
2. [../02-architecture/ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) - Understand system design
3. [../02-architecture/RULES.md](../02-architecture/RULES.md) - Review coding standards

---

## Additional Resources

- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev
- **Vite Docs**: https://vitejs.dev

---

**Last Updated:** 11/05/25
**Need Help?** Check [README.md](./README.md) or ask the team
