import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "next-intl": path.resolve(__dirname, "./src/shims/next-intl.tsx"),
      "next/navigation": path.resolve(__dirname, "./src/shims/next-navigation.ts"),
      "next/link": path.resolve(__dirname, "./src/shims/next-link.tsx"),
      "next/image": path.resolve(__dirname, "./src/shims/next-image.tsx"),
      "next/error": path.resolve(__dirname, "./src/shims/next-error.tsx"),
    },
  },
  build: {
    outDir: "dist",
  },
});
