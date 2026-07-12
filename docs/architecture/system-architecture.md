# System Architecture - MedFlow AI

## Document Control
- Owner: Healthcare Solutions Architecture
- Version: 1.0
- Status: Baseline Architecture Approved
- Last Updated: 2026-07-12

## 1. Architecture Overview
MedFlow AI uses a modular web platform architecture optimized for diagnostic workflow orchestration. The system separates presentation, application logic, workflow processing, notification dispatch, and analytics processing to support phased deployment and future AI services.

The architecture is designed to operate as a focused diagnostic coordination layer and to integrate with external EMR/HMS systems through controlled interfaces.

## 2. Architectural Goals
- Enable fast and reliable workflow operations for laboratory and radiology services.
- Preserve strong security, auditability, and role-based controls.
- Scale API and workflow throughput horizontally.
- Keep integration boundaries explicit for future EMR interoperability.
- Support incremental introduction of AI-driven optimization capabilities.

## 3. High-Level Context
Primary actors are doctors, lab scientists, radiographers, nurses, reception staff, and administrators.

External dependencies include:
- Existing EMR/HMS systems for patient reference and longitudinal clinical records.
- Messaging providers for email/SMS/push notifications.
- Azure-managed platform services for deployment and operations.

## 4. Logical Architecture
### 4.1 Frontend Layer
- Built with Next.js, React, TypeScript, and Tailwind CSS.
- Role-specific portals:
  - Doctor Portal
  - Laboratory Workflow Console
  - Radiology Workflow Console
  - Reception Scheduling Panel
  - Administrator and Analytics Dashboards
- Uses secure token-based session handling and route guards.

### 4.2 Backend Application Layer
- FastAPI service with modular domains:
  - Authentication and Authorization
  - Patients and Appointments
  - Laboratory Workflow
  - Radiology Workflow
  - Notifications
  - Analytics
  - Audit Logging
- REST APIs as the primary integration contract.
- Background job workers for notifications and aggregation tasks.

### 4.3 AI Services Layer (Future Phase)
- Python-based model services using PyTorch and scikit-learn.
- Planned capabilities:
  - Queue delay prediction
  - Appointment no-show risk scoring
  - Capacity optimization recommendations
- AI outputs presented as recommendations with human override.

### 4.4 Data Layer
- PostgreSQL as the primary transactional database.
- Read-optimized views/materialized summaries for dashboards.
- Audit log tables with append-only write policy.

### 4.5 Notification Layer
- Event-driven notification dispatcher.
- Channels: in-app first, SMS/email adapters where configured.
- Retry queue and dead-letter handling for failed deliveries.

## 5. Authentication and Authorization Architecture
- JWT access tokens with short expiry and refresh token rotation.
- Role-based access control with permission matrix per module.
- Endpoint-level authorization decorators in FastAPI.
- Administrative actions require enhanced audit tagging.

## 6. Data Flow
1. Doctor creates lab or radiology request.
2. Backend validates patient and order payload and persists request.
3. Workflow status transitions update department queues.
4. Notification service emits events to subscribed user roles.
5. Analytics pipeline aggregates operational metrics.
6. Dashboard APIs expose real-time and historical insights.

## 7. Future EMR Integration Strategy
- Integration through dedicated adapter services.
- Initial pattern: pull patient demographics and push diagnostic status updates.
- Canonical identifiers and mapping tables for cross-system reconciliation.
- Fault-tolerant retries and reconciliation reports for sync failures.

## 8. Security Architecture
- TLS enforced for all external and inter-service communication.
- Password hashing with modern adaptive algorithms.
- Database encryption at rest and encrypted backups.
- Secrets managed through Azure Key Vault in hosted environments.
- Structured audit logging for privileged operations and PHI-sensitive actions.
- Security scanning in CI via GitHub Actions.

## 9. Reliability and Operations
- Target uptime: 99.5 percent monthly.
- Health probes and readiness checks for all service containers.
- Automated rollback strategy for failed deployments.
- Observability stack: structured logs, metrics, traces, and alerting.
- Backup policy and disaster recovery drill cadence defined in operations runbook.

## 10. Architecture Risks and Controls
| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Over-coupling between workflow modules | Reduced maintainability | Domain-driven module boundaries and ADR governance | Architecture |
| Dashboard query load affecting OLTP | Performance degradation | Read replicas/materialized views and query budgets | Data Engineering |
| Notification provider outages | Delayed workflow communication | Multi-channel fallback and retry/dead-letter handling | Platform Ops |
| Integration mismatch with EMR data | Data inconsistency | Mapping registry, validation, reconciliation jobs | Integration Team |

## 11. References
- docs/product/product-vision.md
- docs/product/product-requirements-document.md
- docs/architecture/database-design.md
- docs/engineering/security-guidelines.md
