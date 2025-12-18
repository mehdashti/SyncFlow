import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Bell, Check, Info, AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
}

// Mock notifications - replace with actual API call
const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'success',
    title: 'Sync Completed',
    message: 'Customer data synced successfully from Salesforce',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    read: false,
  },
  {
    id: '2',
    type: 'warning',
    title: 'Connection Timeout',
    message: 'SAP connection timed out, retrying...',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    read: false,
  },
  {
    id: '3',
    type: 'error',
    title: 'Sync Failed',
    message: 'Unable to sync inventory data to NetSuite',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
  },
  {
    id: '4',
    type: 'info',
    title: 'New Flow Created',
    message: 'Order-to-Cash flow has been deployed',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
    read: true,
  },
]

const typeConfig = {
  info: {
    icon: Info,
    bgClass: 'bg-info-bg',
    textClass: 'text-info',
    borderClass: 'border-info-border',
  },
  success: {
    icon: CheckCircle2,
    bgClass: 'bg-success-bg',
    textClass: 'text-success',
    borderClass: 'border-success-border',
  },
  warning: {
    icon: AlertTriangle,
    bgClass: 'bg-warning-bg',
    textClass: 'text-warning',
    borderClass: 'border-warning-border',
  },
  error: {
    icon: AlertCircle,
    bgClass: 'bg-error-bg',
    textClass: 'text-error',
    borderClass: 'border-error-border',
  },
}

function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

export function NotificationBell() {
  const { t } = useTranslation()
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications)
  const [open, setOpen] = useState(false)

  const unreadCount = notifications.filter((n) => !n.read).length

  const markAllAsRead = () => {
    setNotifications((prev) =>
      prev.map((n) => ({ ...n, read: true }))
    )
  }

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-error text-[10px] font-medium text-white flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="end">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h3 className="font-semibold text-sm">
            {t('notifications.title', 'Notifications')}
          </h3>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto py-1 px-2 text-xs"
              onClick={markAllAsRead}
            >
              <Check className="h-3 w-3 ltr:mr-1 rtl:ml-1" />
              {t('notifications.markAllRead', 'Mark all read')}
            </Button>
          )}
        </div>

        {/* Notifications List */}
        <ScrollArea className="h-[300px]">
          {notifications.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              {t('notifications.empty', 'No notifications')}
            </div>
          ) : (
            <div className="divide-y divide-border">
              {notifications.map((notification) => {
                const config = typeConfig[notification.type]
                const Icon = config.icon
                return (
                  <button
                    key={notification.id}
                    className={cn(
                      'w-full px-4 py-3 text-left hover:bg-accent/50 transition-colors',
                      !notification.read && 'bg-accent/30'
                    )}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex gap-3">
                      <div
                        className={cn(
                          'shrink-0 h-8 w-8 rounded-[3px] flex items-center justify-center',
                          config.bgClass
                        )}
                      >
                        <Icon className={cn('h-4 w-4', config.textClass)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-medium truncate">
                            {notification.title}
                          </p>
                          {!notification.read && (
                            <span className="h-2 w-2 rounded-full bg-primary shrink-0" />
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatRelativeTime(notification.timestamp)}
                        </p>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-border">
          <Button variant="ghost" className="w-full text-sm" size="sm">
            {t('notifications.viewAll', 'View all notifications')}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
