# کتابخانه کامپوننت‌ها - SyncFlow

**Version: 2.1.0**
**Aligned with Enterprise Design System v2.1**

> Related Documentation:
> - [DESIGN_TOKENS.md](./DESIGN_TOKENS.md) - Design tokens & color system
> - [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
> - [FRONTEND_STANDARDS.md](./FRONTEND_STANDARDS.md) - Code standards

راهنمای کامپوننت‌های UI پروژه SyncFlow

## فهرست

1. [کامپوننت‌های پایه (UI Primitives)](#کامپوننت‌های-پایه)
2. [کامپوننت‌های Layout](#کامپوننت‌های-layout)
3. [کامپوننت‌های سفارشی (در دست طراحی)](#کامپوننت‌های-سفارشی)
4. [الگوهای Feature-Specific](#الگوهای-feature-specific)

---

## کامپوننت‌های پایه

این کامپوننت‌ها بر پایه [shadcn/ui](https://ui.shadcn.com/) هستند.

### Button

```tsx
import { Button } from '@/components/ui/button'

// Variants
<Button variant="default">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Destructive</Button>

// Sizes
<Button size="default">Default</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button size="icon"><Icon /></Button>

// With Icon
<Button>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Syncing...
</Button>
```

### Badge

```tsx
import { Badge } from '@/components/ui/badge'

// Variants
<Badge variant="default">Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="outline">Outline</Badge>
<Badge variant="destructive">Failed</Badge>

// Sync Status Examples
<Badge variant="success" className="gap-1">
  <CheckCircle className="h-3 w-3" />
  Success
</Badge>

<Badge variant="destructive">Failed</Badge>

<Badge className="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
  <Loader2 className="h-3 w-3 animate-spin mr-1" />
  Running
</Badge>
```

### Card

```tsx
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Connector Details</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Base URL: https://api.example.com</p>
  </CardContent>
  <CardFooter>
    <Button>Test Connection</Button>
  </CardFooter>
</Card>
```

### Input & Form

```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

<div className="space-y-2">
  <Label htmlFor="name">Connector Name</Label>
  <Input
    id="name"
    placeholder="Enter connector name..."
    value={value}
    onChange={(e) => setValue(e.target.value)}
  />
</div>
```

### Select

```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

<Select value={deltaStrategy} onValueChange={setDeltaStrategy}>
  <SelectTrigger>
    <SelectValue placeholder="Select sync strategy" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="full">Full Sync</SelectItem>
    <SelectItem value="rowversion">Incremental (RowVersion)</SelectItem>
    <SelectItem value="hash">Hash-based</SelectItem>
  </SelectContent>
</Select>
```

### Switch

```tsx
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

<div className="flex items-center space-x-2">
  <Switch
    id="sync-enabled"
    checked={syncEnabled}
    onCheckedChange={setSyncEnabled}
  />
  <Label htmlFor="sync-enabled">Enable Auto-Sync</Label>
</div>
```

### Tabs

```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="schema">Schema</TabsTrigger>
    <TabsTrigger value="history">History</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">
    {/* Overview content */}
  </TabsContent>
  <TabsContent value="schema">
    {/* Schema content */}
  </TabsContent>
</Tabs>
```

### Tooltip

```tsx
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="ghost" size="icon">
        <Info className="h-4 w-4" />
      </Button>
    </TooltipTrigger>
    <TooltipContent side="top">
      <p>This will trigger a full sync</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

### Checkbox

```tsx
import { Checkbox } from '@/components/ui/checkbox'

<div className="flex items-center space-x-2">
  <Checkbox
    id="business-key"
    checked={isBusinessKey}
    onCheckedChange={setIsBusinessKey}
  />
  <label htmlFor="business-key" className="text-sm">
    Use as Business Key
  </label>
</div>
```

---

## کامپوننت‌های Layout

### AppShell

Shell اصلی اپلیکیشن با Sidebar و Header.

```tsx
import { AppShell } from '@/components/layout/AppShell'

function App() {
  return (
    <AppShell>
      <YourPageContent />
    </AppShell>
  )
}
```

**ساختار:**
- **Sidebar** - Navigation با آیکون‌ها
- **Header** - عنوان صفحه + Theme Toggle + Language Switcher
- **Main Content** - محتوای اصلی صفحه

### Sidebar

```tsx
import { Sidebar } from '@/components/layout/Sidebar'

// فقط در AppShell استفاده می‌شود
```

**Navigation Items:**
- Dashboard
- Connectors
- Entities
- Sync Runs
- Schedules
- Failed Records
- Settings

### Header

```tsx
import { Header } from '@/components/layout/Header'

<Header title={t('connectors.title')} />
```

### ThemeToggle

```tsx
import { ThemeToggle } from '@/components/layout/ThemeToggle'

// Light/Dark mode toggle
<ThemeToggle />
```

### LanguageSwitcher

```tsx
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'

// 4 زبان: English, فارسی, العربية, Türkçe
<LanguageSwitcher />
```

---

## کامپوننت‌های سفارشی (در دست طراحی)

این کامپوننت‌ها هنوز ایجاد نشده‌اند و جزو تسک‌های آینده هستند.

### StatusBadge (پیشنهادی)

نمایش وضعیت Connector/Sync با امکان تست.

```tsx
// باید ایجاد شود: components/ui/status-badge.tsx
import { StatusBadge, getStatusFromTestResult } from '@/components/ui/status-badge'

// مشابه APISmith
<StatusBadge
  status="connected"
  latencyMs={45}
  onTest={() => handleTest()}
/>

// Status Types
type ConnectionStatus = 'connected' | 'error' | 'testing' | 'untested'
type SyncStatus = 'success' | 'failed' | 'running'
```

### LatencyIndicator (پیشنهادی)

نمایش latency با رنگ‌بندی.

```tsx
// باید ایجاد شود: components/ui/latency-indicator.tsx
import { LatencyIndicator } from '@/components/ui/latency-indicator'

<LatencyIndicator latencyMs={45} />

// رنگ‌بندی:
// < 100ms: سبز
// 100-500ms: زرد
// > 500ms: قرمز
```

### SyncProgressBar (پیشنهادی)

نوار پیشرفت برای Sync Runs.

```tsx
// باید ایجاد شود: components/ui/sync-progress-bar.tsx
import { SyncProgressBar } from '@/components/ui/sync-progress-bar'

<SyncProgressBar
  current={1500}
  total={10000}
  status="running"
/>
```

---

## الگوهای Feature-Specific

### ConnectorForm

فرم ایجاد/ویرایش Connector.

```tsx
import { ConnectorForm } from '@/features/connectors/components/ConnectorForm'

<ConnectorForm
  connector={existingConnector} // optional برای edit
  onSubmit={(data) => handleSubmit(data)}
  onCancel={() => setOpen(false)}
/>
```

**فیلدها:**
- Name
- Base URL
- Auth Token (optional)
- Is Active (switch)

### EntityForm

فرم ویرایش تنظیمات Entity.

```tsx
import { EntityForm } from '@/features/entities/components/EntityForm'

<EntityForm
  entity={entity}
  onSubmit={(data) => handleUpdate(data)}
  onCancel={() => setOpen(false)}
/>
```

**فیلدها:**
- Sync Enabled (switch)
- Sync Interval (seconds)
- Target Schema
- Target Table

### ScheduleForm

فرم ایجاد/ویرایش Schedule.

```tsx
import { ScheduleForm } from '@/features/schedules/components/ScheduleForm'

<ScheduleForm
  schedule={existingSchedule} // optional برای edit
  onSubmit={(data) => handleSubmit(data)}
  onCancel={() => setOpen(false)}
/>
```

**فیلدها:**
- Entity (select)
- Cron Expression
- Is Active (switch)

---

## الگوهای Layout

### List + Detail Panel (SAP Fiori Pattern)

```tsx
// دو ستونی
<div className="grid grid-cols-[1fr_400px] h-full">
  <div className="overflow-auto">
    {/* List View */}
    <ConnectorsList />
  </div>
  <div className="border-l p-4">
    {/* Detail Panel */}
    {selectedConnector && (
      <ConnectorDetailPanel connector={selectedConnector} />
    )}
  </div>
</div>
```

### Loading States

```tsx
// Skeleton for text
<div className="h-4 bg-muted/50 animate-pulse rounded" />

// Skeleton for card
<div className="h-16 bg-muted/50 animate-pulse rounded-lg" />

// Multiple skeletons
<div className="space-y-2">
  {[1, 2, 3].map((i) => (
    <div key={i} className="h-12 bg-muted/50 animate-pulse rounded-lg" />
  ))}
</div>

// Button loading
<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Syncing...
</Button>
```

### Empty States

```tsx
<div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
  <Database className="h-12 w-12 mb-4 opacity-50" />
  <p>{t('common.noData')}</p>
  <Button className="mt-4" onClick={handleCreate}>
    Create First Connector
  </Button>
</div>
```

### Error States

```tsx
// ✅ Use semantic colors (Design System v2.1)
<div className="p-4 rounded-[3px] bg-destructive-bg border border-destructive-border">
  <div className="flex items-center gap-2 text-destructive">
    <AlertCircle className="h-5 w-5" />
    <span className="font-medium">Sync Failed</span>
  </div>
  <p className="mt-2 text-sm text-muted-foreground">
    {error.message}
  </p>
  <Button className="mt-3" variant="outline" size="sm" onClick={handleRetry}>
    Retry
  </Button>
</div>
```

### Success States

```tsx
// ✅ Use semantic colors (Design System v2.1)
<div className="p-4 rounded-[3px] bg-success-bg border border-success-border">
  <div className="flex items-center gap-2 text-success">
    <CheckCircle className="h-5 w-5" />
    <span className="font-medium">Sync Completed Successfully!</span>
  </div>
  <p className="mt-2 text-sm text-muted-foreground">
    {recordsProcessed} records synced in {duration}s
  </p>
</div>
```

### Warning States

```tsx
// ✅ Use semantic colors (Design System v2.1)
<div className="p-4 rounded-[3px] bg-warning-bg border border-warning-border">
  <div className="flex items-center gap-2 text-warning">
    <AlertTriangle className="h-5 w-5" />
    <span className="font-medium">Sync Pending</span>
  </div>
</div>
```

### Info States

```tsx
// ✅ Use semantic colors (Design System v2.1)
<div className="p-4 rounded-[3px] bg-info-bg border border-info-border">
  <div className="flex items-center gap-2 text-info">
    <Info className="h-5 w-5" />
    <span className="font-medium">Sync Running</span>
  </div>
</div>
```

---

## Utility Classes

### رنگ‌های متداول - Semantic Colors (v2.1)

**استفاده از توکن‌های semantic بجای رنگ‌های hardcoded**

```css
/* ✅ Use semantic tokens from globals.css */
.text-success       /* Success text */
.text-destructive   /* Error text */
.text-warning       /* Warning text */
.text-info          /* Info/Running text */

.bg-success-bg      /* Success background */
.bg-destructive-bg  /* Error background */
.bg-warning-bg      /* Warning background */
.bg-info-bg         /* Info/Running background */

.border-success-border      /* Success border */
.border-destructive-border  /* Error border */
.border-warning-border      /* Warning border */
.border-info-border         /* Info border */
```

**Migration:**

| Old Pattern | New Pattern |
|-------------|-------------|
| `text-green-600 dark:text-green-400` | `text-success` |
| `text-blue-600 dark:text-blue-400` | `text-info` |
| `bg-green-100 dark:bg-green-900/30` | `bg-success-bg` |
| `bg-blue-100 dark:bg-blue-900/30` | `bg-info-bg` |

### کلاس‌های Truncate

```tsx
<p className="truncate">Long connector name...</p>
<p className="line-clamp-2">Multiple lines description...</p>
```

### Transitions

```tsx
<div className="transition-colors" />
<div className="transition-all duration-200" />
<div className="transition-opacity" />
```

---

## نمونه استفاده کامل

### Connector Card

```tsx
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Database, CheckCircle, XCircle } from 'lucide-react'

function ConnectorCard({ connector, isSelected, onSelect }) {
  const { t } = useTranslation()

  return (
    <div
      onClick={() => onSelect(connector)}
      className={cn(
        'p-4 rounded-lg border cursor-pointer transition-all',
        isSelected
          ? 'border-primary bg-primary/5'
          : 'border-border hover:border-primary/50'
      )}
    >
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
          <Database className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-medium truncate">{connector.name}</h3>
          <p className="text-sm text-muted-foreground truncate">
            {connector.base_url}
          </p>
        </div>

        {connector.is_active ? (
          <Badge variant="default" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Active
          </Badge>
        ) : (
          <Badge variant="secondary" className="gap-1">
            <XCircle className="h-3 w-3" />
            Inactive
          </Badge>
        )}
      </div>
    </div>
  )
}
```

### Sync Run Status Badge

```tsx
// ✅ Updated to use semantic colors (Design System v2.1)
function SyncStatusBadge({ status }: { status: SyncStatus }) {
  if (status === 'running') {
    return (
      <Badge className="bg-info-bg text-info border border-info-border">
        <Loader2 className="h-3 w-3 animate-spin mr-1" />
        Running
      </Badge>
    )
  }

  if (status === 'success') {
    return (
      <Badge className="bg-success-bg text-success border border-success-border">
        <CheckCircle className="h-3 w-3 mr-1" />
        Success
      </Badge>
    )
  }

  if (status === 'pending') {
    return (
      <Badge className="bg-warning-bg text-warning border border-warning-border">
        <Clock className="h-3 w-3 mr-1" />
        Pending
      </Badge>
    )
  }

  return (
    <Badge className="bg-destructive-bg text-destructive border border-destructive-border">
      <XCircle className="h-3 w-3 mr-1" />
      Failed
    </Badge>
  )
}
```

---

## تسک‌های آینده

### کامپوننت‌های پیشنهادی برای ایجاد

1. **StatusBadge** - برای Connector status با hover test
2. **LatencyIndicator** - نمایش latency با رنگ‌بندی
3. **SyncProgressBar** - progress bar برای Sync Runs
4. **EntitySchemaViewer** - نمایش JSON schema ستون‌ها
5. **CronExpressionBuilder** - UI helper برای Cron expressions
6. **DataDiffViewer** - نمایش تغییرات در Failed Records

### بهبودهای Layout

1. Wizard pattern برای Connector/Entity creation
2. Split panel برای Sync Run details
3. Timeline view برای Sync history

---

*ایجاد شده: دسامبر 2025*
