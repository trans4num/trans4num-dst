import { createAlternative } from "@/lib/api/mutations/create-alternative";
import { useMutation } from "@tanstack/react-query";
import { useQueryClient } from "@tanstack/react-query";

export function useCreateAlternative(regionId: string) {
  const queryClient = useQueryClient();
  const { mutateAsync, isPending } = useMutation({
    mutationFn: createAlternative,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['alternatives', regionId] });
    },
  });
  return {
    createAlternative: mutateAsync,
    isPending,
  };
}