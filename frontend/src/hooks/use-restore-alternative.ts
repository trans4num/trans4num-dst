import { restoreAlternative } from "@/lib/api/mutations/restore-alternative";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useRestoreAlternative(regionId: string) {
  const queryClient = useQueryClient();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: restoreAlternative,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['alternatives', regionId] });
    },
  });
  return {
    restoreAlternative: mutateAsync,
    isPending,
  };
}
