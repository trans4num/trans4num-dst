import { useQuery } from "@tanstack/react-query"
import { type Region } from "@/models/region"
import { fetchRegions } from "@/lib/api/queries/fetch-regions"
import { useRegionFields } from "@/hooks/use-region-fields"

export function useRegions() {
  const { data, isLoading, error } = useQuery<Region[]>({
    queryKey: ["regions"],
    queryFn: fetchRegions,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
    retry: 3, // Retry failed requests 3 times
  })

  return {
    regions: data,
    isLoading,
    error,
  }
}

export function useRegion(id: string) {
  const { regions, isLoading: regionsLoading, error: regionsError } = useRegions()
  const region = regions?.find(r => r.id === id)
  
  const { 
    fields, 
    isLoading: fieldsLoading, 
    error: fieldsError 
  } = useRegionFields(region?.id)

  // Merge the fields data into the region object if available
  const enrichedRegion = region && fields ? {
    ...region,
    fields,
  } : region

  return {
    region: enrichedRegion,
    isLoading: regionsLoading || fieldsLoading,
    error: regionsError || fieldsError,
  }
}