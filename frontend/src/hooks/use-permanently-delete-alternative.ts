import { permanentlyDeleteAlternative } from "@/lib/api/mutations/permanently-delete-alternative";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function usePermanentlyDeleteAlternative(regionId: string) {
  const queryClient = useQueryClient();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: permanentlyDeleteAlternative,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['alternatives', regionId] });
    },
  });
  return {
    permanentlyDeleteAlternative: mutateAsync,
    isPending,
  };
}
