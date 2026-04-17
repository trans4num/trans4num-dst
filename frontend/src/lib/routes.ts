export const buildAlternativesRoute = (regionId: string) =>
  `/region/alternatives/?regionId=${encodeURIComponent(regionId)}`;

export const buildCreateAlternativeRoute = (regionId: string) =>
  `/region/create-alternative/?regionId=${encodeURIComponent(regionId)}`;

export const buildAlternativeRoute = (regionId: string, id: string) =>
  `/region/alternative/?regionId=${encodeURIComponent(regionId)}&id=${encodeURIComponent(id)}`;
