# SyncFlow Frontend - Implementation Plan

**Date:** 2025-12-09
**Version:** 1.0.0

This document outlines the technology stack, architecture, deployment, and support guidelines for the SyncFlow administrative frontend.

## 1. Technology Stack

### Core
- **React** 18.3+ (desktop-first architecture)
- **TypeScript** 5.4+ (strict mode enforced)
- **Vite** 5.x (fast dev server and build)

### State & Data
- **TanStack Query** 5.x (server data, caching, invalidation)
- **Zustand** 4.x (client UI state)
- **Axios** 1.x (API client with interceptors)

### UI & Forms
- **Tailwind CSS** 3.4+ (utility styling)
- **shadcn/ui + Radix** primitives
- **AG Grid Community** 32.x for enterprise tables
- **React Hook Form** + **Zod** for form validation

### Utilities
- **Lucide React** for icons
- **i18next + react-i18next** for EN/FA translations
- **date-fns** for date formatting
- **clsx + tailwind-merge** for class merging

### Testing
- **Vitest** for unit tests
- **React Testing Library** for components
- **Playwright** for E2E
- **MSW** for API mocking

## 2. Project Layout
```
bridge_v2/frontend/
├── public/locales/{en,fa}/common.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── router.tsx
│   ├── lib/api.ts
│   ├── components/
│   │   ├── layout/
│   │   ├── ui/
│   │   └── features/{entities,mapping,sync,monitoring}
│   ├── pages/{dashboard,entities,mappings,sync,monitoring,settings}
│   ├── hooks/{useEntities,useMappings,useBatches}
│   ├── store/{authStore,uiStore}
│   ├── i18n/index.ts
│   └── styles/globals.css
├── .env.example
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 3. Implementation Phases
1. **Phase F1 – Foundation (2 days)**
   - Initialize Vite project, configure ESLint, Prettier, Husky + lint-staged.
   - Setup Tailwind, CSS variables, and default layout (header/sidebar).
2. **Phase F2 – Core Features (5 days)**
   - Build login page, dashboard, and protected routes.
   - Implement API clients and hooks for sync, entities, failed records.
   - Create drawer-based forms for connections, mappings, and batch actions.
3. **Phase F3 – Monitoring & Sync Controls (4 days)**
   - Build sync list, batch detail, failed-record viewer, pending children dashboards.
   - Add stats cards (throughput, errors, pending counts).
4. **Phase F4 – Polish (2 days)**
   - Add translations (English + Farsi), dark mode, responsive design, accessibility.
   - Write Vitest/unit tests and Playwright scenarios.

## 4. API Client Blueprint
`src/lib/api.ts` exports a base `apiClient` that:
- Reads `VITE_API_BASE_URL`.
- Adds JWT tokens from localStorage.
- Handles JSON payloads and error conversion.
- Retries authentication via refresh tokens when needed.

Services wrap `apiClient` for connections, mappings, sync batches, monitoring metrics, and settings.

## 5. Translation Keys & RTL
- Use JSON files under `public/locales/en` and `public/locales/fa`.
- Mirror layouts and spacing when RTL is active.
- Keep key names aligned (e.g., `dashboard`, `sync`, `pendingChildren`).

## 6. Deployment Checklist
- Build: `pnpm build`
- Output assets to backend `static/` directory.
- Configure `VITE_API_BASE_URL` and monitoring env vars.
- Health check returns `ok` at `GET /health/frontend`.

## 7. Support
- **Author:** SyncFlow Frontend Team
- **Contact:** frontend@syncflow.local
- Run `pnpm lint`, `pnpm test`, `pnpm e2e` before each release.
- Next release planned for 2025-12-09.
