import { apiFetch } from "@/lib/api/client";

export async function deleteAlternative(id: string) {
    const response = await apiFetch(`/simulations/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ deleted: true }),
    });

    if(!response.ok) {
        throw new Error(`Failed to delete alternative: ${response.statusText}`);
    }
}