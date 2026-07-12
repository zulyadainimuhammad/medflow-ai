# Developer Onboarding - MedFlow AI

## 1. Welcome
Welcome to MedFlow AI. This onboarding guide helps new engineers become productive while maintaining healthcare-grade reliability, security, and quality.

Engineering expectations:
- Build with patient flow safety and operational reliability in mind.
- Respect domain boundaries and role-based workflow constraints.
- Ship traceable, tested, and reviewable increments.

## 2. Access and Accounts
Before writing code, ensure the following are complete:
- GitHub repository access.
- Organization SSO and MFA enabled.
- Access to GitHub Actions logs and deployment artifacts.
- Azure non-production access (as required by role).
- Access to secret management workflow (without direct secret export).

Required policy acknowledgments:
- Secure coding policy.
- Data handling policy for regulated healthcare data.
- Incident escalation and on-call etiquette.

## 3. Local Development Environment Setup
### Tooling Baseline
- Git
- Node.js 20+
- Python 3.12+
- Docker and Docker Compose
- PostgreSQL client tools

### Clone and Bootstrap
```bash
git clone <repo-url>
cd medflow-ai
```

Create local environment files:
- frontend/.env.local
- backend/.env

Run local stack:
```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend pytest -m smoke
```

Optional local non-container runs:
```bash
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

## 4. Architecture and Domain Orientation
Read in this order:
1. docs/product/product-vision.md
2. docs/product/product-requirements-document.md
3. docs/architecture/system-architecture.md
4. docs/architecture/database-design.md
5. docs/engineering/security-guidelines.md

Domain ownership model:
- frontend: role-specific user experiences.
- backend: domain APIs and workflow orchestration.
- database: schema, integrity, and migrations.
- infrastructure: deployment and runtime operations.

## 5. Daily Development Workflow
1. Pull latest main branch.
2. Create branch: feature/<scope> or fix/<scope>.
3. Implement changes with tests.
4. Run lint, type checks, and tests locally.
5. Open pull request with required template fields.
6. Address review feedback and ensure CI passes.

## 6. Quality and Security Baseline
Before merge, every PR must:
- Pass linting and formatting checks.
- Pass unit and relevant integration tests.
- Include test coverage for new logic.
- Include documentation updates for behavior changes.
- Pass dependency and secret scanning checks.

Data safety rules:
- Never commit PHI, credentials, or production exports.
- Use synthetic/anonymized data for tests.

## 7. First Week Plan
- Day 1: Environment setup, architecture walkthrough, and access verification.
- Day 2: Review one merged PR in each major domain.
- Day 3: Deliver first low-risk issue with full test and doc updates.
- Day 4: Pair on workflow-critical module change.
- Day 5: Present implementation summary and lessons learned.

## 8. Common Setup Issues
- Docker containers fail to start: verify local port conflicts and restart Docker daemon.
- Migration errors: reset local database volume and rerun migrations.
- Auth failures: verify JWT env values and system clock synchronization.

## 9. Support and Escalation
- Engineering support: platform and domain leads in repository discussions.
- Security concerns: follow SECURITY.md reporting process.
- Release blockers: escalate to release manager and on-call platform engineer.
