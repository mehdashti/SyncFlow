# Application Shell Standards

**Version: 1.0.0**
**Based on: SAP Fiori, Microsoft Dynamics 365, Oracle Fusion, IFS Cloud**

> Related Documentation:
> - [DESIGN_TOKENS.md](./DESIGN_TOKENS.md) - Design tokens & color system
> - [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
> - [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) - UI components

---

## Overview

The Application Shell is the fixed skeleton of the entire application, providing consistent navigation, layout structure, and user experience across all pages.

### Reference Systems

| System | Vendor | Key Features |
|--------|--------|--------------|
| [SAP Fiori](https://experience.sap.com/fiori-design-web/shell-bar/) | SAP | Shell Bar, Floorplans, Dynamic Page |
| [Dynamics 365](https://learn.microsoft.com/en-us/dynamics365/customerengagement/on-premises/basics/find-your-way-around-dynamics-365-customer-engagement-enterprise) | Microsoft | Unified Interface, Office 365 aligned |
| [Oracle Fusion](https://docs.oracle.com/cd/E15586_01/fusionapps.1111/e15524/ui_impl_uishell.htm) | Oracle | UI Shell with 4 areas, Dynamic Tabs |
| [IFS Cloud](https://docs.ifs.com/ifsclouddocs/24r1/OnlineDoc/NavigationInIFSOnlineDocNew.htm) | IFS | Aurena framework, Slide-out Navigator |

---

## Shell Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SHELL BAR (Global Header)                         │
│  [≡] [Logo] App Name              [🔍 Search] [❓] [🔔 3] [🌐] [👤]      │
├────────┬────────────────────────────────────────────────────────────────┤
│        │                      PAGE HEADER                                │
│        │  📍 Home > Work Orders > WO-2024-001                           │
│  S     │  Work Order Details                    [Edit] [Delete] [More ▼]│
│  I     ├────────────────────────────────────────────────────────────────┤
│  D     │                                                                 │
│  E     │                      CONTENT AREA                               │
│  B     │                                                                 │
│  A     │   ┌─────────────────────────────────────────────────────────┐  │
│  R     │   │                                                         │  │
│        │   │              Page Content (Floorplan)                   │  │
│        │   │                                                         │  │
│        │   │   - List Report                                         │  │
│        │   │   - Master-Detail                                       │  │
│        │   │   - Object Page                                         │  │
│        │   │   - Dashboard                                           │  │
│        │   │                                                         │  │
│  [◄]   │   └─────────────────────────────────────────────────────────┘  │
└────────┴────────────────────────────────────────────────────────────────┘
```

---

## 1. Shell Bar (Global Header)

The topmost bar that remains constant across all pages.

### Specifications

| Property | Value | Notes |
|----------|-------|-------|
| Height | 56px | `--header-height: 56px` |
| Background | `--card` | Light: white, Dark: slate |
| Border | `--border` | 1px bottom border |
| Z-Index | 50 | Above all content |
| Position | Fixed | Stays at top on scroll |

### Layout Structure

```
┌──────────────────────────────────────────────────────────────────────┐
│ [≡] [Logo] App Name                    [🔍] [❓] [🔔 3] [🌐] [👤]    │
└──────────────────────────────────────────────────────────────────────┘
 ↑                ↑                              ↑
 Left Zone        Center/Title                   Right Zone (Actions)
```

### Components

#### Left Zone
| Component | Required | Description |
|-----------|----------|-------------|
| Menu Toggle | ✅ | Hamburger icon to collapse/expand sidebar |
| Logo | ✅ | Application logo (24-32px height) |
| App Name | ✅ | Application title |

#### Right Zone (ordered right-to-left)
| Component | Required | Icon | Description |
|-----------|----------|------|-------------|
| User Menu | ✅ | `User` / Avatar | Profile, settings, logout |
| Language | ✅ | `Globe` | Language switcher |
| Notifications | ✅ | `Bell` | Notification center with badge |
| Help | ⚠️ Optional | `HelpCircle` | Help/documentation |
| Theme | ✅ | `Sun`/`Moon` | Dark/light mode toggle |
| Search | ⚠️ Optional | `Search` | Global search (Cmd+K) |

### Implementation

```tsx
// components/shell/ShellBar.tsx
interface ShellBarProps {
  onMenuToggle: () => void
  sidebarCollapsed: boolean
}

export function ShellBar({ onMenuToggle, sidebarCollapsed }: ShellBarProps) {
  return (
    <header className="fixed top-0 left-0 right-0 h-[var(--header-height)]
                       border-b border-border bg-card z-50
                       flex items-center justify-between px-4">
      {/* Left Zone */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={onMenuToggle}>
          {sidebarCollapsed ? <PanelLeft /> : <PanelLeftClose />}
        </Button>
        <img src="/logo.svg" alt="Logo" className="h-7" />
        <span className="font-semibold text-foreground">{appName}</span>
      </div>

      {/* Right Zone */}
      <div className="flex items-center gap-1">
        <GlobalSearch />
        <ThemeToggle />
        <NotificationBell />
        <LanguageSwitcher />
        <UserMenu />
      </div>
    </header>
  )
}
```

---

## 2. Sidebar Navigation

Collapsible navigation panel on the left side.

### Specifications

| Property | Expanded | Collapsed |
|----------|----------|-----------|
| Width | 240px | 64px |
| CSS Variable | `--sidebar-width` | `--sidebar-collapsed` |
| Background | `--card` | `--card` |
| Border | 1px right | 1px right |
| Position | Fixed | Fixed |
| Top Offset | `--header-height` | `--header-height` |

### Navigation Item Structure

```tsx
interface NavItem {
  id: string
  path: string
  icon: LucideIcon
  labelKey: string        // i18n key
  badge?: number          // Optional count badge
  children?: NavItem[]    // For grouped items
}
```

### Navigation Groups

For applications with many items, group them logically:

```tsx
const navigationGroups = [
  {
    id: 'main',
    labelKey: null,  // No header for main items
    items: [
      { id: 'dashboard', path: '/', icon: Home, labelKey: 'nav.dashboard' },
    ]
  },
  {
    id: 'planning',
    labelKey: 'nav.planning',
    items: [
      { id: 'work-orders', path: '/work-orders', icon: ClipboardList, labelKey: 'nav.workOrders' },
      { id: 'scheduling', path: '/scheduling', icon: Calendar, labelKey: 'nav.scheduling' },
    ]
  },
  {
    id: 'master-data',
    labelKey: 'nav.masterData',
    items: [
      { id: 'materials', path: '/materials', icon: Package, labelKey: 'nav.materials' },
      // ...
    ]
  }
]
```

### Collapsed State Behavior

When collapsed:
- Show only icons (centered)
- Show tooltips on hover
- Hide group labels
- Expand on hover (optional)

### Implementation

```tsx
// components/layout/Sidebar.tsx
export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside className={cn(
      'fixed top-[var(--header-height)] left-0',
      'h-[calc(100vh-var(--header-height))]',
      'bg-card border-r border-border',
      'transition-all duration-300 z-40',
      collapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
    )}>
      <nav className="flex flex-col h-full p-2">
        <div className="flex-1 space-y-1 overflow-y-auto">
          {/* Navigation Items */}
        </div>

        {/* Collapse Toggle at Bottom */}
        <Button variant="ghost" size="sm" onClick={onToggle}>
          {collapsed ? <ChevronRight /> : <ChevronLeft />}
        </Button>
      </nav>
    </aside>
  )
}
```

---

## 3. Page Header

Context-specific header for each page, below the Shell Bar.

### Specifications

| Property | Value |
|----------|-------|
| Height | Auto (typically 48-64px) |
| Background | Transparent or `--background` |
| Padding | 24px horizontal, 16px vertical |
| Border | Optional 1px bottom |

### Components

```
┌──────────────────────────────────────────────────────────────────────┐
│ 📍 Home > Section > Current Page                                      │
│ Page Title                                     [Action1] [Action2] ▼  │
│ Optional subtitle or description                                      │
└──────────────────────────────────────────────────────────────────────┘
```

| Component | Required | Description |
|-----------|----------|-------------|
| Breadcrumb | ✅ | Navigation path with clickable links |
| Page Title | ✅ | Current page title (h1) |
| Subtitle | ⚠️ Optional | Additional context |
| Actions | ⚠️ Optional | Page-level action buttons |

### Implementation

```tsx
// components/shell/PageHeader.tsx
interface PageHeaderProps {
  title: string
  subtitle?: string
  breadcrumbs: { label: string; href?: string }[]
  actions?: React.ReactNode
}

export function PageHeader({ title, subtitle, breadcrumbs, actions }: PageHeaderProps) {
  return (
    <div className="px-6 py-4 border-b border-border bg-background">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
        {breadcrumbs.map((crumb, index) => (
          <Fragment key={index}>
            {index > 0 && <ChevronRight className="h-4 w-4" />}
            {crumb.href ? (
              <Link to={crumb.href} className="hover:text-foreground">
                {crumb.label}
              </Link>
            ) : (
              <span className="text-foreground">{crumb.label}</span>
            )}
          </Fragment>
        ))}
      </nav>

      {/* Title Row */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  )
}
```

---

## 4. Content Area Layouts (Floorplans)

### 4.1 List Report Layout

For displaying and filtering large data sets.

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Filter: Status ▼] [Filter: Date ▼] [More Filters]     🔍 Search    │
├─────────────────────────────────────────────────────────────────────┤
│ □ │ Code      │ Name           │ Status    │ Date       │ Actions  │
├───┼───────────┼────────────────┼───────────┼────────────┼──────────┤
│ □ │ WO-001    │ Work Order 1   │ ● Active  │ 2024-01-15 │ ⋮        │
│ □ │ WO-002    │ Work Order 2   │ ○ Draft   │ 2024-01-14 │ ⋮        │
│ □ │ WO-003    │ Work Order 3   │ ● Active  │ 2024-01-13 │ ⋮        │
├─────────────────────────────────────────────────────────────────────┤
│ Showing 1-10 of 156                              [◀] [1] [2] [3] [▶] │
└─────────────────────────────────────────────────────────────────────┘
```

```tsx
// components/layouts/ListReportLayout.tsx
interface ListReportLayoutProps {
  filters?: React.ReactNode
  table: React.ReactNode
  pagination?: React.ReactNode
  bulkActions?: React.ReactNode
}
```

### 4.2 Master-Detail Layout

For list with inline detail panel.

```
┌──────────────────────┬─────────────────────────────────────────────┐
│ Master List          │ Detail Panel                                 │
│ ──────────────────── │ ──────────────────────────────────────────── │
│ 🔍 Search...         │ Work Order: WO-002                           │
│                      │                                              │
│   WO-001  ○ Draft    │ ┌─────────────────────────────────────────┐ │
│ ▶ WO-002  ● Active   │ │ [General] [Schedule] [Materials] [Logs] │ │
│   WO-003  ● Active   │ ├─────────────────────────────────────────┤ │
│   WO-004  ○ Draft    │ │ Status: Active                          │ │
│                      │ │ Priority: High                          │ │
│                      │ │ Due Date: 2024-01-20                    │ │
│                      │ │ Assigned: John Doe                      │ │
│                      │ └─────────────────────────────────────────┘ │
│                      │                                              │
│                      │ [Edit] [Delete] [Start]                      │
└──────────────────────┴─────────────────────────────────────────────┘
```

```tsx
// components/layouts/MasterDetailLayout.tsx
interface MasterDetailLayoutProps {
  masterList: React.ReactNode
  detailPanel: React.ReactNode
  masterWidth?: string  // default: '320px'
  showDetail?: boolean
}
```

### 4.3 Object Page Layout

For viewing/editing a single object.

```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ WO-2024-001                                           [Edit] ▼  │ │
│ │ Production Order for Widget Assembly                            │ │
│ │ ────────────────────────────────────────────────────────────── │ │
│ │ Status: ● Active    Priority: High    Due: Jan 20, 2024        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [General] [Schedule] [Materials] [Operations] [Logs]                │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ ## General Information                                              │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Description: Full widget assembly process                      │ │
│ │ Quantity: 500 units                                            │ │
│ │ Work Center: Assembly Line 1                                   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ## Related Materials                                                │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Material         │ Required │ Available │ Status               │ │
│ │ Widget Base      │ 500      │ 520       │ ✓ OK                 │ │
│ │ Widget Cover     │ 500      │ 480       │ ⚠ Low                │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

```tsx
// components/layouts/ObjectPageLayout.tsx
interface ObjectPageLayoutProps {
  header: {
    title: string
    subtitle?: string
    status?: React.ReactNode
    actions?: React.ReactNode
    attributes?: { label: string; value: string }[]
  }
  tabs: {
    id: string
    label: string
    content: React.ReactNode
  }[]
  defaultTab?: string
}
```

### 4.4 Dashboard Layout

For overview pages with multiple cards/widgets.

```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│ │ Active      │ │ Pending     │ │ Completed   │ │ Overdue     │    │
│ │    24       │ │    12       │ │   156       │ │     3       │    │
│ │ Work Orders │ │ Work Orders │ │ This Month  │ │ ⚠ Warning   │    │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                                     │
│ ┌───────────────────────────────────┐ ┌───────────────────────────┐ │
│ │ Recent Work Orders                │ │ Schedule Overview         │ │
│ │ ─────────────────────────────── │ │ ─────────────────────────│ │
│ │ WO-001 • Active • Jan 15        │ │      [Gantt Chart]        │ │
│ │ WO-002 • Draft • Jan 14         │ │                           │ │
│ │ WO-003 • Active • Jan 13        │ │                           │ │
│ └───────────────────────────────────┘ └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Notification System

### Notification Bell

```tsx
interface NotificationBellProps {
  count: number           // Unread count
  maxDisplay?: number     // Max number to show (default: 99)
}

// Display:
// count = 0   → No badge
// count = 5   → Badge shows "5"
// count = 150 → Badge shows "99+"
```

### Notification Types

| Type | Color | Icon | Usage |
|------|-------|------|-------|
| Info | `text-info` | `Info` | General information |
| Success | `text-success` | `CheckCircle` | Completed actions |
| Warning | `text-warning` | `AlertTriangle` | Attention needed |
| Error | `text-destructive` | `XCircle` | Errors/failures |

### Notification Panel

```tsx
interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
}
```

---

## 6. Global Search (Cmd+K)

### Features

- Keyboard shortcut: `Cmd+K` (Mac) / `Ctrl+K` (Windows)
- Search across: Pages, Work Orders, Materials, etc.
- Recent searches
- Quick actions

### Implementation

```tsx
// components/shell/GlobalSearch.tsx
// Using cmdk library or custom dialog

interface SearchResult {
  id: string
  type: 'page' | 'workOrder' | 'material' | 'action'
  title: string
  subtitle?: string
  icon?: LucideIcon
  href?: string
  action?: () => void
}
```

---

## 7. CSS Variables

Add these to `globals.css`:

```css
:root {
  /* Shell dimensions */
  --header-height: 56px;
  --sidebar-width: 240px;
  --sidebar-collapsed: 64px;
  --page-header-height: 80px;

  /* Content spacing */
  --content-padding: 24px;
  --section-gap: 24px;
}
```

---

## 8. Responsive Behavior

### Breakpoints

| Breakpoint | Sidebar | Shell Bar | Layout |
|------------|---------|-----------|--------|
| < 768px (Mobile) | Hidden/Overlay | Compact | Single column |
| 768-1024px (Tablet) | Collapsed | Full | Responsive |
| > 1024px (Desktop) | Expanded | Full | Full |

### Mobile Adaptations

- Sidebar becomes overlay drawer
- Shell bar may hide some actions
- Master-detail becomes stacked pages
- Breadcrumb may truncate

---

## 9. Accessibility

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Navigate between focusable elements |
| `Escape` | Close dialogs, collapse menus |
| `Enter` | Activate buttons, links |
| `Arrow Keys` | Navigate within menus |
| `Cmd+K` | Open global search |

### ARIA Labels

```tsx
<nav aria-label="Main navigation">
<button aria-expanded={!collapsed} aria-label="Toggle sidebar">
<div role="alert" aria-live="polite">  {/* For notifications */}
```

---

## 10. File Structure

```
src/
├── components/
│   ├── shell/
│   │   ├── AppShell.tsx           # Main shell wrapper
│   │   ├── ShellBar.tsx           # Global header
│   │   ├── PageHeader.tsx         # Page-level header
│   │   ├── GlobalSearch.tsx       # Cmd+K search
│   │   ├── NotificationBell.tsx   # Notification center
│   │   ├── UserMenu.tsx           # User dropdown
│   │   └── index.ts
│   │
│   ├── layout/
│   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   ├── ListReportLayout.tsx   # List + filter layout
│   │   ├── MasterDetailLayout.tsx # List + detail layout
│   │   ├── ObjectPageLayout.tsx   # Single object layout
│   │   ├── DashboardLayout.tsx    # Dashboard cards
│   │   └── index.ts
│   │
│   └── ui/
│       └── ...                    # shadcn/ui components
```

---

## Examples

### Basic Page with PageHeader

```tsx
function WorkOrdersPage() {
  return (
    <>
      <PageHeader
        title={t('workOrders.title')}
        breadcrumbs={[
          { label: t('nav.dashboard'), href: '/' },
          { label: t('nav.workOrders') }
        ]}
        actions={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            {t('workOrders.create')}
          </Button>
        }
      />
      <div className="p-6">
        {/* Page content */}
      </div>
    </>
  )
}
```

### Master-Detail Page

```tsx
function MaterialsPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  return (
    <>
      <PageHeader
        title={t('materials.title')}
        breadcrumbs={[
          { label: t('nav.dashboard'), href: '/' },
          { label: t('nav.masterData'), href: '/master-data' },
          { label: t('nav.materials') }
        ]}
      />
      <MasterDetailLayout
        masterList={<MaterialsList onSelect={setSelectedId} selected={selectedId} />}
        detailPanel={selectedId ? <MaterialDetail id={selectedId} /> : <EmptyState />}
        showDetail={!!selectedId}
      />
    </>
  )
}
```

---

*Created: December 2024*
*Based on SAP Fiori, Microsoft Dynamics 365, Oracle Fusion, IFS Cloud*
