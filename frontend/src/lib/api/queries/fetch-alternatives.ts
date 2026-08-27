import type {
  Alternative,
  AlternativeBarChart,
  AlternativesWithStatusQuo,
} from "@/models/alternative"
import { apiFetch } from "@/lib/api/client";
interface AlternativeResponse {
    statusQuo: SimulationResponse
    simulations: Array<SimulationResponse>
}

interface SimulationResponse {
  id: string
  name: string
  regionId: string
  model: {
    goal: {
      name: string
      description: string
      type: string
      configuration: [
        {
          name: string
          enabled: boolean
          value: number
          range: {
            min: number | null
            max: number | null
          }
          unit: string
        }
      ]
    }
    constraints: [
      {
        name: string
        enabled: boolean
        value: number
        range: {
          min: number | null
          max: number | null
        }
        unit: string
      }
    ]
  }
  created: string
  status: "success" | "processing" | "failed" | "nonOptimal"
  deleted?: boolean
  summary: Array<{
    name: string
    value: number
    unit: string
  }>
  charts: {
    name: string
    values: Record<string, number>
  }[]
  barCharts: {
    chartName: string
    unit: string
    chartData: {
      name: string
      values: Record<string, number>
    }[]
  }[]
}

export async function fetchAlternatives(regionId: string): Promise<AlternativesWithStatusQuo> {
    const response = await apiFetch(`/simulations?region=${regionId}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch alternatives for region ${regionId}: ${response.statusText}`)
    }
    const data: AlternativeResponse = await response.json()

    const statusQuo = createAlternative(data.statusQuo);
    const alternatives = data.simulations.map(createAlternative) as Alternative[];
    if (alternatives[0]) alternatives[0].deleted = true; // TEMP: kun til test af Deleted-tab UI, fjern før commit
    
    return {statusQuo, alternatives} as AlternativesWithStatusQuo;
  }

  function createAlternative(data: SimulationResponse): Alternative {
    return {
      id: data.id,
      name: data.name,
      regionId: data.regionId,
      status: data.status,
      summary: data.summary,
      charts: data.charts,
      barCharts: roundBarChartsNumberValues(data.barCharts),
      model: data.model,
      created: data.created,
      deleted: data.deleted ?? false,
    };
  }

  function roundRecordNumbersToTwoDecimals(
    record: Record<string, number>,
  ): Record<string, number> {
    return Object.fromEntries(
      Object.entries(record).map(([key, value]) => [
        key,
        Number(value.toFixed(2)),
      ]),
    )
  }
  
  function roundBarChartsNumberValues(
    barCharts: SimulationResponse["barCharts"] | undefined,
  ): AlternativeBarChart[] | undefined {
    return barCharts?.map((chart) => ({
      ...chart,
      chartData: chart.chartData.map((category) => ({
        ...category,
        values: roundRecordNumbersToTwoDecimals(category.values),
      })),
    }))
  }
