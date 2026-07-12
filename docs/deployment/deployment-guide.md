# Deployment Guide - MedFlow AI

## 1. Overview
This guide defines how MedFlow AI is built, tested, and deployed from local development to Azure production using Docker and GitHub Actions. It supports controlled releases for diagnostic workflow services with audit-ready change evidence.

## 2. Environment Matrix
| Environment | Purpose | URL/Region | Owner | Change Window |
|---|---|---|---|---|
| Local Dev | Developer feature implementation and debugging | localhost | Feature Team | Any time |
| Integration | Shared integration and API contract validation | Azure West Europe (non-prod) | Platform Engineering | Weekdays |
| Staging | Pre-production validation, UAT, and release rehearsal | Azure West Europe (staging) | Platform + QA | Weekdays + release freeze windows |
| Production | Live hospital operations | Azure West Europe (prod primary) | SRE + Operations | Approved release windows only |

## 3. Prerequisites
- Repository access with required permissions.
- Docker and Docker Compose installed.
- Python 3.12 and Node.js 20 for local non-container workflows.
- Azure subscription access and service principal for CI/CD.
- GitHub Actions secrets configured for deployment credentials.
- Security and operations approval for production releases.

## 4. Local Development Setup
1. Clone repository and create branch.
2. Create local env files for frontend and backend.
3. Start dependencies and services with Docker Compose.
4. Run migrations and seed baseline role/permission data.
5. Validate health endpoints and smoke tests.

Example startup command set:
```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend pytest -m smoke
```

## 5. Docker Deployment Model
- Services:
	- frontend (Next.js)
	- backend (FastAPI)
	- postgres (managed externally in staging/prod)
	- optional worker for async notifications/analytics jobs
- Images are versioned by git SHA and semantic release tag.
- Base images must be pinned and scanned for vulnerabilities.

## 6. GitHub Actions CI/CD Workflow
### CI Pipeline (on pull request and main push)
1. Checkout and dependency install.
2. Static checks (lint, formatting, type checks).
3. Unit and integration tests.
4. Security scans (dependency, secrets, container checks).
5. Build Docker images and publish as CI artifacts.

### CD Pipeline (approved deployment)
1. Pull signed artifacts.
2. Deploy to staging.
3. Run smoke and regression suites.
4. Manual approval gate for production.
5. Deploy production with rolling strategy.
6. Verify post-deployment SLO and business health checks.

## 7. Azure Deployment Architecture
- Container runtime: Azure Container Apps or AKS (final choice per environment scale).
- Database: Azure Database for PostgreSQL Flexible Server.
- Secrets: Azure Key Vault.
- Networking: Private endpoints and restricted ingress.
- Observability: Azure Monitor, Log Analytics, and alert rules.
- Storage: Encrypted backup storage with policy retention.

## 8. Required Environment Variables
Core backend variables:
- APP_ENV
- API_BASE_PATH
- JWT_SECRET_KEY
- JWT_ACCESS_TTL_MINUTES
- JWT_REFRESH_TTL_DAYS
- DATABASE_URL
- REDIS_URL (optional for async queue)
- NOTIFICATION_PROVIDER
- KEY_VAULT_URI (Azure)

Core frontend variables:
- NEXT_PUBLIC_API_BASE_URL
- NEXT_PUBLIC_APP_ENV

Security variables:
- ENCRYPTION_KEY_REFERENCE
- AUDIT_LOG_SALT_REFERENCE

Do not store secrets in repository files. Use GitHub secrets and Azure Key Vault references.

## 9. Production Deployment Strategy
- Strategy: rolling deployment with health-gated promotion.
- Release candidate is first validated in staging with operational sign-off.
- Production rollout starts with low-risk service slice where possible.
- Automatic rollback triggers on failed health checks or critical error surge.

## 10. Verification Checklist
- API health endpoint returns success.
- Authentication flow works for all core roles.
- Request creation and status transitions validated for lab and radiology.
- Notifications are delivered and acknowledged.
- Dashboard metrics update within expected latency.
- Error and security alerts are below threshold.

## 11. Rollback Procedure
Trigger conditions:
- Critical workflow failure rate above threshold.
- Authentication or authorization outage.
- Data integrity issue detected in production.

Rollback steps:
1. Freeze incoming deployment traffic.
2. Re-deploy last known good image tags.
3. Re-run smoke checks.
4. Confirm queue and notification subsystem stability.
5. Record incident and rollback evidence.

Database rollback considerations:
- Prefer forward-fix migrations.
- If rollback is required, restore from point-in-time backup and reconcile delta events.

## 12. Incident Handling and Escalation
- Detection: alert from monitoring and error budget policy.
- Triage owner: on-call SRE.
- Escalation: backend lead, security lead, product operations.
- Communication: incident channel plus stakeholder status updates every 30 minutes for Sev-1.

## 13. Compliance and Audit Evidence
- Change request and approval records.
- CI/CD logs and artifact provenance.
- Deployment timestamps and operator identity.
- Post-deployment verification report.
- Incident and rollback records where applicable.
