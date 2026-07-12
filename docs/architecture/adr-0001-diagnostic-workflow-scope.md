# ADR-0001: Focus on Diagnostic Workflow Platform, not Full HMS

- Status: Accepted
- Date: 2026-07-12
- Decision Makers: Product, Clinical Advisory, Architecture
- Related Context: AHIF 2026 field validation findings

## Context
Field observations showed significant inefficiencies in diagnostic request workflows. Attempting to solve all hospital domains at once would delay impact and increase implementation risk.

## Decision
MedFlow AI will focus on laboratory and radiology workflow orchestration, scheduling coordination, notifications, patient tracking, and diagnostic analytics. Full HMS domains remain out of scope.

## Consequences
### Positive
- Faster time to value for diagnostic services.
- Clear product identity and implementation boundaries.
- Easier integration strategy with existing HMS/EMR systems.

### Negative
- Some stakeholders may request non-diagnostic modules not supported in core product.
- Integration effort is required where sites expect all-in-one replacement.

## Security and Compliance Impact
Focused scope improves ability to enforce strict audit controls in high-risk workflow transitions.

## Rollout Impact
Supports phased deployment by department and lower training burden.
