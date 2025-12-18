import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'
import {
  Search,
  Home,
  Workflow,
  Database,
  PlugZap,
  Activity,
  History,
  Settings,
  type LucideIcon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface SearchResult {
  id: string
  type: 'page' | 'flow' | 'connection' | 'action'
  title: string
  subtitle?: string
  icon: LucideIcon
  href?: string
  action?: () => void
}

const pageResults: SearchResult[] = [
  { id: 'dashboard', type: 'page', title: 'Dashboard', icon: Home, href: '/' },
  { id: 'flows', type: 'page', title: 'Flows', icon: Workflow, href: '/flows' },
  { id: 'connections', type: 'page', title: 'Connections', icon: PlugZap, href: '/connections' },
  { id: 'data-sources', type: 'page', title: 'Data Sources', icon: Database, href: '/data-sources' },
  { id: 'monitoring', type: 'page', title: 'Monitoring', icon: Activity, href: '/monitoring' },
  { id: 'history', type: 'page', title: 'Run History', icon: History, href: '/history' },
  { id: 'settings', type: 'page', title: 'Settings', icon: Settings, href: '/settings' },
]

export function GlobalSearch() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Filter results based on query
  const filteredResults = query.trim()
    ? pageResults.filter((result) =>
        result.title.toLowerCase().includes(query.toLowerCase())
      )
    : pageResults.slice(0, 5)

  // Keyboard shortcut: Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(true)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Handle navigation within results
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((i) => Math.min(i + 1, filteredResults.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((i) => Math.max(i - 1, 0))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        const selected = filteredResults[selectedIndex]
        if (selected) {
          handleSelect(selected)
        }
      }
    },
    [filteredResults, selectedIndex]
  )

  const handleSelect = (result: SearchResult) => {
    setOpen(false)
    setQuery('')
    setSelectedIndex(0)

    if (result.href) {
      navigate({ to: result.href })
    } else if (result.action) {
      result.action()
    }
  }

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen(true)}
        className="hidden md:flex"
      >
        <Search className="h-5 w-5" />
      </Button>

      <Button
        variant="outline"
        onClick={() => setOpen(true)}
        className="hidden lg:flex items-center gap-2 text-muted-foreground h-9 px-3"
      >
        <Search className="h-4 w-4" />
        <span className="text-sm">{t('common.search', 'Search')}...</span>
        <kbd className="pointer-events-none ml-2 inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="p-0 max-w-lg overflow-hidden">
          <div className="flex items-center border-b border-border px-3">
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('search.placeholder', 'Search flows, connections...')}
              className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
              autoFocus
            />
          </div>

          <div className="max-h-[300px] overflow-y-auto p-2">
            {filteredResults.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                {t('search.noResults', 'No results found')}
              </div>
            ) : (
              <div className="space-y-1">
                <p className="px-2 py-1 text-xs text-muted-foreground font-medium">
                  {t('search.pages', 'Pages')}
                </p>
                {filteredResults.map((result, index) => {
                  const Icon = result.icon
                  return (
                    <button
                      key={result.id}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2 rounded-[3px] text-left transition-colors',
                        index === selectedIndex
                          ? 'bg-accent text-accent-foreground'
                          : 'hover:bg-accent/50'
                      )}
                      onClick={() => handleSelect(result)}
                      onMouseEnter={() => setSelectedIndex(index)}
                    >
                      <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{result.title}</p>
                        {result.subtitle && (
                          <p className="text-xs text-muted-foreground truncate">
                            {result.subtitle}
                          </p>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between border-t border-border px-3 py-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span>↑↓ navigate</span>
              <span>↵ select</span>
              <span>esc close</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
