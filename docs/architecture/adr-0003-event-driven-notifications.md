# ADR-0003: Event-Driven Notification Pipeline

- Status: Accepted
- Date: 2026-07-12
- Decision Makers: Platform Engineering, Operations, Product
- Related Context: Need for reliable cross-department communication

## Context
Diagnostic workflows require timely event-driven updates without blocking core request processing.

## Decision
Implement notifications as an asynchronous event-driven pipeline with retry and dead-letter behavior.

## Consequences
### Positive
- Improves resilience and decouples core workflows from delivery channel latency.
- Supports channel expansion (in-app, SMS, email) without rewriting core modules.

### Negative
- Adds operational complexity in queue monitoring and delivery diagnostics.

## Security and Compliance Impact
Notification payload policies must prevent unnecessary PHI exposure and enforce message audit logging.

## Rollout Impact
Supports incremental channel rollout per facility and policy profile.
