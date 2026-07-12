# Contribution Workflow - MedFlow AI

## 1. Purpose
Define a predictable, audit-friendly contribution process that maintains software quality, security, and domain clarity for MedFlow AI.

## 2. Issue Intake and Planning
- All work starts with a tracked issue (bug, feature, chore, security).
- Each issue must include:
	- Problem statement
	- Scope and acceptance criteria
	- Domain owner
	- Risk classification (low, medium, high)
- Features touching architecture or workflow transitions must reference relevant ADRs and PRD sections.

## 3. Branch Strategy
- main: protected production-ready branch.
- feature/<short-scope>: new capabilities.
- fix/<short-scope>: defects and hotfixes.
- chore/<short-scope>: maintenance and tooling.

Rules:
- Keep branches short-lived and rebased with main regularly.
- Avoid long-running divergence for workflow-critical modules.

## 4. Commit Conventions
- Preferred style: Conventional Commits.
	- feat:, fix:, docs:, refactor:, test:, chore:
- Commits should be scoped, atomic, and reversible.
- Include issue reference in commit body or PR description.

## 5. Pull Request Workflow
Every PR must include:
- Summary of problem and solution.
- Affected modules and risk assessment.
- Test evidence (unit/integration/e2e as applicable).
- Security impact statement.
- Rollback strategy for operationally significant changes.
- Documentation updates for behavior/interface changes.

## 6. Code Review Process
- Required reviewers by change type:
	- Frontend changes: frontend maintainer.
	- Backend/domain changes: backend maintainer.
	- Database migration changes: data owner.
	- Security-sensitive changes: security reviewer.
- Review SLA targets:
	- Standard PRs: first response within 1 business day.
	- High-priority fixes: first response within 4 hours in business window.
- Review outcomes:
	- Approve
	- Request changes
	- Block (requires domain lead resolution)

## 7. Quality and Compliance Gates
PR cannot merge unless all required checks pass:
- Linting, formatting, and type checks.
- Unit and integration tests.
- Security and dependency scans.
- Documentation update checks.

Additional gate for high-risk changes:
- Clinical/operations sign-off for workflow-impacting behavior.

## 8. Merge and Release Management
- Merge strategy: squash merge by default for clean history.
- Release management:
	- Tag release candidate in staging.
	- Validate smoke and regression checks.
	- Approve production promotion.
- Update CHANGELOG and relevant roadmap documents with released capabilities.

## 9. Issue Management Lifecycle
Status model:
- Backlog -> Ready -> In Progress -> In Review -> Done

Defect severity model:
- Sev-1: critical production impact
- Sev-2: major workflow degradation
- Sev-3: minor or non-blocking issue

## 10. Hotfix Process
- Create fix/hotfix branch from main release state.
- Prioritize minimal, targeted change.
- Run focused regression suite.
- Fast-track review with required maintainer and security checks.
- Post-release, back-merge hotfix into active development branch.

## 11. Post-Release Feedback and Continuous Improvement
- Track release performance metrics and incident reports.
- Document lessons learned in retrospectives.
- Convert repeated review comments into coding standard updates.
- Create ADRs when recurring architectural trade-offs emerge.
