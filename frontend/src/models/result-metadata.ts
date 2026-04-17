export type AlternativeResult = {
  alternative_id: string
  field_id: string
  status_quo: ResultMetadata
  alternative: ResultMetadata
}

export type ResultMetadata = {
    n_load: number
    nature: number
    n_load_per_ha: number
    economy: number
    farm_economy: number
    consistensy: number
}