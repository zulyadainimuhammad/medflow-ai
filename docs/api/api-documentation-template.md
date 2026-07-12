# API Documentation - MedFlow AI v1

## API Overview
- Service name: MedFlow AI Core API
- Version: v1
- Base URL (local): http://localhost:8000/api/v1
- Base URL (staging): https://staging-api.medflow.ai/api/v1
- Base URL (production): https://api.medflow.ai/api/v1
- Owner: Backend Engineering
- Last Updated: 2026-07-12

## Standards
- Protocol: HTTPS in non-local environments.
- Content type: application/json.
- Authentication: JWT Bearer tokens with refresh workflow.
- Authorization model: RBAC (role + permission checks per endpoint).
- Time format: ISO 8601 UTC.
- Pagination: page and page_size with metadata.
- Rate limiting baseline:
  - Auth endpoints: 10 requests/minute/IP.
  - Core data endpoints: 120 requests/minute/token.
  - Analytics endpoints: 60 requests/minute/token.

## Endpoint Catalog
| Method | Path | Description | Auth Required | Idempotent |
|---|---|---|---|---|
| POST | /auth/login | Authenticate user and issue JWT tokens | No | No |
| POST | /auth/refresh | Rotate access token using refresh token | Yes | No |
| POST | /auth/logout | Invalidate current refresh token | Yes | Yes |
| GET | /auth/me | Get authenticated user profile | Yes | Yes |
| GET | /patients | List patients with search filters | Yes | Yes |
| POST | /patients | Register a patient profile | Yes | No |
| GET | /patients/{patient_id} | Get patient details and workflow summary | Yes | Yes |
| PATCH | /patients/{patient_id} | Update patient profile fields | Yes | No |
| GET | /doctors/me/requests | Get diagnostic requests created by logged-in doctor | Yes | Yes |
| POST | /laboratory/requests | Create laboratory request | Yes | No |
| GET | /laboratory/requests | List laboratory requests by status/priority | Yes | Yes |
| PATCH | /laboratory/requests/{request_id}/status | Transition laboratory request status | Yes | No |
| POST | /radiology/requests | Create radiology request | Yes | No |
| GET | /radiology/requests | List radiology requests by status/modality | Yes | Yes |
| PATCH | /radiology/requests/{request_id}/status | Transition radiology request status | Yes | No |
| GET | /appointments | List appointments by date/department/status | Yes | Yes |
| POST | /appointments | Create appointment slot assignment | Yes | No |
| PATCH | /appointments/{appointment_id} | Update appointment details or status | Yes | No |
| GET | /notifications | List user notifications | Yes | Yes |
| PATCH | /notifications/{notification_id}/acknowledge | Acknowledge notification | Yes | Yes |
| GET | /analytics/overview | Operational KPI snapshot | Yes | Yes |
| GET | /analytics/turnaround-time | Turnaround metrics by department and date range | Yes | Yes |
| GET | /analytics/queue-load | Queue pressure and bottleneck indicators | Yes | Yes |

## Endpoint Details
### POST /auth/login
#### Purpose
Authenticate user credentials and issue access and refresh tokens.

#### Request
- Headers: Content-Type: application/json
- Body:
```json
{
  "email": "doctor@hospital.org",
  "password": "string"
}
```

#### Response
```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "full_name": "Dr. Amina Yusuf",
    "role": "doctor"
  }
}
```

### POST /laboratory/requests
#### Purpose
Create a new laboratory workflow request linked to a patient and requesting doctor.

#### Request
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "test_panel": "FBC",
  "priority": "urgent",
  "clinical_notes": "Rule out severe infection"
}
```

#### Response
```json
{
  "id": "uuid",
  "status": "requested",
  "created_at": "2026-07-12T09:30:00Z"
}
```

### PATCH /radiology/requests/{request_id}/status
#### Purpose
Transition radiology request status with audit trail capture.

#### Request
```json
{
  "status": "reported",
  "note": "CT report signed by radiologist"
}
```

#### Response
```json
{
  "id": "uuid",
  "previous_status": "in_progress",
  "status": "reported",
  "updated_at": "2026-07-12T12:15:00Z"
}
```

### GET /analytics/turnaround-time
#### Purpose
Return turnaround statistics for laboratory and radiology requests.

#### Query Parameters
- from: ISO date.
- to: ISO date.
- department: laboratory | radiology | all.

#### Response
```json
{
  "from": "2026-07-01",
  "to": "2026-07-12",
  "department": "all",
  "median_turnaround_minutes": 142,
  "p90_turnaround_minutes": 281,
  "completed_requests": 1284
}
```

## Error Model
| Code | HTTP Status | Meaning | Client Action |
|---|---|---|---|
| AUTH_001 | 401 | Invalid or expired token | Re-authenticate or refresh token |
| AUTH_002 | 403 | Insufficient permissions | Request appropriate role/permission |
| VAL_001 | 422 | Validation failure | Correct payload and retry |
| RES_404 | 404 | Resource not found | Verify identifier and context |
| WF_409 | 409 | Invalid workflow transition | Refresh state and use allowed transition |
| SYS_500 | 500 | Internal server error | Retry if transient; escalate with request id |

## Versioning and Deprecation
- Versioning strategy: URI path versioning (/api/v1).
- Backward compatibility: non-breaking additions only within major version.
- Deprecation policy: minimum 90-day notice before removing endpoints.
- Breaking change process: ADR plus release notes and migration guide.

## Security Considerations
- Validate and sanitize all inputs at request boundary.
- Enforce permission checks on all role-sensitive operations.
- Mask regulated data in logs and analytics exports.
- Record audit entries for status transitions and privileged actions.

## Testing and Validation
- Contract tests for request/response schemas.
- Integration tests for cross-module workflows.
- Negative tests for authorization and invalid status transitions.
- Load tests for queue listing and analytics endpoints.
