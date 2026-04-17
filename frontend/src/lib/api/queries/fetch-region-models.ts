import { type RegionModels as RegionModels } from "@/models/region-models";
import { apiFetch } from "@/lib/api/client";

export async function fetchRegionModels(regionId: string): Promise<RegionModels> {
    const response = await apiFetch(`/regions/${regionId}/models`)

    if (!response.ok) {
      throw new Error(`Failed to fetch regions: ${response.statusText}`)
    }

    const data: RegionModels = await response.json()

    return data
  }
