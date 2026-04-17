"use client";

import type { Locale } from "@/i18n/config";
import { useState, useTransition } from "react";
import ReactCountryFlag from "react-country-flag";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSidebar } from "@/components/ui/sidebar";
import { useTranslations } from "next-intl";
import { useAppLocale } from "@/components/locale-provider";

type Props = {
  defaultValue: string;
  items: Array<{ value: string; label: string }>;
  label: string;
};

export default function LocaleSwitcherDropdown({
  defaultValue,
  items,
  label,
}: Props) {
  const t = useTranslations("LocaleSwitcher");
  const { setLocale } = useAppLocale();
  const [currentLocale, setCurrentLocale] = useState(defaultValue);
  const [, startTransition] = useTransition();
  const { open } = useSidebar();
  function handleSelect(value: string) {
    setCurrentLocale(value);
    startTransition(() => {
      setLocale(value as Locale);
    });
  }

  return (
    <Select value={currentLocale} onValueChange={handleSelect}>
      <SelectTrigger className="">
        <SelectValue placeholder="Language">
          <LanguageIcon language={currentLocale} className="mr-2" />
          {open && <span>{t(currentLocale)}</span>}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {items.map(({ value: itemValue, label }) => (
          <SelectItem key={itemValue} value={itemValue}>
            <LanguageIcon language={itemValue} className="mr-2" />
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
  
}

function LanguageIcon({
  language,
  className,
}: {
  language: string;
  className?: string;
}) {
  return (
    <span className="inline-block items-center ">
      <ReactCountryFlag
        countryCode={languageToCountry[language]}
        svg
        className="mr-2"
        aria-hidden="true"
        style={{
          width: "1.2em",
          height: "1.2em",
        }}
      />
    </span>
  );
}

const languageToCountry: Record<string, string> = {
  dk: "DK",
  en: "GB",
  de: "DE",
};
