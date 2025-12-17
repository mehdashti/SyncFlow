import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import i18n, { getLanguageDir, type LanguageCode } from '@/lib/i18n'

interface LocaleState {
  locale: LanguageCode
  setLocale: (locale: LanguageCode) => void
}

function applyLocale(locale: LanguageCode) {
  const dir = getLanguageDir(locale)
  document.documentElement.setAttribute('dir', dir)
  document.documentElement.setAttribute('lang', locale)
  i18n.changeLanguage(locale)
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set) => ({
      locale: 'en',
      setLocale: (locale) => {
        applyLocale(locale)
        set({ locale })
      },
    }),
    {
      name: 'syncflow-locale',
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyLocale(state.locale)
        }
      },
    }
  )
)
