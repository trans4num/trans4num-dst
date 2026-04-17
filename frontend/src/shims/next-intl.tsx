import { createContext, useContext } from "react";

type Messages = Record<string, string | Messages>;

type IntlContextValue = {
  locale: string;
  messages: Messages;
};

const IntlContext = createContext<IntlContextValue | undefined>(undefined);

const resolvePath = (messages: Messages, path: string) =>
  path.split(".").reduce<string | Messages | undefined>((value, part) => {
    if (typeof value !== "object" || value === null) {
      return undefined;
    }
    return value[part];
  }, messages);

const formatMessage = (
  template: string,
  values?: Record<string, string | number | null | undefined>,
) =>
  values
    ? template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? ""))
    : template;

export function NextIntlClientProvider({
  locale,
  messages,
  children,
}: {
  locale: string;
  messages: Messages;
  children: React.ReactNode;
}) {
  return <IntlContext.Provider value={{ locale, messages }}>{children}</IntlContext.Provider>;
}

export const useLocale = () => {
  const context = useContext(IntlContext);
  if (!context) {
    throw new Error("useLocale must be used within NextIntlClientProvider");
  }
  return context.locale;
};

export const useTranslations = (namespace?: string) => {
  const context = useContext(IntlContext);
  if (!context) {
    throw new Error("useTranslations must be used within NextIntlClientProvider");
  }

  return (key: string, values?: Record<string, string | number | null | undefined>) => {
    const fullKey = namespace ? `${namespace}.${key}` : key;
    const result = resolvePath(context.messages, fullKey);
    return typeof result === "string" ? formatMessage(result, values) : fullKey;
  };
};
