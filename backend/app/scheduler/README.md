# PulsePlan Scheduler Subsystem

## Overview

The PulsePlan Scheduler Subsystem is an intelligent task scheduling system that combines constraint satisfaction optimization with machine learning to generate optimal study and work schedules for users. The system uses OR-Tools for constraint solving, contextual bandits for adaptive parameter tuning, and logistic regression for completion probability prediction.

## Architecture

### Core Components

The scheduler subsystem follows a modular architecture with clear separation of concerns:

```
app/scheduler/
├── __init__.py                 # Package initialization and exports
├── README.md                  # This documentation
├── config.py                  # Configuration management
├── domain.py                  # Core domain models and types
├── features.py                # Feature extraction for ML models
├── service.py                 # Main orchestration service
├── telemetry.py               # Metrics, tracing, and observability
├── api.py                     # FastAPI REST endpoints
├── tools.py                   # LangGraph integration tools
├── optimization/              # Constraint satisfaction components
│   ├── __init__.py
│   ├── time_index.py         # Time discretization and indexing
│   ├── solver.py             # OR-Tools CP-SAT optimization
│   ├── constraints.py        # Constraint building helpers
│   ├── objective.py          # Objective function construction
│   └── fallback.py           # Greedy fallback scheduler
├── learning/                 # Machine learning components
│   ├── __init__.py
│   ├── model_store.py        # Model persistence layer
│   ├── completion_model.py   # Completion probability prediction
│   └── bandits.py            # Contextual bandit weight tuning
├── adapt/                    # Adaptive scheduling and rescheduling
│   ├── __init__.py
│   ├── rescheduler.py        # Missed task rescheduling strategies
│   ├── evaluator.py          # Schedule quality evaluation
│   └── updater.py            # Post-run learning updates
├── io/                       # Input/output and data management
│   ├── __init__.py
│   ├── dto.py                # Data transfer objects (Pydantic schemas)
│   ├── repository.py         # Data access layer
│   └── idempotency.py        # Request deduplication
└── tests/                    # Test suite
    └── ...
```

### Key Design Principles

- **Modular Design**: Each component has a single responsibility and clear interfaces
- **Async/Await**: Full asynchronous support for scalable concurrent operations
- **Type Safety**: Comprehensive type hints and Pydantic validation
- **Observability**: Built-in metrics, tracing, and structured logging
- **Extensibility**: Plugin architecture for new constraints and learning algorithms
- **Production Ready**: Error handling, fallbacks, and operational tooling

## Data Models

### Core Domain Objects

#### Task
Represents a schedulable unit of work with constraints and preferences:
- **Basic Properties**: ID, title, kind (study/assignment/exam/etc.), estimated duration
- **Scheduling Constraints**: Minimum/maximum block sizes, deadlines, earliest start times
- **Preferences**: Preferred time windows, avoided periods, importance weight
- **Dependencies**: Prerequisites, ordering constraints, course associations

#### BusyEvent  
Represents existing calendar commitments that constrain scheduling:
- **Time Bounds**: Start/end times with timezone awareness
- **Conflict Rules**: Hard (cannot overlap) vs soft (movable) constraints
- **Source Integration**: Google Calendar, Microsoft Outlook, internal events

#### Preferences
User-specific scheduling preferences and constraints:
- **Time Bounds**: Workday hours, daily effort limits, break patterns
- **Quality Preferences**: Deep work windows, context switching penalties
- **Learning Configuration**: Model update frequency, exploration rates

### Configuration Models

The system uses a hierarchical configuration system with environment-specific overrides:
- **Solver Configuration**: OR-Tools parameters, time limits, worker counts
- **Learning Configuration**: Model hyperparameters, update schedules
- **Telemetry Configuration**: Metrics collection, export settings
- **Infrastructure Configuration**: Database, cache, and API settings

## Scheduling Algorithm

### Constraint Satisfaction Framework

The core scheduling algorithm uses constraint programming to find optimal task assignments:

#### Hard Constraints (Must Be Satisfied)
- **Temporal Conflicts**: No overlaps with existing calendar events
- **Deadline Adherence**: All work completed before task deadlines
- **Block Size Limits**: Respect minimum and maximum contiguous work periods
- **Precedence Orders**: Dependencies between tasks honored
- **Capacity Limits**: Daily and weekly effort boundaries respected

#### Soft Constraints (Penalties in Objective)
- **Time Preferences**: Alignment with user's preferred work hours
- **Context Switching**: Penalties for frequent task changes
- **Fragmentation**: Preference for fewer, longer work blocks
- **Workload Balance**: Even distribution across days and weeks
- **Course Fairness**: Balanced attention across academic subjects

### Learning Layer

#### Completion Probability Prediction
A logistic regression model predicts the likelihood that a user will complete a task when scheduled at a specific time:
- **Features**: Time of day, day of week, task characteristics, historical patterns
- **Training**: Online learning from actual completion outcomes
- **Application**: Objective function incorporates expected utility = probability × task weight

#### Adaptive Weight Tuning
A contextual bandit algorithm automatically tunes penalty weights in the objective function:
- **Algorithm**: Thompson Sampling with Bayesian updates
- **Context**: User profile, time of day, workload characteristics
- **Reward Signal**: Based on completion rates, user satisfaction, and schedule stability
- **Exploration**: Balances exploitation of known good strategies with exploration of alternatives

### Optimization Process

1. **Input Processing**: Load tasks, calendar events, and user preferences
2. **Time Discretization**: Convert continuous time to discrete slots (15 or 30 minutes)
3. **Feature Extraction**: Generate ML features for all (task, time slot) combinations
4. **Weight Selection**: Bandit algorithm chooses penalty weights based on context
5. **Model Building**: Construct CP-SAT constraint satisfaction problem
6. **Optimization**: Solve with OR-Tools within configured time limit
7. **Fallback**: If optimization fails, use greedy heuristic scheduler
8. **Post-Processing**: Generate explanations and quality metrics
9. **Learning Updates**: Update ML models based on scheduling outcomes

## API Reference

### REST Endpoints

#### POST /api/v1/schedule/run
Execute scheduling for a user with full optimization.

**Request Body:**
```json
{
    "user_id": "string",
    "horizon_days": 7,
    "dry_run": false,
    "lock_existing": true,
    "options": {}
}
```

**Response:**
```json
{
    "job_id": "string",
    "feasible": true,
    "blocks": [
        {
            "task_id": "string",
            "title": "string", 
            "start": "2023-01-01T09:00:00Z",
            "end": "2023-01-01T10:30:00Z",
            "provider": "pulse",
            "metadata": {}
        }
    ],
    "metrics": {},
    "explanations": {}
}
```

#### POST /api/v1/schedule/preview
Generate schedule preview without persisting changes.

#### POST /api/v1/schedule/reschedule
Reschedule missed or problematic tasks with increased urgency.

#### GET /api/v1/schedule/health
Get system health status and component diagnostics.

#### GET /api/v1/schedule/metrics
Retrieve performance and usage metrics for monitoring.

### LangGraph Tools

#### scheduling_tool
Primary tool for AI agents to generate optimized schedules.

**Parameters:**
- `user_id`: User identifier
- `horizon_days`: Scheduling horizon (1-30 days)
- `dry_run`: Preview mode flag
- `lock_existing`: Preserve existing blocks flag
- `options`: Additional configuration options

**Returns:**
```python
{
    "success": bool,
    "feasible": bool,
    "schedule": {...},
    "metrics": {...},
    "insights": [...],
    "explanations": {...}
}
```

#### reschedule_tool
Intelligent rescheduling for missed or conflicting tasks.

#### schedule_analysis_tool
Performance analysis and optimization recommendations.

#### preference_update_tool
Update user preferences with impact analysis and optional rescheduling.

## Configuration

### Environment Variables

The system supports configuration through environment variables with the `SCHEDULER_` prefix:

```bash
# Core Settings
SCHEDULER_ENVIRONMENT=production
SCHEDULER_GRANULARITY=30
SCHEDULER_MAX_HORIZON=30

# Solver Configuration
SCHEDULER_SOLVER_TIME_LIMIT=10
SCHEDULER_SOLVER_WORKERS=4

# Learning Configuration  
SCHEDULER_LEARNING_LR=0.05
SCHEDULER_BANDIT_EXPLORATION=0.1

# Infrastructure
SCHEDULER_CACHE_BACKEND=redis
SCHEDULER_REDIS_URL=redis://localhost:6379
SCHEDULER_DB_BACKEND=postgresql
SCHEDULER_DB_CONNECTION=postgresql://user:pass@localhost/db

# Observability
SCHEDULER_LOG_LEVEL=INFO
SCHEDULER_METRICS_ENABLED=true
SCHEDULER_TRACING_ENABLED=true
```

### Configuration Files

Configuration can also be provided via YAML or JSON files:

```yaml
# scheduler.yaml
environment: production
time_granularity_minutes: 30
max_horizon_days: 30

solver:
  time_limit_seconds: 10
  num_search_workers: 4
  
learning:
  completion_model_lr: 0.05
  bandit_exploration_rate: 0.1
  
default_weights:
  context_switch: 2.0
  avoid_window: 1.5
  late_night: 3.0
```

## Deployment

### Dependencies

Core dependencies managed through requirements:
- **fastapi**: REST API framework
- **pydantic**: Data validation and serialization
- **ortools**: Constraint satisfaction optimization
- **scikit-learn**: Machine learning algorithms
- **numpy**: Numerical computing
- **asyncio**: Asynchronous programming support
- **pytz**: Timezone handling

Optional dependencies for production:
- **redis**: Distributed caching
- **postgresql**: Production database
- **prometheus-client**: Metrics export
- **jaeger-client**: Distributed tracing

### Environment Setup

Development environment:
```bash
# Install dependencies
pip install -r requirements.txt

# Set development configuration
export SCHEDULER_ENVIRONMENT=development
export SCHEDULER_LOG_LEVEL=DEBUG

# Run with hot reload
uvicorn app.main:app --reload
```

Production environment:
```bash
# Production dependencies
pip install -r requirements-prod.txt

# Production configuration
export SCHEDULER_ENVIRONMENT=production
export SCHEDULER_CACHE_BACKEND=redis
export SCHEDULER_DB_BACKEND=postgresql

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Monitoring and Observability

### Metrics Collection

The system emits comprehensive metrics for monitoring:

#### Performance Metrics
- `scheduler.run.duration` - Time to generate schedules
- `scheduler.solve.time_ms` - Optimization solver time
- `scheduler.solve.status` - Success/failure rates
- `scheduler.fallback.rate` - Fallback scheduler usage

#### Quality Metrics  
- `scheduler.completion_rate` - Task completion rates
- `scheduler.satisfaction.score` - User satisfaction
- `scheduler.reschedule.rate` - Rescheduling frequency
- `scheduler.objective.value` - Optimization objective scores

#### System Metrics
- `scheduler.requests.rate` - API request rates
- `scheduler.cache.hit_rate` - Cache effectiveness
- `scheduler.learning.updates` - Model update frequency

### Distributed Tracing

Request flows are traced across components:
- **Trace Context**: Propagated through async calls
- **Span Annotations**: Key operations and decisions
- **Error Tracking**: Exception capture and analysis
- **Performance Analysis**: Bottleneck identification

### Structured Logging

All components use structured logging with correlation IDs:
```python
logger.info("Schedule generated", 
    user_id=user_id, 
    feasible=result.feasible, 
    blocks=len(result.blocks),
    solve_time_ms=result.solve_time_ms)
```

## Testing

### Test Categories

#### Unit Tests
- Domain model validation
- Algorithm correctness
- Configuration handling
- Error conditions

#### Integration Tests  
- End-to-end scheduling workflows
- Database persistence
- API endpoint functionality
- ML model training and inference

#### Performance Tests
- Optimization solver scaling
- API response times
- Memory usage patterns
- Concurrent user handling

#### Property Tests
- Constraint satisfaction verification
- Schedule feasibility checking
- ML model convergence
- Configuration validation

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests  
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v --benchmark-only

# Coverage report
pytest --cov=app.scheduler --cov-report=html
```

## Troubleshooting

### Common Issues

#### Scheduling Failures
- **Infeasible Problems**: Check for conflicting deadlines or insufficient time
- **Solver Timeouts**: Reduce complexity or increase time limits
- **Poor Quality**: Review penalty weights and user preferences

#### Performance Issues
- **Slow Response Times**: Check solver configuration and database queries
- **Memory Usage**: Monitor feature matrix size and model storage
- **Cache Misses**: Verify cache configuration and key generation

#### Integration Problems
- **Calendar Sync**: Check API credentials and permission scopes
- **Database Connections**: Verify connection strings and network access
- **Model Loading**: Check file permissions and storage backend

### Diagnostic Tools

#### Health Endpoints
- `/api/v1/schedule/health` - Component status
- `/api/v1/schedule/metrics` - Performance data
- `/api/v1/schedule/diagnostics` - Detailed analysis

#### Configuration Export
```bash
curl -X GET "http://localhost:8000/api/v1/schedule/config/export?format=yaml"
```

#### Log Analysis
```bash
# Search for scheduling errors
grep "ERROR.*scheduling" /var/log/scheduler.log

# Analyze performance patterns
grep "Schedule generated" /var/log/scheduler.log | jq '.solve_time_ms'
```

## Contributing

### Development Workflow

1. **Setup Development Environment**
   ```bash
   git clone <repository>
   cd backend/app/scheduler
   pip install -r requirements-dev.txt
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-constraint-type
   ```

3. **Implement Changes**
   - Add tests first (TDD approach)
   - Implement feature with type hints
   - Update documentation

4. **Validate Changes**
   ```bash
   pytest tests/
   mypy app/scheduler/
   black app/scheduler/
   flake8 app/scheduler/
   ```

5. **Submit Pull Request**
   - Clear description of changes
   - Reference related issues
   - Include performance impact analysis

### Code Standards

- **Type Hints**: All functions must have complete type annotations
- **Documentation**: Docstrings for all public methods and classes
- **Error Handling**: Comprehensive exception handling with structured logging
- **Testing**: Minimum 80% code coverage with meaningful tests
- **Performance**: No regressions in scheduling time or memory usage

### Architecture Decisions

Major architectural changes require documentation in `docs/architecture/` with:
- **Problem Statement**: What issue does the change address
- **Alternatives Considered**: Other approaches evaluated
- **Decision Rationale**: Why this approach was chosen
- **Implementation Plan**: Staged rollout strategy
- **Success Metrics**: How to measure success

## License

This scheduler subsystem is part of the PulsePlan project and follows the main project's licensing terms.