# API Documentation - Template

## API Overview
- Service name:
- Version:
- Base URL:
- Owner:
- Last Updated:

## Standards
- Protocols:
- Content types:
- Authentication:
- Authorization model:
- Rate limits:

## Endpoint Catalog
| Method | Path | Description | Auth Required | Idempotent |
|---|---|---|---|---|
|  |  |  |  |  |

## Endpoint Details Template
### [METHOD] /path
#### Purpose
Describe what this endpoint does.

#### Request
- Headers:
- Path parameters:
- Query parameters:
- Request body schema:

#### Response
- Success response schema:
- Error responses and status codes:

#### Example Request
```http
GET /example
Authorization: Bearer <token>
```

#### Example Response
```json
{
  "message": "example"
}
```

## Error Model
| Code | HTTP Status | Meaning | Client Action |
|---|---|---|---|
|  |  |  |  |

## Versioning and Deprecation
- Versioning strategy:
- Deprecation policy:
- Breaking change process:

## Security Considerations
- Input validation
- Sensitive data handling
- Audit logging requirements

## Testing and Validation
- Contract tests
- Integration tests
- Load and resilience testing
