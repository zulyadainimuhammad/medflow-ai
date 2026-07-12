# Frontend Foundation

Next.js engineering scaffold for MedFlow AI.

## What Is Included
- Next.js App Router with TypeScript strict mode.
- Tailwind CSS, ESLint, and Prettier baseline setup.
- Frontend health endpoint:
	- GET /api/health
- Playwright test configuration with starter health test.
- Dockerfile for local and CI container builds.

## Quick Start
1. Install dependencies:
```bash
npm install
```
2. Start development server:
```bash
npm run dev
```
3. Run quality checks:
```bash
npm run lint
npm run typecheck
npm run format:check
```
4. Run e2e placeholder tests:
```bash
npm run test:e2e
```

## Scope Boundary
This frontend contains only development foundation and infrastructure. Product feature modules are intentionally not implemented yet.
