import { type Region } from "@/models/region"
import * as turf from "@turf/turf";
import { apiFetch } from "@/lib/api/client";
interface RegionsResponse {
    regions: Array<{
      id: string
      name: string
      area: GeoJSON.Polygon
    }>
  }


export async function fetchRegions(): Promise<Region[]> {
    const response = await apiFetch(`/regions`)

    if (!response.ok) {
      throw new Error(`Failed to fetch regions: ${response.statusText}`)
    }
    
    const data: RegionsResponse = await response.json()
    
    return data.regions.map(region => ({
      id: region.id,
      name: region.name,
      area: {
        type: "Polygon",
        coordinates: region.area.coordinates.filter((coord): coord is number[][] => 
          coord.every(point => point.every(val => val !== null))
        )
      },
      initialViewState: calculateInitialViewState(region.area),
      fields: {
        type: "FeatureCollection",
        features: [] 
      }
    }))
  }


function calculateInitialViewState(area: GeoJSON.Polygon) {
  const center = turf.center(area);
  const initialViewState = {
    latitude: center.geometry.coordinates[1],
    longitude: center.geometry.coordinates[0],
    zoom: 8
  };
  return initialViewState;
}
