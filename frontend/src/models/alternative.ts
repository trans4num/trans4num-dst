import { z } from "zod"

export type AlternativesWithStatusQuo = {
  statusQuo: Alternative,
  alternatives: Alternative[]
}

export type Alternative = {
  id: string
  name: string
  regionId: string
  status: "pending" | "success" | "failed" | "processing" | "nonOptimal"
  model?: AlternativeModel
  summary?: AlternativeResultSummary
  charts?: AlternativeChart[]
  barCharts?: AlternativeBarChart[]
  created: string
}

export type AlternativeChart = {
  name: string
  values: Record<string, number>
}

export type AlternativeBarChart = {
  chartName: string
  unit: string
  chartData: BarchartData[]
}

export type BarchartData = {
  name: string
  values: Record<string, number>
}

export type AlternativeModel = {
    constraints: AlternativeConstraint[]
    goal: AlternativeGoal
}
export type AlternativeGoal = {
    name: string
    description: string
    type: string
    configuration: AlternativeConfiguration[]
}

export type AlternativeConfiguration = {
  name: string
  enabled: boolean
  value: number
  range: {
    min: number | null
    max: number | null
  }
  unit: string
}

export type AlternativeConstraint = {
  name: string
  enabled: boolean
  value: number
  range: {
    min: number | null
    max: number | null
  }
  unit: string
}

export type AlternativeResultSummary = AlternativeResultSummaryEntry[]
export type AlternativeResultSummaryEntry = { name: string, value: number, unit: string }

export const alternativeFormSchema = z.object({
  name: z.string().min(2),
  regionId: z.string(),
  model: z.object({
    goal: z.object({
      name: z.string(),
      description: z.string(),
      type: z.string(),
      configuration: z.array(z.object({
        name: z.string(),
        enabled: z.boolean(),
        value: z.number(),
        range: z.array(z.number()).length(2),
        unit: z.string(),
      })),
    }),
    constraints: z.array(z.object({
      name: z.string(),
      enabled: z.boolean(),
      value: z.number(),
      range: z.array(z.number()).length(2),
      unit: z.string(),
    })),
  }),
})

export type AlternativeFormValues = z.infer<typeof alternativeFormSchema>

