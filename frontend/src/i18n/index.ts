import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import HttpBackend from 'i18next-http-backend'

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: ['en', 'fa', 'ar', 'tr'],
    debug: import.meta.env.DEV,

    interpolation: {
      escapeValue: false,
    },

    backend: {
      loadPath: import.meta.env.BASE_URL + 'locales/{{lng}}/translation.json',
    },

    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  })

export default i18n

// RTL languages
export const rtlLanguages = ['fa', 'ar']

export const isRtlLanguage = (lang: string) => rtlLanguages.includes(lang)

// Language config
export const languages = [
  { code: 'en', name: 'English', dir: 'ltr' },
  { code: 'fa', name: 'Persian', dir: 'rtl' },
  { code: 'ar', name: 'Arabic', dir: 'rtl' },
  { code: 'tr', name: 'Turkish', dir: 'ltr' },
] as const
