import { fetchAlternatives } from "@/lib/api/queries/fetch-alternatives";
import { type Alternative, type AlternativesWithStatusQuo } from "@/models/alternative";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

export function useAlternatives(regionId?: string, refetchInterval?: number) {
  const [selectedRow, setSelectedRow] = useState<Alternative | null>(null);
  const { data, isLoading, error } = useQuery<AlternativesWithStatusQuo>({
    queryKey: ['alternatives', regionId],
    queryFn: () => {
      if (!regionId) {
        return Promise.reject(new Error('No region selected'));
      }
      return fetchAlternatives(regionId);
    },
    enabled: !!regionId, // Only fetch when regionId is available
    refetchInterval: refetchInterval,
    retry: (failureCount, error) => {
      // Don't retry if the error is due to missing regionId
      if (error.message === 'No region selected') return false;
      // Retry other errors up to 3 times
      return failureCount < 3;
    },
  });

  return {
    alternatives: data?.alternatives,
    statusQuo: data?.statusQuo,
    isLoading,
    error,
    selectedRow,
    setSelectedRow,
  };
}