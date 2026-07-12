# ADR-0002: FastAPI plus Next.js as Initial Product Stack

- Status: Accepted
- Date: 2026-07-12
- Decision Makers: Engineering, Architecture, Product
- Related Context: Need for rapid delivery and maintainable web platform

## Context
The platform requires rapid iteration, reliable API development, and maintainable frontend portals for multiple clinical roles.

## Decision
Use FastAPI (Python) for backend APIs and Next.js with React/TypeScript for frontend applications.

## Consequences
### Positive
- Strong developer productivity and clear API contracts.
- Broad ecosystem support and hiring feasibility.
- Alignment with planned AI stack in Python.

### Negative
- Requires disciplined API versioning and contract testing to prevent divergence.
- Team must maintain expertise across Python and TypeScript stacks.

## Security and Compliance Impact
FastAPI and Next.js ecosystem supports mature security tooling and CI scanning integration.

## Rollout Impact
Enables modular service delivery and consistent web deployment model.
