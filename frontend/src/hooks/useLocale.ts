import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '@/store'
import { isRtlLanguage } from '@/i18n'

export function useLocale() {
  const { locale, setLocale } = useUIStore()
  const { i18n } = useTranslation()

  useEffect(() => {
    // Change i18n language
    i18n.changeLanguage(locale)

    // Set document direction
    const isRtl = isRtlLanguage(locale)
    document.documentElement.dir = isRtl ? 'rtl' : 'ltr'
    document.documentElement.lang = locale
  }, [locale, i18n])

  return { locale, setLocale, isRtl: isRtlLanguage(locale) }
}
