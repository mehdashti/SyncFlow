'use client'

import { Toaster as Sonner } from 'sonner'

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-white group-[.toaster]:text-neutral-900 group-[.toaster]:border-neutral-200 group-[.toaster]:shadow-lg dark:group-[.toaster]:bg-neutral-800 dark:group-[.toaster]:text-neutral-100 dark:group-[.toaster]:border-neutral-700',
          description: 'group-[.toast]:text-neutral-500 dark:group-[.toast]:text-neutral-400',
          actionButton:
            'group-[.toast]:bg-primary-500 group-[.toast]:text-white',
          cancelButton:
            'group-[.toast]:bg-neutral-100 group-[.toast]:text-neutral-500 dark:group-[.toast]:bg-neutral-700 dark:group-[.toast]:text-neutral-400',
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
