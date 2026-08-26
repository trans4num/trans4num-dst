import { deleteAlternative } from "@/lib/api/mutations/delete-alternative";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useRestoreAlternative(regionId: string) {
  const queryClient = useQueryClient();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: deleteAlternative,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['alternatives', regionId] });
    },
  });
  return {
    restoreAlternative: mutateAsync,
    isPending,
  };
}