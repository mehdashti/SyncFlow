import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/cn'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary-500 text-white',
        secondary: 'border-transparent bg-neutral-100 text-neutral-900 dark:bg-neutral-700 dark:text-neutral-100',
        destructive: 'border-transparent bg-error-500 text-white',
        outline: 'text-neutral-900 dark:text-neutral-100',
        success: 'border-transparent bg-success-100 text-success-700 dark:bg-success-700/20 dark:text-success-500',
        warning: 'border-transparent bg-warning-100 text-warning-700 dark:bg-warning-700/20 dark:text-warning-500',
        error: 'border-transparent bg-error-100 text-error-700 dark:bg-error-700/20 dark:text-error-500',
        info: 'border-transparent bg-info-100 text-info-700 dark:bg-info-700/20 dark:text-info-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
