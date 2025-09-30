# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules
YOU MUST STRICTLY FOLLOW ./RULES.md

## Architecture Overview

PulsePlan is an AI-powered academic planning system with a **LangGraph multi-agent architecture**. The codebase has two main components:

- **Backend**: Python FastAPI application (`backend/`) with LangGraph workflows, agent orchestration, and complex scheduling optimization
- **Frontend**: React web application (`web/`) with TypeScript, Vite, and Tailwind CSS

The system uses **specialized AI agents** coordinated through LangGraph graphs to handle different workflows (chat, scheduling, calendar, tasks, briefings, search, database operations). The backend integrates with Canvas LMS, Google/Microsoft calendars, and provides advanced scheduling using constraint programming (OR-Tools).

## Development Commands

### Backend (Python)

```bash
cd backend

# Start development server
python main.py

# Run tests
pytest

# Code formatting and linting
black .
ruff check .

# Install dependencies
pip install -r requirements.txt
```

### Frontend (React Web)

```bash
cd web

# Start Vite development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Format code
npm run format

# Run tests
npm run test
```

### Testing and Verification

```bash
# Verify Supabase configuration
npm run verify-supabase

# Verify calendar integration
npm run verify-calendar
```

## Key Architectural Components

### LangGraph Agent System (`backend/app/agents/`)

- **Orchestrator** (`orchestrator.py`): Central workflow manager with isolation, error boundaries, and recovery
- **Graphs** (`graphs/`): Specialized workflow implementations (ChatGraph, TaskGraph, SchedulingGraph, etc.)
- **Tools** (`tools/`): 15+ specialized tools for different operations (calendar, email, tasks, memory, etc.)
- **Core** (`core/`): Advanced features like workflow containers, state management, and recovery services

### Scheduling Engine (`backend/app/scheduler/`)

- **Constraint Programming**: OR-Tools CP-SAT solver for optimal task assignment
- **Machine Learning**: Contextual bandits and completion prediction models
- **Optimization**: Multi-objective optimization balancing deadlines, preferences, and efficiency

### Memory System (`backend/app/memory/`)

- **Dual-layer architecture**: PostgreSQL vector storage + Redis ephemeral memory
- **Semantic search**: OpenAI embeddings with namespace organization
- **Auto-ingestion**: Automated processing of academic data

### Integration Services (`backend/app/services/`)

- **OAuth management**: Multi-provider token refresh and secure storage
- **Calendar sync**: Bidirectional Google/Microsoft Calendar integration
- **Canvas service**: Automated LMS synchronization

## Environment Configuration

The application requires several environment variables:

- `OPENAI_API_KEY`: OpenAI API access
- Supabase configuration for database
- Google/Microsoft OAuth credentials for integrations
- Canvas LMS API credentials
- Redis configuration for caching

Check `.env.example` files in `web/` and `backend/` directories for complete configuration requirements.

## Code Conventions

### Python Backend

- **Type hints**: Required for all function parameters and returns
- **Async/await**: Use throughout for database and API operations
- **Error handling**: Use custom `WorkflowError` class for agent errors
- **Logging**: Structured logging with correlation IDs

### React Web Frontend

- **TypeScript**: Strict type checking enabled
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing with React Router v6
- **Tailwind CSS**: Utility-first CSS framework with Radix UI components
- **TanStack Query**: Server state management and caching
- **React Hook Form**: Form handling with Zod validation
- **Contexts**: React contexts for state management in `src/contexts/`
- **Hooks**: Custom hooks in `src/hooks/` for API integration

## Agent Workflow Execution

When working with agent workflows:

1. **Entry point**: `AgentOrchestrator.execute_workflow()` or specific methods like `execute_natural_language_query()`
2. **State management**: Uses `WorkflowState` and `WorkflowContainer` for isolation
3. **Error boundaries**: All workflows run within error boundaries with automatic recovery
4. **Tool execution**: Agents select and execute tools based on input analysis

Example workflow types:

- `WorkflowType.NATURAL_LANGUAGE`: General chat and NLP processing
- `WorkflowType.SCHEDULING`: Intelligent task scheduling with optimization
- `WorkflowType.CALENDAR`: Calendar operations and sync
- `WorkflowType.TASK`: Task CRUD operations
- `WorkflowType.BRIEFING`: Daily briefing generation

## Database Schema

Uses Supabase (PostgreSQL) with Row Level Security:

- User management and authentication
- Task and todo storage with foreign key relationships
- OAuth token storage (encrypted)
- Vector embeddings for semantic memory
- Scheduling constraints and preferences

## Testing Strategy

- **Backend**: pytest with async support (`pytest-asyncio`)
- **Coverage**: Use `pytest-cov` for coverage reports
- **Mocking**: Mock external API calls (OpenAI, Google, Microsoft, Canvas)
- **Integration tests**: Test full workflow execution paths

## Performance Considerations

- **Redis caching**: Multi-layer caching strategy for API responses
- **Background jobs**: Async job processing for Canvas sync and analytics
- **Connection pooling**: Optimized database and Redis connections
- **Resource limits**: Workflow containers have configurable resource limits
- **Circuit breakers**: Protection against cascading failures

## WebSocket Integration

Real-time updates use Socket.IO:

- **WebSocket manager** (`app/core/websocket.py`): Central connection management
- **Agent status updates**: Live workflow execution status
- **Real-time notifications**: System events and job completions

## Security Requirements

- **Token encryption**: All OAuth tokens encrypted with user-specific keys
- **Row Level Security**: Database-level access control
- **Input validation**: Comprehensive Pydantic validation
- **Rate limiting**: Request throttling and abuse protection
- **CORS configuration**: Secure cross-origin resource sharing
