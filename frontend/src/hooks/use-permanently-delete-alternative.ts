import { deleteAlternative } from "@/lib/api/mutations/delete-alternative";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function usePermanentlyDeleteAlternative(regionId: string) {
  const queryClient = useQueryClient();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: deleteAlternative,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['alternatives', regionId] });
    },
  });
  return {
    permanentlyDeleteAlternative: mutateAsync,
    isPending,
  };
}