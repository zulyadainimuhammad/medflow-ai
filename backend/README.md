# Backend Foundation

FastAPI engineering scaffold for MedFlow AI.

## What Is Included
- FastAPI app bootstrap with versioned API prefix.
- Health check endpoints:
	- GET /api/v1/health/live
	- GET /api/v1/health/ready
- Environment configuration through pydantic-settings.
- Python quality toolchain: Ruff, Black, isort, mypy.
- Pytest base configuration and health route tests.
- Dockerfile for local and CI container builds.

## Quick Start
1. Install dependencies:
```bash
pip install -e .[dev]
```
2. Run the service:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
3. Run quality checks:
```bash
ruff check app tests
black --check app tests
isort --check-only app tests
mypy app
pytest
```

## Scope Boundary
This backend contains foundation infrastructure only. No domain business logic or feature modules are implemented yet.
