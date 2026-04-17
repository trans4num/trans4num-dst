import { fetchSingleAlternative } from "@/lib/api/queries/fetch-single-alternative";
import { type Alternative } from "@/models/alternative";
import { useQuery } from "@tanstack/react-query";

export function useSingleAlternative(regionId: string, alternative_id: string) {
  const { data, isLoading, error } = useQuery<Alternative>({
    queryKey: ['alternatives', regionId, alternative_id],
    queryFn: () => {
      if (!regionId ||! alternative_id) {
        return Promise.reject(new Error('No region or alternative selected'));
      }
      return fetchSingleAlternative(regionId, alternative_id);
    },
    enabled: !!regionId && !!alternative_id, // Only fetch when id's are given 
  });

  return {
    alternative: data,
    isLoading,
    error,
  };
}