# استانداردهای فرانت‌اند - SyncFlow

**Version: 2.1.0**
**Aligned with Enterprise Design System v2.1**

> Related Documentation:
> - [DESIGN_TOKENS.md](./DESIGN_TOKENS.md) - Design tokens & color system
> - [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
> - [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) - UI components

این سند شامل قوانین و استانداردهای کدنویسی پروژه SyncFlow است.

## فهرست

1. [ساختار پروژه](#ساختار-پروژه)
2. [نام‌گذاری](#نام‌گذاری)
3. [کامپوننت‌ها](#کامپوننت‌ها)
4. [State Management](#state-management)
5. [API Integration](#api-integration)
6. [Styling](#styling)
7. [Internationalization](#internationalization)
8. [Testing](#testing)
9. [Performance](#performance)

---

## ساختار پروژه

```
frontend/
├── src/
│   ├── api/                    # API layer
│   │   ├── client.ts           # Axios instance
│   │   └── services/           # Service functions
│   │       ├── connectors.service.ts
│   │       ├── entities.service.ts
│   │       ├── sync.service.ts
│   │       ├── schedules.service.ts
│   │       └── index.ts
│   │
│   ├── components/             # Shared components
│   │   ├── layout/             # Layout components
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   └── LanguageSwitcher.tsx
│   │   └── ui/                 # UI primitives (shadcn/ui)
│   │       ├── button.tsx
│   │       ├── badge.tsx
│   │       ├── card.tsx
│   │       └── ...
│   │
│   ├── features/               # Feature modules
│   │   ├── connectors/
│   │   │   ├── components/
│   │   │   │   └── ConnectorForm.tsx
│   │   │   └── pages/
│   │   │       └── ConnectorsPage.tsx
│   │   │
│   │   ├── entities/
│   │   │   ├── components/
│   │   │   │   └── EntityForm.tsx
│   │   │   └── pages/
│   │   │       └── EntitiesPage.tsx
│   │   │
│   │   ├── sync/
│   │   │   ├── components/
│   │   │   └── pages/
│   │   │       ├── SyncPage.tsx
│   │   │       └── FailedRecordsPage.tsx
│   │   │
│   │   ├── schedules/
│   │   │   ├── components/
│   │   │   │   └── ScheduleForm.tsx
│   │   │   └── pages/
│   │   │       └── SchedulesPage.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   └── pages/
│   │   │       └── DashboardPage.tsx
│   │   │
│   │   └── settings/
│   │       └── pages/
│   │           └── SettingsPage.tsx
│   │
│   ├── lib/                    # Utilities
│   │   ├── utils.ts
│   │   └── i18n.ts
│   │
│   ├── locales/                # i18n (flat structure - needs restructuring)
│   │   ├── en.json
│   │   ├── fa.json
│   │   ├── ar.json
│   │   └── tr.json
│   │
│   ├── store/                  # Zustand stores
│   │
│   ├── styles/                 # Global styles
│   │   └── globals.css
│   │
│   ├── types/                  # TypeScript types
│   │   └── index.ts            # All types (needs restructuring)
│   │
│   └── routes/                 # TanStack Router
│       └── __root.tsx
│
└── docs/                       # Documentation
```

---

## نام‌گذاری

### فایل‌ها

| نوع | قالب | مثال |
|-----|------|------|
| کامپوننت React | PascalCase | `ConnectorForm.tsx` |
| Hook | camelCase با پیشوند use | `useConnectorTest.ts` |
| Service | camelCase با پسوند .service | `connectors.service.ts` |
| Types | camelCase با پسوند .types | `connector.types.ts` (آینده) |
| Store | camelCase با پسوند Store | `connectorStore.ts` |
| Utility | camelCase | `utils.ts` |

### کامپوننت‌ها

```typescript
// Good - PascalCase
export function ConnectorForm() { ... }
export function SyncStatusBadge() { ... }

// Bad
export function connectorForm() { ... }
export function sync_status_badge() { ... }
```

### Props Interface

```typescript
// Good - نام کامپوننت + Props
interface ConnectorFormProps {
  connector?: Connector
  onSubmit: (data: ConnectorCreate) => void
  onCancel: () => void
}

// Bad
interface Props { ... }
interface IConnectorForm { ... }
```

### متغیرها و توابع

```typescript
// camelCase برای متغیرها
const isActive = true
const connectorUid = '...'

// camelCase برای توابع
function handleTest() { ... }
function getConnectorStatus() { ... }

// UPPER_SNAKE_CASE برای constants
const API_BASE_URL = '...'
const SYNC_INTERVALS = [ ... ]
```

---

## کامپوننت‌ها

### ساختار کامپوننت

```typescript
// 1. Imports - ترتیب: react, libraries, local
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Connector } from '@/types'

// 2. Types/Interfaces
interface ConnectorCardProps {
  connector: Connector
  onSelect: (conn: Connector) => void
  className?: string
}

// 3. Component
export function ConnectorCard({
  connector,
  onSelect,
  className,
}: ConnectorCardProps) {
  const { t } = useTranslation()

  // 4. Hooks اول
  const [isHovered, setIsHovered] = useState(false)

  // 5. Derived state
  const isActive = connector.is_active && connector.last_test_success === true

  // 6. Handlers
  const handleClick = () => {
    onSelect(connector)
  }

  // 7. Render
  return (
    <div className={cn('p-4 rounded-lg', className)}>
      {/* ... */}
    </div>
  )
}
```

### الگوهای رایج

#### Conditional Rendering

```typescript
// Good - Early return
if (isLoading) {
  return <Skeleton />
}

if (!data) {
  return <EmptyState />
}

return <DataView data={data} />

// Good - Inline ternary (برای کوتاه)
{isActive ? <CheckIcon /> : <XIcon />}

// Bad - Nested ternaries
{isActive ? <A /> : isError ? <B /> : <C />}
```

---

## State Management

### Zustand Store Pattern

```typescript
// store/connectorStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ConnectorState {
  // State
  selectedConnectorUid: string | null

  // Actions
  selectConnector: (uid: string | null) => void
  reset: () => void
}

const initialState = {
  selectedConnectorUid: null,
}

export const useConnectorStore = create<ConnectorState>()(
  persist(
    (set) => ({
      ...initialState,

      selectConnector: (uid) => set({ selectedConnectorUid: uid }),

      reset: () => set(initialState),
    }),
    {
      name: 'connector-storage',
    }
  )
)
```

### TanStack Query Pattern

```typescript
// Query
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['connectors'],
  queryFn: connectorsService.getAll,
  staleTime: 60000, // 1 minute
})

// Mutation
const mutation = useMutation({
  mutationFn: connectorsService.create,
  onSuccess: (data) => {
    toast.success(t('success.created'))
    queryClient.invalidateQueries({ queryKey: ['connectors'] })
  },
  onError: (error) => {
    toast.error(error.message)
  },
})
```

---

## API Integration

### ⚠️ وضعیت فعلی (نیاز به بهبود)

**مشکل:** Endpoints مستقیم در service ها هاردکد شده‌اند.

```typescript
// فعلی - نیاز به بهبود
const response = await apiClient.get<Connector>(`/connectors/${uid}`)
```

### ✅ استاندارد پیشنهادی (مشابه APISmith)

**باید ایجاد شود:** `api/endpoints.ts`

```typescript
// api/endpoints.ts
export const API_ENDPOINTS = {
  CONNECTORS: {
    LIST: '/connectors',
    DETAIL: (uid: string) => `/connectors/${uid}`,
    CREATE: '/connectors',
    UPDATE: (uid: string) => `/connectors/${uid}`,
    DELETE: (uid: string) => `/connectors/${uid}`,
    TEST: (uid: string) => `/connectors/${uid}/test`,
    DISCOVER: (uid: string) => `/connectors/${uid}/discover`,
  },
  ENTITIES: {
    LIST: '/entities',
    DETAIL: (uid: string) => `/entities/${uid}`,
    CREATE: '/entities',
    UPDATE: (uid: string) => `/entities/${uid}`,
    DELETE: (uid: string) => `/entities/${uid}`,
  },
  SYNC: {
    LIST: '/sync-runs',
    DETAIL: (uid: string) => `/sync-runs/${uid}`,
    TRIGGER: (entityUid: string) => `/entities/${entityUid}/sync`,
  },
  SCHEDULES: {
    LIST: '/schedules',
    DETAIL: (uid: string) => `/schedules/${uid}`,
    CREATE: '/schedules',
    UPDATE: (uid: string) => `/schedules/${uid}`,
    DELETE: (uid: string) => `/schedules/${uid}`,
  },
  FAILED_RECORDS: {
    LIST: '/failed-records',
    DETAIL: (uid: string) => `/failed-records/${uid}`,
    RETRY: (uid: string) => `/failed-records/${uid}/retry`,
  },
  DASHBOARD: {
    STATS: '/dashboard/stats',
    RECENT_SYNCS: '/dashboard/recent-syncs',
  },
} as const
```

### Service Pattern (پس از بهبود)

```typescript
// api/services/connectors.service.ts
import { apiClient } from '../client'
import { API_ENDPOINTS } from '../endpoints'
import type { Connector, ConnectorCreate } from '@/types'

export const connectorsService = {
  getAll: async (): Promise<Connector[]> => {
    const response = await apiClient.get(API_ENDPOINTS.CONNECTORS.LIST)
    return Array.isArray(response.data) ? response.data : response.data.items
  },

  getById: async (uid: string): Promise<Connector> => {
    const response = await apiClient.get(API_ENDPOINTS.CONNECTORS.DETAIL(uid))
    return response.data
  },

  test: async (uid: string): Promise<TestConnectionResult> => {
    const response = await apiClient.post(API_ENDPOINTS.CONNECTORS.TEST(uid))
    return response.data
  },
}
```

---

## Styling

### Tailwind CSS Conventions

```typescript
// استفاده از cn() برای conditional classes
import { cn } from '@/lib/utils'

<div className={cn(
  // Base classes اول
  'flex items-center gap-2 p-4 [border-radius:3px]',
  // Conditional classes
  isActive && 'bg-primary/10 border-primary',
  isDisabled && 'opacity-50 cursor-not-allowed',
  // Props className آخر
  className
)}>
```

### Border Radius Standard

**⚠️ قانون مهم: حداکثر border-radius مجاز 3px است!**

```typescript
// ✅ Correct - استاندارد مشابه APISmith
'[border-radius:3px]'  // پیش‌فرض برای همه کامپوننت‌ها
'[border-radius:2px]'  // فقط برای عناصر خیلی کوچک (Checkbox)
'rounded-full'         // فقط برای دایره‌ها (Status dots, Pills)

// ❌ Wrong - بیش از 3px ممنوع
'rounded-md'   // 6px - ممنوع
'rounded-lg'   // 8px - ممنوع
'rounded-xl'   // 12px - ممنوع
```

**کاربردها:**
| Component Type | Border Radius | مثال |
|----------------|---------------|------|
| Controls | `[border-radius:3px]` | Button, Input, Select |
| Containers | `[border-radius:3px]` | Card, Dialog, Panel |
| Small Elements | `[border-radius:2px]` | Checkbox |
| Status Indicators | `rounded-full` | Sync status dots |

### Color Conventions - Semantic Colors (v2.1)

**Use semantic color tokens instead of hardcoded colors!**

See [DESIGN_TOKENS.md](./DESIGN_TOKENS.md) for full color system documentation.

```typescript
// ✅ CORRECT - Use semantic colors (three-part system)
const syncStatusColors = {
  success: {
    text: 'text-success',
    bg: 'bg-success-bg',
    border: 'border-success-border',
  },
  failed: {
    text: 'text-destructive',
    bg: 'bg-destructive-bg',
    border: 'border-destructive-border',
  },
  running: {
    text: 'text-info',
    bg: 'bg-info-bg',
    border: 'border-info-border',
  },
  pending: {
    text: 'text-warning',
    bg: 'bg-warning-bg',
    border: 'border-warning-border',
  },
}

// ❌ WRONG - Hardcoded colors
const badColors = {
  success: 'text-green-600 dark:text-green-400',  // Use text-success
  error: 'text-red-600 dark:text-red-400',        // Use text-destructive
  warning: 'text-yellow-600 dark:text-yellow-400', // Use text-warning
  running: 'text-blue-600 dark:text-blue-400',    // Use text-info
}

// Background with Alpha (still valid for primary/muted)
'bg-primary/10'  // 10% opacity
'bg-muted/50'    // 50% opacity
```

### Color Migration Guide

| Old Pattern | New Pattern |
|-------------|-------------|
| `text-green-600 dark:text-green-400` | `text-success` |
| `text-red-600 dark:text-red-400` | `text-destructive` |
| `text-yellow-600 dark:text-yellow-400` | `text-warning` |
| `text-blue-600 dark:text-blue-400` | `text-info` |
| `bg-green-100 dark:bg-green-900/30` | `bg-success-bg` |
| `bg-red-100 dark:bg-red-900/30` | `bg-destructive-bg` |
| `bg-yellow-100 dark:bg-yellow-900/30` | `bg-warning-bg` |
| `bg-blue-100 dark:bg-blue-900/30` | `bg-info-bg` |

---

## Internationalization

### ⚠️ وضعیت فعلی (نیاز به بهبود)

**مشکل:** فایل‌های flat در `locales/` - باید folder-based شود.

```
locales/
├── en.json
├── fa.json
├── ar.json
└── tr.json
```

### ✅ استاندارد پیشنهادی (مشابه APISmith)

```
locales/
├── en/
│   └── translation.json
├── fa/
│   └── translation.json
├── ar/
│   └── translation.json
└── tr/
    └── translation.json
```

### Translation Keys Pattern

```json
{
  "connectors": {
    "title": "APISmith Connectors",
    "create": "Add Connector",
    "test": "Test Connection",
    "discover": "Discover APIs",
    "status": {
      "active": "Active",
      "inactive": "Inactive",
      "testing": "Testing..."
    }
  },
  "entities": {
    "title": "Entities",
    "sync": "Sync Now",
    "deltaStrategy": {
      "full": "Full Sync",
      "rowversion": "Incremental (RowVersion)",
      "hash": "Hash-based"
    }
  }
}
```

### Usage

```typescript
const { t } = useTranslation()

// Simple
t('connectors.title')

// With interpolation
t('sync.recordsProcessed', { count: 150 })

// Dynamic key
t(`entities.deltaStrategy.${strategy}`)
```

---

## Testing

### Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { ConnectorCard } from './ConnectorCard'

describe('ConnectorCard', () => {
  const mockConnector = {
    uid: '123',
    name: 'Test Connector',
    base_url: 'https://api.example.com',
    is_active: true,
  }

  it('renders connector name', () => {
    render(<ConnectorCard connector={mockConnector} />)
    expect(screen.getByText('Test Connector')).toBeInTheDocument()
  })

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn()
    render(<ConnectorCard connector={mockConnector} onSelect={onSelect} />)

    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith(mockConnector)
  })
})
```

---

## Performance

### Lazy Loading

```typescript
// Routes
const ConnectorsPage = lazy(() => import('./features/connectors/pages/ConnectorsPage'))

// In router
<Suspense fallback={<PageSkeleton />}>
  <ConnectorsPage />
</Suspense>
```

### Memoization

```typescript
// برای expensive calculations
const filteredEntities = useMemo(() => {
  return entities.filter(entity => entity.sync_enabled)
}, [entities])

// برای callback stability
const handleSync = useCallback((entityUid: string) => {
  syncMutation.mutate(entityUid)
}, [syncMutation])
```

### Query Optimization

```typescript
// staleTime برای کاهش requests
useQuery({
  queryKey: ['connectors'],
  queryFn: connectorsService.getAll,
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 30 * 60 * 1000,   // 30 minutes cache
})
```

---

## تسک‌های بهبود (Roadmap)

### High Priority

1. ✅ ایجاد `api/endpoints.ts` - جداسازی endpoints از services
2. ✅ تقسیم `types/index.ts` به فایل‌های domain-specific:
   - `connector.types.ts`
   - `entity.types.ts`
   - `sync.types.ts`
   - `schedule.types.ts`
3. ✅ ایجاد کامپوننت‌های سفارشی:
   - `components/ui/status-badge.tsx`
   - `components/ui/latency-indicator.tsx`
4. ✅ تبدیل translations به folder-based structure

### Medium Priority

5. بهبود Feature structure - اضافه کردن `hooks/` و `components/list/`, `components/detail/`
6. ایجاد Wizard pattern برای Connector/Entity creation
7. اضافه کردن E2E tests

### Low Priority

8. مستندسازی Component Library
9. مستندسازی Architecture

---

## Code Review Checklist

- [ ] نام‌گذاری مناسب (PascalCase/camelCase)
- [ ] Types کامل و بدون `any`
- [ ] استفاده از `cn()` برای conditional classes
- [ ] ترجمه‌ها در هر چهار زبان (en, fa, ar, tr)
- [ ] Loading و Error states پوشش داده شده
- [ ] Console.log ها حذف شده
- [ ] Dark mode تست شده
- [ ] Responsive تست شده (4 زبان با RTL support)

---

*ایجاد شده: دسامبر 2025*
