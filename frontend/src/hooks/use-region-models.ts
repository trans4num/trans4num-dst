import { useQuery } from "@tanstack/react-query"
import { type RegionModels } from "@/models/region-models"
import { fetchRegionModels } from "@/lib/api/queries/fetch-region-models"

export function useRegionModels(regionId?: string) {
  const { data, isLoading, error } = useQuery<RegionModels>({
    queryKey: ["region-models", regionId],
    queryFn: () => fetchRegionModels(regionId!),
    enabled: !!regionId,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
    retry: 3, // Retry failed requests 3 times
  })

  return {
    regionModels: data,
    isLoading,
    error,
  }
}
