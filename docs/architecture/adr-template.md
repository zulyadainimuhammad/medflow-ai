# ADR Authoring Standard - MedFlow AI

This document defines the required structure and quality bar for architecture decision records in MedFlow AI.

## Purpose
ADRs capture high-impact technical decisions so teams can understand why a path was chosen, what alternatives were considered, and how decisions affect security, reliability, and delivery.

## Required ADR Structure
Each ADR must include the following sections:

1. Header
- ADR ID and title
- Status (Proposed, Accepted, Superseded, Rejected)
- Decision date
- Decision makers
- Related issue/epic link

2. Context
- Problem statement and constraints.
- Why the decision is needed now.

3. Decision Drivers
- Product outcomes.
- Security/compliance requirements.
- Reliability/performance requirements.
- Team and operational constraints.

4. Options Considered
- At least two viable options documented.
- Risks and trade-offs for each option.

5. Decision Outcome
- Chosen option and rationale.
- Positive consequences.
- Negative consequences and known limitations.

6. Security and Compliance Impact
- Effect on healthcare data protection controls.
- Audit and traceability implications.

7. Operational Impact
- SLO/reliability impact.
- Monitoring and observability impact.
- Cost and runbook implications.

8. Rollout and Validation
- Migration/rollout plan.
- Rollback approach.
- Validation criteria and test evidence.

9. References
- Linked PRD sections, architecture docs, and implementation PRs.

## Authoring Rules
- Use specific, evidence-based reasoning.
- Avoid ambiguous statements and generic justifications.
- Link every accepted ADR in adr-index.md.
- Superseding ADRs must reference replaced ADR IDs explicitly.
