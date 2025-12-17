import { Globe } from 'lucide-react'
import { useLocaleStore } from '@/store'
import { SUPPORTED_LANGUAGES, type LanguageCode } from '@/lib/i18n'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export function LanguageSwitcher() {
  const { locale, setLocale } = useLocaleStore()

  return (
    <Select value={locale} onValueChange={(value) => setLocale(value as LanguageCode)}>
      <SelectTrigger className="w-[100px]">
        <Globe className="h-4 w-4 mr-2" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {SUPPORTED_LANGUAGES.map((lang) => (
          <SelectItem key={lang.code} value={lang.code}>
            {lang.code.toUpperCase()}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
