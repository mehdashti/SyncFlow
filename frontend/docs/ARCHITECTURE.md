# معماری فرانت‌اند - SyncFlow

**Version: 2.1.0**
**Aligned with Enterprise Design System v2.1**

> Related Documentation:
> - [DESIGN_TOKENS.md](./DESIGN_TOKENS.md) - Design tokens & color system
> - [FRONTEND_STANDARDS.md](./FRONTEND_STANDARDS.md) - Code standards
> - [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) - UI components

این سند معماری و ساختار پروژه SyncFlow را شرح می‌دهد.

## فهرست

1. [نمای کلی](#نمای-کلی)
2. [Tech Stack](#tech-stack)
3. [معماری کلی](#معماری-کلی)
4. [Data Flow](#data-flow)
5. [Routing](#routing)
6. [State Management](#state-management)
7. [API Communication](#api-communication)
8. [Internationalization](#internationalization)
9. [Theme & Styling](#theme--styling)
10. [Security](#security)

---

## نمای کلی

**SyncFlow** یک پلتفرم مدیریت Data Sync است که داده‌ها را از APISmith (یک API Management platform) دریافت کرده و به دیتابیس منتقل می‌کند.

### هدف پروژه

- **کاوش API‌ها** از APISmith instances (Connectors)
- **پیکربندی Sync** - delta strategies, schedules
- **اجرای Sync** - دستی یا خودکار
- **مانیتورینگ** - وضعیت sync ها، failed records
- **مدیریت Schedules** - Cron-based scheduling

---

## Tech Stack

### Core

| تکنولوژی | نسخه | کاربرد |
|----------|------|--------|
| **React** | 19.2 | UI Framework |
| **TypeScript** | ~5.9 | Type Safety |
| **Vite** | 7.2 | Build Tool |
| **Tailwind CSS** | 4.1 | Styling |

### Routing & State

| تکنولوژی | نسخه | کاربرد |
|----------|------|--------|
| **TanStack Router** | 1.141 | File-based Routing |
| **TanStack Query** | 5.90 | Server State Management |
| **Zustand** | 5.0 | Client State Management |

### UI Components

| تکنولوژی | نسخه | کاربرد |
|----------|------|--------|
| **shadcn/ui** | - | Component Library (Radix UI based) |
| **Radix UI** | - | Headless UI Primitives |
| **Lucide React** | 0.556 | Icons |
| **Vaul** | 1.1 | Drawer component |

### Forms & Validation

| تکنولوژی | نسخه | کاربرد |
|----------|------|--------|
| **React Hook Form** | 7.68 | Form Management |
| **Zod** | 4.1 | Schema Validation |

### i18n & Utilities

| تکنولوژی | نسخه | کاربرد |
|----------|------|--------|
| **i18next** | 25.7 | Internationalization |
| **react-i18next** | 16.4 | React Integration |
| **date-fns** | 4.1 | Date Formatting |
| **Axios** | 1.13 | HTTP Client |
| **Sonner** | 2.0 | Toast Notifications |

---

## معماری کلی

### Layer Architecture

```
┌─────────────────────────────────────────────────┐
│                    UI Layer                      │
│  (Pages, Components, Forms, Layouts)            │
├─────────────────────────────────────────────────┤
│              State Management Layer              │
│  (Zustand Stores, TanStack Query Cache)         │
├─────────────────────────────────────────────────┤
│                 Service Layer                    │
│  (API Services, Business Logic)                 │
├─────────────────────────────────────────────────┤
│               Infrastructure Layer               │
│  (Axios Client, Router, i18n, Theme)            │
└─────────────────────────────────────────────────┘
```

### Feature-Based Organization

```
features/
├── connectors/        # APISmith instance management
├── entities/          # Discovered APIs from Connectors
├── sync/              # Sync run monitoring & failed records
├── schedules/         # Cron-based sync scheduling
├── dashboard/         # Overview & statistics
└── settings/          # User preferences
```

هر feature شامل:
- `pages/` - صفحات route شده
- `components/` - کامپوننت‌های اختصاصی feature
- (آینده) `hooks/` - custom hooks

---

## Data Flow

### 1. User Action → Component

```typescript
// مثال: Trigger Sync
function SyncButton({ entityUid }: { entityUid: string }) {
  const syncMutation = useMutation({
    mutationFn: () => syncService.trigger(entityUid),
    onSuccess: () => {
      toast.success('Sync started')
      queryClient.invalidateQueries({ queryKey: ['sync-runs'] })
    },
  })

  return (
    <Button onClick={() => syncMutation.mutate()}>
      Sync Now
    </Button>
  )
}
```

### 2. Mutation → Service → API

```typescript
// api/services/sync.service.ts
export const syncService = {
  trigger: async (entityUid: string): Promise<SyncRun> => {
    const response = await apiClient.post(`/entities/${entityUid}/sync`)
    return response.data
  },
}
```

### 3. API Response → Cache → UI Update

```typescript
// TanStack Query automatically:
// 1. Updates cache
// 2. Invalidates related queries
// 3. Re-renders dependent components
```

---

## Routing

### File-Based Routing (TanStack Router)

```
routes/
├── __root.tsx              # Root layout
├── _app/                   # Authenticated routes
│   ├── dashboard.tsx       # /dashboard
│   ├── connectors.tsx      # /connectors
│   ├── entities.tsx        # /entities
│   ├── sync.tsx            # /sync
│   ├── schedules.tsx       # /schedules
│   ├── failed-records.tsx  # /failed-records
│   └── settings.tsx        # /settings
└── index.tsx               # / (redirect to dashboard)
```

### Route Navigation

```typescript
import { useNavigate } from '@tanstack/react-router'

function Component() {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate({ to: '/connectors' })
  }
}
```

### Route Params

```typescript
// Route: /entities/$uid
import { useParams } from '@tanstack/react-router'

function EntityDetailPage() {
  const { uid } = useParams({ from: '/entities/$uid' })

  const { data: entity } = useQuery({
    queryKey: ['entity', uid],
    queryFn: () => entitiesService.getById(uid),
  })
}
```

---

## State Management

### Zustand - Client State

برای state هایی که:
- Local هستند (UI state)
- Persist می‌شوند (localStorage)
- Global هستند اما server-side نیستند

```typescript
// مثال: User Preferences Store
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PreferencesState {
  theme: 'light' | 'dark'
  locale: string
  setTheme: (theme: 'light' | 'dark') => void
  setLocale: (locale: string) => void
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: 'light',
      locale: 'en',
      setTheme: (theme) => set({ theme }),
      setLocale: (locale) => set({ locale }),
    }),
    {
      name: 'preferences-storage',
    }
  )
)
```

### TanStack Query - Server State

برای state هایی که:
- از server می‌آیند
- Cache می‌شوند
- Auto-refetch دارند
- Invalidation دارند

```typescript
// Query - Read
const { data, isLoading, error } = useQuery({
  queryKey: ['connectors'],
  queryFn: connectorsService.getAll,
  staleTime: 5 * 60 * 1000, // 5 minutes
})

// Mutation - Write
const mutation = useMutation({
  mutationFn: connectorsService.create,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['connectors'] })
  },
})
```

---

## API Communication

### Axios Client

```typescript
// api/client.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor (برای auth)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor (برای error handling)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error)
  }
)
```

### Service Pattern

```typescript
// api/services/connectors.service.ts
import { apiClient } from '../client'
import type { Connector, ConnectorCreate } from '@/types'

export const connectorsService = {
  getAll: async (): Promise<Connector[]> => {
    const response = await apiClient.get('/connectors')
    return Array.isArray(response.data) ? response.data : response.data.items
  },

  create: async (data: ConnectorCreate): Promise<Connector> => {
    const response = await apiClient.post('/connectors', data)
    return response.data
  },
}
```

---

## Internationalization

### پشتیبانی از 4 زبان

- **English** (en) - LTR
- **فارسی** (fa) - RTL
- **العربية** (ar) - RTL
- **Türkçe** (tr) - LTR

### i18n Setup

```typescript
// lib/i18n.ts
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslations },
      fa: { translation: faTranslations },
      ar: { translation: arTranslations },
      tr: { translation: trTranslations },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })
```

### RTL Support

```typescript
// در تغییر زبان
useEffect(() => {
  document.dir = ['fa', 'ar'].includes(i18n.language) ? 'rtl' : 'ltr'
}, [i18n.language])
```

---

## Theme & Styling

### Dark Mode Support

```typescript
// ذخیره در localStorage
const theme = localStorage.getItem('theme') || 'light'
document.documentElement.classList.toggle('dark', theme === 'dark')
```

### Tailwind Configuration

```javascript
// tailwind.config.js
export default {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: 'hsl(var(--primary))',
        // ...
      },
    },
  },
}
```

### CSS Variables

```css
/* globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 3.9%;
    --primary: 221.2 83.2% 53.3%;
    /* ... */
  }

  .dark {
    --background: 0 0% 3.9%;
    --foreground: 0 0% 98%;
    --primary: 217.2 91.2% 59.8%;
    /* ... */
  }
}
```

---

## Security

### Authentication (آینده)

```typescript
// فعلاً بدون auth - آینده:
// JWT token in localStorage
// Protected routes با middleware
// Role-based access control
```

### XSS Prevention

- استفاده از React (auto-escaping)
- عدم استفاده از `dangerouslySetInnerHTML`
- Sanitize user inputs

### CORS

```typescript
// Backend باید این headerها را برگرداند:
// Access-Control-Allow-Origin
// Access-Control-Allow-Methods
// Access-Control-Allow-Headers
```

---

## Performance Optimizations

### Code Splitting

```typescript
// Lazy loading routes
const ConnectorsPage = lazy(() => import('./features/connectors/pages/ConnectorsPage'))
```

### Query Caching

```typescript
// staleTime & gcTime
useQuery({
  queryKey: ['connectors'],
  queryFn: connectorsService.getAll,
  staleTime: 5 * 60 * 1000,   // 5 minutes fresh
  gcTime: 30 * 60 * 1000,     // 30 minutes cache
})
```

### Memoization

```typescript
const filteredEntities = useMemo(() => {
  return entities.filter(e => e.sync_enabled)
}, [entities])
```

---

## Build & Deployment

### Build

```bash
pnpm run build
# Output: dist/
```

### Environment Variables

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Production

```bash
# Build
pnpm run build

# Preview
pnpm run preview

# Deploy dist/ to static hosting (Nginx, Vercel, Netlify, etc.)
```

---

## Domain Model

### Core Entities

```
┌─────────────┐
│  Connector  │ (APISmith Instance)
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐
│   Entity    │ (Discovered API)
└──────┬──────┘
       │ 1:N
       ▼
┌─────────────┐         ┌─────────────┐
│  Sync Run   │ 1:N     │  Schedule   │
└──────┬──────┘────────►└─────────────┘
       │ 1:N
       ▼
┌─────────────┐
│Failed Record│
└─────────────┘
```

### Entity Relationships

- **Connector** (1) → (N) **Entity**
- **Entity** (1) → (N) **Sync Run**
- **Entity** (1) → (1) **Schedule** (optional)
- **Sync Run** (1) → (N) **Failed Record**

---

## توسعه آینده

### Phase 1 - Standardization (در دست اجرا)

- ✅ ایجاد `api/endpoints.ts`
- ✅ تقسیم `types/index.ts` به domain files
- ✅ Restructure translations به folder-based
- ✅ ایجاد کامپوننت‌های سفارشی (StatusBadge, etc.)

### Phase 2 - UX Improvements

- Wizard برای Connector/Entity setup
- Real-time Sync progress با WebSocket
- Advanced filtering و search
- Bulk operations

### Phase 3 - Advanced Features

- Data lineage visualization
- Sync performance analytics
- Custom transformation rules
- Multi-database support

---

*ایجاد شده: دسامبر 2025*
