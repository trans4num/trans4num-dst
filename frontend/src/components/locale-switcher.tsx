import { useTranslations } from "next-intl"
import LocaleSwitcherToggle from "@/components/locale-switcher-select"
import { useAppLocale } from "@/components/locale-provider"

export default function LocaleSwitcher() {
  const t = useTranslations("LocaleSwitcher")
  const { locale } = useAppLocale()

  return (
    <LocaleSwitcherToggle
      defaultValue={locale}
      items={[
        {
          value: "en",
          label: t("en"),
        },
        {
          value: "de",
          label: t("de"),
        },
        {
            value: "dk",
            label: t("dk"),
          },
      ]}
      label={t("label")}
    />
  )
}
