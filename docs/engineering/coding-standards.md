# Coding Standards - MedFlow AI

## 1. Purpose
Establish implementation conventions that ensure MedFlow AI code remains secure, readable, testable, and production-ready across frontend, backend, and future AI services.

## 2. Engineering Principles
- Design for maintainability and explicit domain boundaries.
- Prefer deterministic behavior and explicit error handling.
- Optimize for safe clinical operations, not clever shortcuts.
- Keep business logic out of transport and presentation layers.

## 3. Stack-Specific Conventions
### 3.1 Python and FastAPI
- Python version baseline: 3.12.
- Style: PEP 8 with Ruff and Black enforcement.
- Type hints required for public functions and service boundaries.
- FastAPI routers grouped by domain module.
- Pydantic models used for request/response contracts.
- Use dependency injection for auth and data access context.

### 3.2 TypeScript, React, and Next.js
- TypeScript strict mode required.
- ESLint + Prettier enforced in CI.
- Functional components with explicit prop types.
- Avoid business rules in UI components; use hooks/services.
- Shared UI primitives in component library folders.

### 3.3 Tailwind CSS
- Use design tokens and semantic utility composition.
- Avoid arbitrary colors unless mapped to design system tokens.
- Keep utility class length manageable with reusable class patterns.

## 4. Naming and Folder Structure
- Python modules: snake_case.
- TypeScript files/components: kebab-case for files, PascalCase for component names.
- API paths: plural resource nouns.
- Tests mirror source structure.

Recommended domain layout:
- backend/app/domains/<domain_name>/
- frontend/src/modules/<domain_name>/

## 5. Code Quality Rules
- Mandatory checks: lint, format, type-check, unit tests.
- Cyclomatic complexity target: <= 10 per function unless justified.
- Function length target: <= 60 lines for business logic functions.
- Structured logging with contextual request IDs.
- No commented-out dead code in merged branches.

## 6. Testing Conventions
- Unit tests required for business logic and validators.
- Integration tests required for endpoint-domain-database paths.
- End-to-end tests required for critical diagnostic workflows.
- Bug fixes require regression test coverage.

## 7. Error Handling and API Standards
- Return explicit, consistent error codes and messages.
- Never expose stack traces or internal secrets in responses.
- Validate input at boundary and enforce status transition guards.
- Include correlation/request IDs in error responses.

## 8. Security Coding Requirements
- Validate and sanitize all inbound data.
- Enforce role/permission checks server-side for every protected route.
- Never trust client-calculated workflow states.
- No hardcoded secrets, keys, or credentials.
- Use approved cryptography libraries and secure defaults.

## 9. Documentation Requirements
- Update relevant docs for API, architecture, or workflow changes.
- Any architectural trade-off must reference an ADR.
- Complex workflows require sequence comments or linked docs.

## 10. Git and Review Workflow Standards
- Branch naming: feature/<scope>, fix/<scope>, chore/<scope>.
- Commit style: conventional commits preferred.
- PR must include scope, validation evidence, risk, and rollback notes.
- Required reviewers:
	- Backend changes: backend maintainer.
	- Frontend changes: frontend maintainer.
	- Security-sensitive changes: security reviewer.

## 11. Definition of Done
- Code merged with passing CI.
- Tests and docs updated.
- Security and compliance checks passed.
- Feature acceptance criteria validated.

## 12. Exceptions Process
Any exception requires a documented rationale in PR notes, explicit reviewer approval, and follow-up remediation ticket if the exception is temporary.