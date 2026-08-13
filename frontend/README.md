# Trans4num DST Frontend

This frontend is a Vite + React + TypeScript single-page app built for static hosting on S3/CloudFront.

## Development

Run the local dev server:

```bash
npm run dev
```

Build the production bundle:

```bash
npm run build
```

Preview the built app locally:

```bash
npm run preview
```

The production output is written to `dist/`.

## Configuration

No local secrets or environment variables are required.

Public runtime values are defined in [src/lib/public-config.ts](./src/lib/public-config.ts).
The API URL can be set at build time with `VITE_API_BASE_URL`:

```ts
export const PUBLIC_CONFIG = {
  apiBaseUrl: "http://localhost:8000/api/v1",
  mapStyle: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
} as const;
```

If the backend base URL changes, set `VITE_API_BASE_URL` before building.

## Auth Model

- The browser calls `POST /login` on the backend API.
- The returned bearer token is stored in `sessionStorage`.
- Protected routes redirect to `/login` if the token is missing or expired.

## Routing

Client-side routing is handled with `react-router-dom`.
