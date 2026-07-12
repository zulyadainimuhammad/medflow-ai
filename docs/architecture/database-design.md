# Database Design - MedFlow AI

## Document Control
- Owner: Data Architecture Team
- Version: 1.0
- Status: Approved for MVP Implementation
- Last Updated: 2026-07-12

## 1. Purpose and Scope
This document defines the MedFlow AI transactional data model for diagnostic workflow management, scheduling, notifications, access control, and auditability. It excludes full EMR longitudinal charting by design.

## 2. Data Architecture Overview
- Transactional store: PostgreSQL (primary source of truth).
- Analytical layer: Aggregated tables/materialized views for operational dashboards.
- Cache/search: Optional Redis for transient queue acceleration in later phases.
- Integration pathway: Adapter-managed sync with external EMR/HMS systems.

## 3. Core Entities
### 3.1 users
- Purpose: Identity records for all authenticated staff users.
- Key fields: id, staff_id, full_name, email, phone, department_id, is_active, last_login_at, created_at.
- Relationships: many-to-many with roles through user_roles.

### 3.2 roles
- Purpose: Role definitions such as doctor, lab_scientist, radiographer, nurse, reception, admin.
- Key fields: id, name, description, created_at.

### 3.3 permissions
- Purpose: Action-level permissions for modules and operations.
- Key fields: id, code, module, action, description.

### 3.4 role_permissions
- Purpose: Junction table linking roles to permissions.
- Key fields: role_id, permission_id.

### 3.5 patients
- Purpose: Patient demographic profile and identifiers required for diagnostic workflows.
- Key fields: id, hospital_patient_id, first_name, last_name, date_of_birth, sex, phone, emergency_contact, created_at.
- Privacy: Classified as regulated data.

### 3.6 appointments
- Purpose: Scheduled diagnostic appointments with status tracking.
- Key fields: id, patient_id, service_type, department, scheduled_at, status, created_by, updated_at.
- Statuses: scheduled, confirmed, checked_in, in_progress, completed, no_show, cancelled.

### 3.7 laboratory_requests
- Purpose: Laboratory diagnostic request lifecycle.
- Key fields: id, patient_id, doctor_id, test_panel, priority, status, sample_collected_at, completed_at, notes.
- Statuses: requested, received, in_progress, completed, verified, cancelled.

### 3.8 radiology_requests
- Purpose: Radiology diagnostic request lifecycle.
- Key fields: id, patient_id, doctor_id, modality, body_region, priority, status, scheduled_slot_id, completed_at, report_ready_at.
- Statuses: requested, scheduled, in_progress, reported, completed, cancelled.

### 3.9 notifications
- Purpose: Event-based communication records.
- Key fields: id, recipient_user_id, channel, event_type, payload, delivery_status, sent_at, acknowledged_at.
- Delivery statuses: queued, sent, delivered, failed, acknowledged.

### 3.10 audit_logs
- Purpose: Immutable record of security and workflow-critical actions.
- Key fields: id, actor_user_id, action, entity_type, entity_id, before_state, after_state, ip_address, user_agent, occurred_at.
- Policy: Append-only with retention and archival controls.

## 4. Relationship Summary
- users <> roles via user_roles.
- roles <> permissions via role_permissions.
- patients -> appointments (one-to-many).
- patients -> laboratory_requests (one-to-many).
- patients -> radiology_requests (one-to-many).
- users -> laboratory_requests and radiology_requests as requesting clinicians.
- users -> notifications as recipients.
- users -> audit_logs as actors.

## 5. Schema Standards
- Naming: snake_case for tables and columns.
- Primary keys: UUID for distributed-safe identity.
- Foreign keys: explicit constraints with indexed references.
- Timestamps: created_at and updated_at in UTC for all mutable entities.
- Soft deletes: restricted to selected business entities; audit_logs never deleted.

## 6. Data Lifecycle Management
- Operational data retained online for at least 24 months by default.
- Audit logs retained for minimum 7 years or per local regulatory requirement.
- Daily encrypted backups with point-in-time recovery target under 15 minutes.
- Archival process for closed appointments and completed requests older than policy threshold.

## 7. Data Quality and Integrity Controls
- Required fields and format validations at API and DB layers.
- Enumerated status constraints to prevent invalid transitions.
- Unique constraints:
  - users.email
  - patients.hospital_patient_id
  - requests external reference ids where present
- Trigger-based audit capture for privileged updates.

## 8. Security and Privacy Controls
- Data classification tags at table and column level in schema documentation.
- Encryption at rest on PostgreSQL volumes and backup storage.
- TLS for all DB connections.
- Row-level access controls planned for multi-facility deployments.
- Strict least-privilege database roles for app services, analytics jobs, and admin access.

## 9. Performance and Scalability Strategy
- Composite indexes on status and scheduled_at for queue operations.
- Indexing by patient_id and created_at for timeline retrieval.
- Partition strategy (future): time-based partitioning for audit_logs and notifications.
- Read optimization through materialized views for dashboard KPIs.

## 10. Migration and Change Management
- Migration tooling: Alembic.
- Migration conventions:
  - Forward-only migration scripts.
  - Data backfill scripts versioned with schema changes.
  - Rollback scripts for destructive operations.
- Every schema change requires PR review from backend and data owners.

## 11. Operational Runbooks
- Incident class: schema migration failure.
  - Action: halt rollout, restore snapshot, execute rollback migration.
- Incident class: replication lag or query timeout.
  - Action: throttle analytics jobs, evaluate index plan, scale DB resources.
- On-call ownership: Platform Data On-Call rotating weekly with defined escalation path.
