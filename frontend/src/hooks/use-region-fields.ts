import { useQuery } from "@tanstack/react-query"
import { fetchRegionFields } from "@/lib/api/queries/fetch-region-fields"

export function useRegionFields(regionId: string | undefined) {
  const { data, isLoading, error } = useQuery<GeoJSON.FeatureCollection<GeoJSON.Polygon, { id: string }>>({
    queryKey: ["region-fields", regionId],
    queryFn: () => fetchRegionFields(regionId!),
    enabled: !!regionId, // Only fetch if we have a regionId
  })

  return {
    fields: data,
    isLoading,
    error,
  }
}
