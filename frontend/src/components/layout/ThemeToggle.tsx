import { Moon, Sun, Monitor } from 'lucide-react'
import { useThemeStore, type Theme } from '@/store'
import { Button } from '@/components/ui/button'

const themeIcons: Record<Theme, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
}

export function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()
  const Icon = themeIcons[theme]

  const cycleTheme = () => {
    const themes: Theme[] = ['light', 'dark', 'system']
    const currentIndex = themes.indexOf(theme)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }

  return (
    <Button variant="ghost" size="icon" onClick={cycleTheme} title={`Theme: ${theme}`}>
      <Icon className="h-5 w-5" />
    </Button>
  )
}
