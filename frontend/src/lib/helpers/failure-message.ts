import type { Alternative } from "@/models/alternative"

type Translate = (key: string, values?: Record<string, string | number>) => string

const constraintNames: Record<string, { label: string; unit: string }> = {
  "N-Load Change": { label: "nitrogen", unit: "kg N" },
  "Economy Change": { label: "economy", unit: "DKK" },
  "Single Farmer Impact": { label: "farmIncome", unit: "DKK" },
  "Area Change": { label: "area", unit: "ha" },
  "Fields Change": { label: "fields", unit: "fields" },
  "Percentage of farm type change": { label: "farmType", unit: "fields" },
}

/** Present persisted engine diagnostics without changing the original record. */
export function formatFailureMessage(alternative: Alternative, locale: string, t: Translate) {
  const raw = alternative.errorMessage
  if (!raw) return null
  const number = (value: number, decimals = 0) => new Intl.NumberFormat(
    locale === "dk" ? "da-DK" : locale,
    { maximumFractionDigits: decimals },
  ).format(value)
  const match = raw.match(/^(.+?) cannot be satisfied: attainable range \[([^,]+),\s*([^\]]+)\], required at (most|least) (.+)$/)
  if (match) {
    const [, scopedName, low, high, comparison, target] = match
    const name = scopedName.replace(/ for .+$/, "")
    const minimum = Number(low), maximum = Number(high), limit = Number(target)
    if ([minimum, maximum, limit].every(Number.isFinite)) {
      const rule = [...(alternative.model?.goal.configuration ?? []), ...(alternative.model?.constraints ?? [])]
        .find(configuration => configuration.name === name && configuration.enabled)
      if (name === "N-Load Change" && comparison === "most" && limit < 0 && rule && rule.value < 0) {
        const requestedPercent = Math.abs(rule.value)
        const maximumReduction = Math.max(0, -minimum)
        const maximumPercent = requestedPercent * maximumReduction / Math.abs(limit)
        return {
          message: t("Optimization.failures.nitrogenReduction", {
            requestedPercent: number(requestedPercent, 1),
            requestedReduction: number(Math.abs(limit)),
            maximumPercent: number(maximumPercent, 1),
            maximumReduction: number(maximumReduction),
          }),
          technicalDetails: raw,
        }
      }
      const known = constraintNames[name]
      const label = known ? t(`Optimization.failures.constraints.${known.label}`) : name
      const unit = known?.unit === "fields" ? t("Optimization.failures.fieldsUnit") : known?.unit ?? ""
      return {
        message: t(comparison === "most" ? "Optimization.failures.maximumLimit" : "Optimization.failures.minimumLimit", {
          constraint: label,
          bestCase: number(comparison === "most" ? minimum : maximum, known?.unit === "ha" ? 2 : 0),
          limit: number(limit, known?.unit === "ha" ? 2 : 0),
          unit,
        }),
        technicalDetails: raw,
      }
    }
  }
  const reason = alternative.optimization?.terminationReason
  if (reason === "time_limit_no_solution" || reason === "no_solution") {
    return { message: t("Optimization.failures.timeout"), technicalDetails: raw }
  }
  if (reason === "infeasible" && raw === "No feasible solution exists.") {
    return { message: t("Optimization.failures.infeasible"), technicalDetails: raw }
  }
  return { message: raw }
}
