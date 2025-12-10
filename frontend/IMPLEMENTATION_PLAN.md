# SyncFlow Frontend - Implementation Plan

**Version:** 1.0.0  
**Based on:** Mahur Mehdashti Design System v2.0 & Mahur Mehdashti Frontend Requirements v1.0  
**Target Port:** 5172  
**Date:** December 2025  
**Owner:** Mahur Mehdashti <mehdashti@gmail.com>

This plan describes the SyncFlow administrative UI—its objectives, technology stack, project structure, design principles, implementation phases, and testing guidelines.

## Table of Contents
1. Executive Summary
2. Technology Stack
3. Project Structure
4. Design System Integration
5. API Client Architecture
6. Implementation Phases
7. Component & Page Specifications
8. State Management
9. Testing Strategy

## 1. Executive Summary
SyncFlow Frontend enables integration engineers and operators to manage sync jobs, mappings, monitoring, and settings for the SyncFlow backend.
Key functions:
- Dashboard: sync metrics, system health, queues
- Sync management: start/stop/history for batches
- Entity configuration: business keys, parent references
- Mapping editor: field-level transformations
- Monitoring: failed records, pending children, alerts
- Settings: locales, theme, tokens

## 2. Technology Stack
- **Frontend:** React 19, TypeScript 5.7+, Vite 6, pnpm 9
- **State & Data:** TanStack Query 5, Zustand 5, Axios 1
- **Styling:** Tailwind CSS 4, shadcn/ui, Lucide icons, CSS variables from Mahur Mehdashti design tokens
- **Forms:** React Hook Form + Zod + resolver bridge
- **Routing:** TanStack Router 1, drawer-based navigation (no modals)
- **Testing:** Vitest, React Testing Library, Playwright, MSW
- **Internationalization:** i18next/react-i18next (EN + FA + AR + TR)

## 3. Project Structure
```
bridge_v2/frontend/
├── public/locales/{en,fa,ar,tr}/translation.json
├── src/
│   ├── api/ (client, services for entities/mappings/sync/monitoring)
│   ├── components/
│   ├── features/
│   ├── pages/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   ├── styles/global.css
│   ├── i18n/index.ts
│   ├── App.tsx, router.tsx, main.tsx
```
Shared UI components rely on `@mahur-mehdashti/ui` tokens and tailwind for responsive designs.

## 4. Design System Integration
- Adopt Mahur Mehdashti blue/orange palette, typography, spacing, and tokens.
- Drawer-based forms (InlineConfirm) replace modals to ensure keyboard-first UX.
- AG Grid wraps data-heavy tables to display entity lists, batches, and monitoring data.
- Dark/light mode toggles with persistent user preference.
- RTL support when FA/AR locale selected (mirrored layout and CSS overrides).

## 5. API Client Architecture
`src/api/client.ts` exposes `apiClient()` that:
- Reads `VITE_API_BASE_URL` from env
- Adds JWT tokens from storage with refresh logic
- Handles JSON body serialization and error mapping

Services such as `entities.service.ts`, `sync.service.ts`, `mapping.service.ts`, and `monitoring.service.ts` wrap `apiClient()` for domain operations.

## 6. Implementation Phases
1. **Phase 0 – Setup (Day 1)**: scaffold Vite + TypeScript, configure ESLint/Prettier/Vite, create `.env` samples, and install shared dependencies.
2. **Phase 1 – Base Layout (Days 2–3)**: build AppShell, header, sidebar, and drawer infrastructure.
3. **Phase 2 – Core Features (Week 1)**: implement login, dashboard, entity/mapping management pages, and API services.
4. **Phase 3 – Monitoring & Sync Ops (Week 2)**: build sync list/history, batch pages, failed records, pending children, and schedule controls.
5. **Phase 4 – Polish & Testing (Week 3)**: finalize translations, dark mode, RTL fixes, Storybook stories, and automated tests.

## 7. Component & Page Specifications
- **Dashboard:** stats cards, timeline chart for syncs, job list, quick filters.
- **Sync Management:** table of batches, start-sync drawer (entity select, schedule, filters), action menu for retries/cancellations.
- **Entities:** list view with business key counts, drawer for editing fields and parent refs.
- **Mapping:** mapping table with field transformations, preview, and live sync.
- **Monitoring:** charts for failed records, pending children, health statuses, metrics export.
- **Settings:** theme switch, language selector, token management, health check display.

## 8. State Management
- Zustand stores keep auth state, UI theme/locale, toast notifications.
- TanStack Query handles fetching/caching for entities, syncs, batches, failed records, metrics.
- Derived hooks (`useEntities`, `useMappings`, `useSyncBatches`) encapsulate API logic and caching policies.

## 9. Testing Strategy
- Unit tests with Vitest for hooks/services.
- React Testing Library for drawer forms and data tables.
- Playwright for critical flows: login, start sync, view failed records, pending children.
- Storybook stories for shared components.
- MSW service worker for API mocking during testing.

This plan ensures the SyncFlow frontend remains consistent with backend expectations, supports multi-language users, and meets enterprise-grade UX standards.
