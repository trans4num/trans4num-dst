import type { AlternativeFormValues } from "@/models/alternative";
import { apiFetch } from "@/lib/api/client";

export async function createAlternative(data: AlternativeFormValues) {
  const payload = {
    ...data,
  };

  const response = await apiFetch(`/simulations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to create alternative: ${response.statusText}`);
  }
}
