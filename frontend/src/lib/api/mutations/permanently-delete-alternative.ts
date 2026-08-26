import { apiFetch } from "@/lib/api/client";

export async function permanentlyDeleteAlternative(id: string) {
    const response = await apiFetch(`/simulations/${id}`, {
        method: "DELETE",
    });

    if(!response.ok) {
        throw new Error(`Failed to permanently delete alternative: ${response.statusText}`);
    }
}