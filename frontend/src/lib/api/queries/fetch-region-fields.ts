import { apiFetch } from "@/lib/api/client";

export async function fetchRegionFields(regionId: string): Promise<GeoJSON.FeatureCollection<GeoJSON.Polygon, { id: string }>> {
  const response = await apiFetch(`/fields/geometries?region=${regionId}`, {
    headers: {
      "Accept-Encoding": "gzip",
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch fields for region ${regionId}: ${response.statusText}`)
  }

  const data: GeoJSON.FeatureCollection<GeoJSON.Polygon, { id: string }> = await response.json()
  return data
}
