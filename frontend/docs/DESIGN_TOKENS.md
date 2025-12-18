# Design Tokens - SyncFlow

**Version: 2.1.0**
**Aligned with Enterprise Design System v2.1**

> Related Documentation:
> - [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
> - [FRONTEND_STANDARDS.md](./FRONTEND_STANDARDS.md) - Code standards
> - [COMPONENT_LIBRARY.md](./COMPONENT_LIBRARY.md) - UI components

---

## Brand Identity

### Design Philosophy

SyncFlow follows an **Industrial Petrol** design philosophy with:
- **Sharp corners** (3px max radius) for enterprise precision
- **Muted, professional colors** for reduced eye strain
- **Three-part semantic color system** for consistent status indicators
- **High contrast** in both light and dark modes

---

## Color System

### Primary Palette - Industrial Petrol

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--primary` | `#006D8F` (195 100% 28%) | `#35778C` (195 45% 38%) | Primary actions, links |
| `--primary-foreground` | `#FFFFFF` | `#FFFFFF` | Text on primary |

### Background & Foreground

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--background` | `#F8FAFC` (210 20% 98%) | `#0F172A` (220 30% 7%) | Page background |
| `--foreground` | `#334155` (215 25% 27%) | `#F1F5F9` (210 40% 96%) | Primary text |
| `--card` | `#FFFFFF` | `#1E293B` (220 25% 12%) | Card backgrounds |
| `--muted` | (210 40% 96%) | (220 25% 18%) | Subtle backgrounds |
| `--muted-foreground` | (215 16% 47%) | (215 20% 65%) | Secondary text |

### Semantic Colors - Three-Part System

Each semantic color has **three CSS variables**:

1. **Base** (`--success`) - For text and icons
2. **Background** (`--success-bg`) - For container backgrounds
3. **Border** (`--success-border`) - For borders

#### Success (Green)

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--success` | 142 76% 36% | 142 71% 45% |
| `--success-bg` | 142 76% 94% | 142 50% 15% |
| `--success-border` | 142 76% 70% | 142 50% 25% |

**Usage:**
```tsx
// Text
<span className="text-success">Sync completed</span>

// Container
<div className="bg-success-bg border border-success-border">
  <span className="text-success">Success message</span>
</div>
```

#### Warning (Amber)

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--warning` | 38 92% 50% | 38 92% 50% |
| `--warning-bg` | 48 96% 89% | 38 50% 15% |
| `--warning-border` | 38 92% 70% | 38 50% 30% |

**Usage:**
```tsx
<div className="bg-warning-bg border border-warning-border">
  <span className="text-warning">Warning message</span>
</div>
```

#### Info (Blue)

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--info` | 199 89% 48% | 199 89% 48% |
| `--info-bg` | 199 89% 94% | 199 50% 15% |
| `--info-border` | 199 70% 60% | 199 40% 30% |

**Usage:**
```tsx
<div className="bg-info-bg border border-info-border">
  <span className="text-info">Info message</span>
</div>
```

#### Destructive (Red)

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--destructive` | 0 84% 60% | 0 63% 31% |
| `--destructive-bg` | 0 84% 95% | 0 50% 15% |
| `--destructive-border` | 0 70% 70% | 0 40% 30% |

**Usage:**
```tsx
<div className="bg-destructive-bg border border-destructive-border">
  <span className="text-destructive">Error message</span>
</div>
```

### Color Migration Guide

| Old Pattern | New Pattern |
|-------------|-------------|
| `text-green-600` | `text-success` |
| `text-red-600` / `text-red-500` | `text-destructive` |
| `text-yellow-600` / `text-amber-600` | `text-warning` |
| `text-blue-600` | `text-info` |
| `bg-green-100` | `bg-success-bg` |
| `bg-red-100` / `bg-destructive/10` | `bg-destructive-bg` |
| `bg-yellow-100` / `bg-amber-100` | `bg-warning-bg` |
| `bg-blue-100` | `bg-info-bg` |
| `border-green-200` | `border-success-border` |
| `border-red-200` | `border-destructive-border` |

---

## Typography

### Font Families

| Direction | Font Stack |
|-----------|------------|
| LTR | `'Inter', 'Segoe UI', system-ui, sans-serif` |
| RTL | `'Vazirmatn', Tahoma, sans-serif` |

### Font Sizes

| Class | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `text-xs` | 0.75rem (12px) | 1rem | Labels, metadata |
| `text-sm` | 0.875rem (14px) | 1.25rem | Secondary text, table cells |
| `text-base` | 1rem (16px) | 1.5rem | Body text |
| `text-lg` | 1.125rem (18px) | 1.75rem | Subheadings |
| `text-xl` | 1.25rem (20px) | 1.75rem | Card titles |
| `text-2xl` | 1.5rem (24px) | 2rem | Page titles |

---

## Spacing

### Base Unit: 4px

| Token | Value | Usage |
|-------|-------|-------|
| `gap-1` / `p-1` | 4px | Minimal spacing |
| `gap-2` / `p-2` | 8px | Tight spacing |
| `gap-3` / `p-3` | 12px | Compact spacing |
| `gap-4` / `p-4` | 16px | Default spacing |
| `gap-6` / `p-6` | 24px | Section spacing |
| `gap-8` / `p-8` | 32px | Large spacing |

---

## Border Radius

### Enterprise Standard: 3px Maximum

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 2px | Small elements (Checkbox) |
| `--radius-md` | 3px | **Default** - Buttons, Inputs, Cards |
| `--radius-lg` | 4px | Overlays (Dialogs, Dropdowns) |
| `--radius-pill` | 9999px | Pills, Status dots |

### Usage in Code

```tsx
// Default - 3px
<Button className="rounded-[3px]">Action</Button>
<Card className="rounded-[3px]">Content</Card>

// Small - 2px
<Checkbox className="rounded-[2px]" />

// Full round - Pills only
<Badge className="rounded-full">Status</Badge>
```

### Migration

| Old | New |
|-----|-----|
| `rounded-md` (6px) | `rounded-[3px]` |
| `rounded-lg` (8px) | `rounded-[3px]` or `rounded-[4px]` for dialogs |
| `rounded-xl` (12px) | `rounded-[3px]` |

---

## Layout

### Fixed Dimensions

| Token | Value | Usage |
|-------|-------|-------|
| `--header-height` | 56px | Top header |
| `--sidebar-width` | 240px | Expanded sidebar |
| `--sidebar-collapsed` | 64px | Collapsed sidebar |

### Breakpoints

| Name | Width | Usage |
|------|-------|-------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Small desktop |
| `xl` | 1280px | Desktop |
| `2xl` | 1536px | Large desktop |

---

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Subtle elevation |
| `shadow` | `0 1px 3px 0 rgb(0 0 0 / 0.1)` | Cards |
| `shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | Dropdowns |
| `shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1)` | Modals |

---

## Component Tokens

### Sidebar

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--sidebar` | `#1E3A4C` (200 50% 20%) | `#0B131E` (210 40% 5%) |
| `--sidebar-foreground` | `#FFFFFF` | (210 40% 90%) |
| `--sidebar-accent` | (195 100% 28%) | (195 45% 38%) |

### Table

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `--table-stripe` | (210 20% 97%) | (220 25% 10%) |
| `--table-header` | (210 20% 95%) | (220 25% 15%) |

---

## Sync Status Colors

For SyncFlow's domain-specific statuses:

| Status | Text Class | Background Class | Border Class |
|--------|------------|------------------|--------------|
| Running | `text-info` | `bg-info-bg` | `border-info-border` |
| Success | `text-success` | `bg-success-bg` | `border-success-border` |
| Failed | `text-destructive` | `bg-destructive-bg` | `border-destructive-border` |
| Pending | `text-warning` | `bg-warning-bg` | `border-warning-border` |

### Example Implementation

```tsx
const syncStatusStyles = {
  running: {
    text: 'text-info',
    bg: 'bg-info-bg',
    border: 'border-info-border',
  },
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
  pending: {
    text: 'text-warning',
    bg: 'bg-warning-bg',
    border: 'border-warning-border',
  },
}
```

---

## Animations

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| `fadeIn` | 200ms | ease-out | Content appearance |
| `slideInUp` | 200ms | ease-out | Toasts, tooltips |
| `slideInRight` | 300ms | ease-out | Panels |
| `slideInLeft` | 300ms | ease-out | RTL panels |

---

*Created: December 2025*
*Aligned with Enterprise Design System v2.1*
