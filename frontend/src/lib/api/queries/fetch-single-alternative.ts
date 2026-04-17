import { type Alternative } from "@/models/alternative"
import { fetchAlternatives } from "@/lib/api/queries/fetch-alternatives"

export async function fetchSingleAlternative(regionId: string, alternative_id:string): Promise<Alternative> {
    const data = await fetchAlternatives(regionId);
    const alternatives = data.alternatives;
    
    const alternative = alternatives.find((alt) => alt.id === alternative_id);
    if (!alternative) {
      throw new Error(`Alternative with ID ${alternative_id} not found for region ${regionId}.`);
    }
    return alternative;
  }
