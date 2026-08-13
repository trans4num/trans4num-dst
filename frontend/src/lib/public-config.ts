export const PUBLIC_CONFIG = {
  apiBaseUrl:
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  mapStyle: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
} as const;
