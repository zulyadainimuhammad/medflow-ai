# MedFlow AI Enterprise Architecture

## Document Control
- Owner: Chief Software Architect, MedFlow AI
- Version: 1.0
- Status: Production Architecture Baseline
- Last Updated: 2026-07-12

## 1. High-Level System Architecture
MedFlow AI is a diagnostic workflow platform designed to orchestrate laboratory and radiology operations across hospitals and diagnostic centers. The architecture separates user experience, domain APIs, workflow engines, notification/event processing, analytics, and future AI services.

Core architecture principles:
- Domain-driven modularity across diagnostic workflows.
- Event-driven communication for asynchronous operations.
- Security, auditability, and least privilege by default.
- Cloud-native deployment with controlled environment promotion.
- Integration-ready boundaries for future EMR interoperability.

```mermaid
flowchart LR
    U1[Doctors]
    U2[Lab Scientists]
    U3[Radiographers]
    U4[Nurses and Reception]
    U5[Administrators]

    FE[MedFlow Web App\nNext.js + React + TypeScript]
    GW[API Gateway]
    BE[Core API Services\nFastAPI]
    WF[Workflow Orchestrator]
    EV[Event Bus]
    NT[Notification Service]
    AN[Analytics Service]
    AI[AI Services\nFuture Phase]
    DB[(PostgreSQL)]
    AU[(Audit Log Store)]
    EMR[External EMR/HMS\nFuture Integration]

    U1 --> FE
    U2 --> FE
    U3 --> FE
    U4 --> FE
    U5 --> FE

    FE --> GW --> BE
    BE --> WF
    BE --> DB
    BE --> AU
    WF --> EV
    EV --> NT
    EV --> AN
    EV --> AI
    NT --> FE
    AN --> FE
    BE <--> EMR
    AI --> BE
```

## 2. C4 Model

### 2.1 Context Diagram
```mermaid
flowchart LR
    subgraph Users
      D[Doctor]
      L[Laboratory Scientist]
      R[Radiographer]
      N[Nurse]
      RC[Reception Staff]
      A[Hospital Administrator]
    end

    MF[MedFlow AI Platform]
    EMR[Hospital EMR/HMS]
    MSG[SMS/Email Gateway]
    IDP[Enterprise Identity Provider]

    D --> MF
    L --> MF
    R --> MF
    N --> MF
    RC --> MF
    A --> MF

    MF <--> EMR
    MF --> MSG
    MF <--> IDP
```

### 2.2 Container Diagram
```mermaid
flowchart TB
    subgraph Client Tier
      WEB[Web Frontend\nNext.js]
    end

    subgraph Application Tier
      APIGW[API Gateway]
      AUTH[Auth and RBAC Service]
      PAT[Patient and Appointment Service]
      LAB[Laboratory Workflow Service]
      RAD[Radiology Workflow Service]
      NOTIF[Notification Service]
      ANALYTICS[Analytics Service]
      AUDIT[Audit Service]
      WORKER[Async Worker]
      AIAPI[AI Inference API\nFuture]
    end

    subgraph Data Tier
      PG[(PostgreSQL)]
      CACHE[(Redis/Queue)]
      BLOB[(Object Storage)]
    end

    WEB --> APIGW
    APIGW --> AUTH
    APIGW --> PAT
    APIGW --> LAB
    APIGW --> RAD
    APIGW --> NOTIF
    APIGW --> ANALYTICS

    AUTH --> PG
    PAT --> PG
    LAB --> PG
    RAD --> PG
    NOTIF --> PG
    ANALYTICS --> PG
    AUDIT --> PG

    LAB --> WORKER
    RAD --> WORKER
    WORKER --> CACHE
    WORKER --> NOTIF
    WORKER --> ANALYTICS
    WORKER --> AIAPI

    NOTIF --> BLOB
```

### 2.3 Component Diagram (Core API)
```mermaid
flowchart LR
    subgraph Core API Service
      ROUTER[REST Routers]
      AUTHZ[AuthN/AuthZ Middleware]
      VLD[Request Validation]
      APP[Application Services]
      DOMAIN[Domain Layer]
      REPO[Repository Layer]
      EVENTS[Domain Event Publisher]
      AUD[Audit Interceptor]
    end

    ROUTER --> AUTHZ --> VLD --> APP
    APP --> DOMAIN --> REPO
    DOMAIN --> EVENTS
    APP --> AUD
```

## 3. Domain Model
MedFlow AI domain is organized around diagnostic workflow orchestration and operational visibility.

Bounded contexts:
- Identity and Access: users, roles, permissions, session and token policies.
- Patient Flow: patient records, visits, movement and appointment coordination.
- Laboratory Workflow: request lifecycle, sample progress, verification.
- Radiology Workflow: request lifecycle, scheduling, report readiness.
- Notification and Communication: event subscriptions, delivery channels, acknowledgments.
- Analytics and Operations: KPIs, throughput, bottlenecks, turnaround metrics.
- Audit and Compliance: immutable traces for critical actions.

```mermaid
classDiagram
    class User {
      uuid id
      string full_name
      string email
      bool is_active
    }
    class Role {
      uuid id
      string name
    }
    class Permission {
      uuid id
      string code
      string module
      string action
    }
    class Patient {
      uuid id
      string hospital_patient_id
      string full_name
    }
    class Appointment {
      uuid id
      datetime scheduled_at
      string status
    }
    class LaboratoryRequest {
      uuid id
      string test_panel
      string status
      string priority
    }
    class RadiologyRequest {
      uuid id
      string modality
      string status
      string priority
    }
    class Notification {
      uuid id
      string channel
      string delivery_status
    }
    class AuditLog {
      uuid id
      string action
      datetime occurred_at
    }

    User "*" -- "*" Role : assigned
    Role "*" -- "*" Permission : grants
    Patient "1" -- "*" Appointment : has
    Patient "1" -- "*" LaboratoryRequest : has
    Patient "1" -- "*" RadiologyRequest : has
    User "1" -- "*" LaboratoryRequest : requests
    User "1" -- "*" RadiologyRequest : requests
    User "1" -- "*" Notification : receives
    User "1" -- "*" AuditLog : performs
```

## 4. Entity Relationship Diagram (ERD)
```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigns
    ROLES ||--o{ ROLE_PERMISSIONS : grants
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : maps

    PATIENTS ||--o{ APPOINTMENTS : books
    PATIENTS ||--o{ LABORATORY_REQUESTS : has
    PATIENTS ||--o{ RADIOLOGY_REQUESTS : has

    USERS ||--o{ LABORATORY_REQUESTS : creates
    USERS ||--o{ RADIOLOGY_REQUESTS : creates
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ AUDIT_LOGS : acts

    USERS {
      uuid id PK
      string staff_id
      string email
      string full_name
      bool is_active
    }

    ROLES {
      uuid id PK
      string name
    }

    PERMISSIONS {
      uuid id PK
      string code
      string module
      string action
    }

    PATIENTS {
      uuid id PK
      string hospital_patient_id UK
      string first_name
      string last_name
      date date_of_birth
    }

    APPOINTMENTS {
      uuid id PK
      uuid patient_id FK
      string department
      datetime scheduled_at
      string status
    }

    LABORATORY_REQUESTS {
      uuid id PK
      uuid patient_id FK
      uuid doctor_id FK
      string test_panel
      string priority
      string status
    }

    RADIOLOGY_REQUESTS {
      uuid id PK
      uuid patient_id FK
      uuid doctor_id FK
      string modality
      string priority
      string status
    }

    NOTIFICATIONS {
      uuid id PK
      uuid recipient_user_id FK
      string channel
      string event_type
      string delivery_status
    }

    AUDIT_LOGS {
      uuid id PK
      uuid actor_user_id FK
      string action
      string entity_type
      uuid entity_id
      datetime occurred_at
    }
```

## 5. Authentication and Authorization Architecture
Authentication:
- JWT access tokens with short TTL and refresh token rotation.
- Login protected by password policy and brute-force throttling.
- Optional MFA capability for privileged users.

Authorization:
- RBAC with role to permission mapping.
- Permission checks at API gateway and service layer.
- Resource-level checks for ownership and department scope.

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant GW as API Gateway
    participant AUTH as Auth Service
    participant API as Domain API

    U->>FE: Submit credentials
    FE->>GW: POST /auth/login
    GW->>AUTH: Validate credentials
    AUTH-->>GW: Access + Refresh token
    GW-->>FE: JWT tokens
    FE->>GW: API request with Bearer token
    GW->>AUTH: Introspect/validate token
    AUTH-->>GW: Claims + permissions
    GW->>API: Forward request with claims
    API-->>GW: Authorized response
    GW-->>FE: Response
```

## 6. Role-Based Access Control (RBAC)
RBAC model:
- Roles are business-aligned, not team-title aligned.
- Permissions are action-level and module-scoped.
- Administrative overrides are auditable and restricted.

| Role | Key Permissions |
|---|---|
| Doctor | create/read own lab and radiology requests, read patient diagnostic timeline |
| Laboratory Scientist | read assigned lab queue, update lab request statuses, verify completion |
| Radiographer | read assigned radiology queue, update radiology statuses, mark reports ready |
| Nurse | read patient flow status, update readiness and movement events |
| Reception Staff | manage appointments, check-in/out patients, notify queue updates |
| Hospital Administrator | read all operational dashboards, manage non-clinical configuration |
| Platform Admin | user/role management, policy configuration, audit access |

## 7. Data Flow Diagrams

### 7.1 Core Diagnostic Workflow DFD
```mermaid
flowchart LR
    DR[Doctor] -->|Create request| API[Core API]
    API --> DB[(PostgreSQL)]
    API --> EV[Event Bus]
    EV --> LABQ[Lab Queue]
    EV --> RADQ[Radiology Queue]
    LABQ --> STAFF1[Lab Scientist]
    RADQ --> STAFF2[Radiographer]
    STAFF1 --> API
    STAFF2 --> API
    API --> DB
    API --> EV
    EV --> NOTIF[Notification Service]
    NOTIF --> USERS[Clinical Users]
```

### 7.2 Analytics Data Flow DFD
```mermaid
flowchart LR
    DB[(Operational DB)] --> ETL[Aggregation Jobs]
    ETL --> MART[(Analytics Views)]
    MART --> DASH[Analytics API]
    DASH --> ADMIN[Admin Dashboard]
```

## 8. Request Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Requested
    Requested --> Received
    Received --> InProgress
    InProgress --> Completed
    Completed --> Verified
    Requested --> Cancelled
    Received --> Cancelled
    InProgress --> Cancelled

    state Radiology {
      [*] --> RequestedR
      RequestedR --> Scheduled
      Scheduled --> InProgressR
      InProgressR --> Reported
      Reported --> CompletedR
      RequestedR --> CancelledR
      Scheduled --> CancelledR
    }
```

Lifecycle governance:
- Every state transition is validated by workflow rules.
- Every transition emits an audit log and domain event.
- Invalid transitions return conflict errors and are blocked.

## 9. Event Flow
```mermaid
sequenceDiagram
    participant API as Workflow API
    participant BUS as Event Bus
    participant N as Notification Service
    participant A as Analytics Service
    participant AU as Audit Service

    API->>BUS: publish RequestStatusChanged
    BUS->>N: consume event
    BUS->>A: consume event
    BUS->>AU: consume event
    N-->>BUS: NotificationDispatched
    A-->>BUS: MetricsUpdated
    AU-->>BUS: AuditRecorded
```

Event design:
- Events are immutable and versioned.
- Correlation IDs are carried across services.
- Consumers are idempotent to prevent duplicate side effects.

## 10. Notification Architecture
Notification services are event-driven and multi-channel.

Channels:
- In-app notifications (primary channel).
- SMS and email connectors (facility-configurable).

Reliability controls:
- Retry policies with exponential backoff.
- Dead-letter queue for terminal failures.
- Delivery and acknowledgment tracking.

```mermaid
flowchart LR
    EV[Event Bus] --> NR[Notification Rules Engine]
    NR --> INAPP[In-App Channel]
    NR --> SMS[SMS Adapter]
    NR --> EMAIL[Email Adapter]
    INAPP --> TRACK[Delivery Tracker]
    SMS --> TRACK
    EMAIL --> TRACK
    TRACK --> DB[(Notification Store)]
```

## 11. AI Service Architecture
AI capabilities are introduced as decision-support services, not autonomous decision makers.

Initial AI capabilities (future phases):
- Queue delay prediction.
- Appointment no-show risk scoring.
- Capacity recommendation for lab/radiology scheduling.

Architecture controls:
- Offline model training pipeline.
- Online inference API with strict timeout budgets.
- Human override and explainability requirement in UI.

```mermaid
flowchart TB
    DATA[(Operational and Historical Data)] --> FEAT[Feature Pipeline]
    FEAT --> TRAIN[Model Training\nPyTorch/Scikit-learn]
    TRAIN --> REG[Model Registry]
    REG --> SERVE[Inference Service]
    SERVE --> API[Core API]
    API --> UI[Role Portals]
    API --> LOG[Prediction Audit Log]
```

## 12. Deployment Architecture
Deployment model:
- Containerized services for frontend, APIs, workers, and AI service.
- Environment promotion: dev -> staging -> production.
- Blue/green or rolling deployment by service criticality.

```mermaid
flowchart LR
    GH[GitHub Repository] --> CI[GitHub Actions CI]
    CI --> REG[Container Registry]
    REG --> STG[Staging Environment]
    STG --> GATE[Release Approval]
    GATE --> PROD[Production Environment]
```

## 13. Azure Cloud Architecture
```mermaid
flowchart TB
    USERS[Hospital Users] --> FRONTDOOR[Azure Front Door / WAF]
    FRONTDOOR --> APP[Azure Container Apps or AKS]
    APP --> DB[(Azure PostgreSQL Flexible Server)]
    APP --> REDIS[(Azure Cache for Redis)]
    APP --> KV[Azure Key Vault]
    APP --> MON[Azure Monitor + Log Analytics]
    APP --> BLOB[Azure Storage Accounts]

    CI[GitHub Actions] --> ACR[Azure Container Registry]
    ACR --> APP
```

Azure architecture controls:
- Private networking and least-privilege managed identities.
- Key Vault-backed secret injection.
- Centralized monitoring, alerting, and cost controls.

## 14. Logging Architecture
Logging strategy:
- Structured JSON logs with correlation IDs.
- Log classes: access, application, security, workflow, audit.
- PHI/PII masking at source and sink.

```mermaid
flowchart LR
    FE[Frontend] --> COL[Log Collector]
    API[API Services] --> COL
    WORKER[Workers] --> COL
    AI[AI Service] --> COL
    COL --> LA[Log Analytics Workspace]
    COL --> SIEM[Security Analytics]
```

## 15. Monitoring Architecture
Monitoring pillars:
- Metrics: latency, throughput, error rate, queue depth.
- Traces: cross-service request tracing.
- Logs: operational and security logs.
- Synthetic health checks for critical user journeys.

```mermaid
flowchart LR
    APPS[All Services] --> OTEL[OpenTelemetry Pipeline]
    OTEL --> MET[Metrics Store]
    OTEL --> TR[Trace Store]
    OTEL --> LOGS[Log Store]
    MET --> ALERT[Alert Manager]
    TR --> ALERT
    LOGS --> ALERT
    ALERT --> NOC[On-Call and Incident Channels]
```

## 16. Security Architecture
Security model includes identity hardening, network controls, data protections, and continuous assurance.

Controls:
- TLS for all traffic.
- RBAC and fine-grained permission enforcement.
- Secrets via Key Vault with rotation policies.
- Immutable audit logs for sensitive actions.
- SAST, dependency and secrets scanning in CI.
- WAF and API abuse protections.

```mermaid
flowchart TB
    INTERNET[Internet Traffic] --> WAF[WAF and DDoS Protection]
    WAF --> GW[API Gateway]
    GW --> AUTH[Auth Service]
    GW --> API[Core APIs]
    API --> ENC[(Encrypted Data Stores)]
    API --> AUDIT[(Immutable Audit Logs)]
    API --> VAULT[Secrets Vault]
```

## 17. API Gateway Architecture
Gateway responsibilities:
- TLS termination and request routing.
- JWT validation and policy enforcement.
- Rate limiting and abuse protection.
- Request/response logging and correlation IDs.
- API version routing and deprecation enforcement.

```mermaid
flowchart LR
    FE[Frontend Clients] --> GW[API Gateway]
    GW --> AUTH[Auth Service]
    GW --> P[Patient and Appointment API]
    GW --> L[Laboratory API]
    GW --> R[Radiology API]
    GW --> N[Notification API]
    GW --> A[Analytics API]
```

## 18. Future EMR Integration Architecture
Integration goals:
- Exchange patient demographics and diagnostic status with external EMR/HMS.
- Avoid tight coupling through adapter and canonical model patterns.
- Guarantee traceability and reconciliation for all synchronized records.

Integration patterns:
- Adapter layer for EMR-specific protocol handling.
- Canonical event schema for internal domain mapping.
- Retry, reconciliation, and exception queue for failed syncs.

```mermaid
flowchart LR
    MFAPI[MedFlow Integration API] --> MAP[Canonical Mapper]
    MAP --> ADP[EMR Adapter Layer]
    ADP --> EMR1[EMR System A]
    ADP --> EMR2[EMR System B]
    MAP --> REC[Reconciliation Service]
    REC --> OPS[Integration Operations Dashboard]
```

## Architecture Governance
- All major architecture changes require ADR submission and approval.
- Security and compliance impact assessment is mandatory for integration and data model changes.
- Production architecture revisions follow versioned change control with rollback strategy.
