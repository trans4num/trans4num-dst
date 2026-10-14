"use client"

import { NextIntlClientProvider } from "next-intl"
import { createContext, useContext, useEffect, useMemo, useState } from "react"

import { defaultLocale, locales, type Locale } from "@/i18n/config"
import deMessages from "@/messages/de.json"
import dkMessages from "@/messages/dk.json"
import enMessages from "@/messages/en.json"
import deOptimization from "../../messages/de.json"
import dkOptimization from "../../messages/dk.json"
import enOptimization from "../../messages/en.json"

const LOCALE_STORAGE_KEY = "trans4num-locale"

const messagesByLocale = {
  // Optimization messages have one shared source. Preserve the app catalogs'
  // other translations, including their delete/restore and tooltip content.
  de: { ...deMessages, HomePage: { ...deMessages.HomePage, Optimization: deOptimization.HomePage.Optimization } },
  dk: { ...dkMessages, HomePage: { ...dkMessages.HomePage, Optimization: dkOptimization.HomePage.Optimization } },
  en: { ...enMessages, HomePage: { ...enMessages.HomePage, Optimization: enOptimization.HomePage.Optimization } },
} as const

type LocaleContextValue = {
  locale: Locale
  setLocale: (locale: Locale) => void
}

const LocaleContext = createContext<LocaleContextValue | undefined>(undefined)

const detectBrowserLocale = (): Locale => {
  if (typeof window === "undefined") {
    return defaultLocale
  }

  const storedLocale = window.localStorage.getItem(LOCALE_STORAGE_KEY)

  if (storedLocale && locales.includes(storedLocale as Locale)) {
    return storedLocale as Locale
  }

  const browserLocale = window.navigator.language.slice(0, 2).toLowerCase()

  if (locales.includes(browserLocale as Locale)) {
    return browserLocale as Locale
  }

  return defaultLocale
}

export const LocaleProvider = ({ children }: { children: React.ReactNode }) => {
  const [locale, setLocale] = useState<Locale>(defaultLocale)

  useEffect(() => {
    setLocale(detectBrowserLocale())
  }, [])

  useEffect(() => {
    document.documentElement.lang = locale
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  }, [locale])

  const value = useMemo<LocaleContextValue>(
    () => ({
      locale,
      setLocale,
    }),
    [locale],
  )

  return (
    <LocaleContext.Provider value={value}>
      <NextIntlClientProvider locale={locale} messages={messagesByLocale[locale]}>
        {children}
      </NextIntlClientProvider>
    </LocaleContext.Provider>
  )
}

export const useAppLocale = () => {
  const context = useContext(LocaleContext)

  if (!context) {
    throw new Error("useAppLocale must be used within a LocaleProvider")
  }

  return context
}
