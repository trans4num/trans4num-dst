import { fetchVariables } from "@/lib/api/queries/fetch-variables"
import { useQuery } from "@tanstack/react-query"



export function useFieldMetadata(type: string, alternativeId: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["result-variables", alternativeId, type],
    queryFn: () => fetchVariables(type, alternativeId),
    enabled: !! alternativeId && !! type, // Only fetch if ID and type are provided
  })

  return {
    metadata: data,
    isLoading,
    error,
  }
}
