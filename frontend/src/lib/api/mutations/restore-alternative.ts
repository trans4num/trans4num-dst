import { apiFetch } from "@/lib/api/client";

export async function restoreAlternative(id: string) {
    const response = await apiFetch(`/simulations/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ deleted: false }),
    });

    if(!response.ok) {
        throw new Error(`Failed to restore alternative: ${response.statusText}`);
    }
}