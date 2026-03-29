import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/hardware": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/vms": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/apps": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/storage": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/networks": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/misc": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/documents": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
      "/map": {
        target: "http://127.0.0.1:5001",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    // MapPage pulls in cytoscape (~500k+ minified); lazy-loaded, not in the main chunk.
    chunkSizeWarningLimit: 650,
  },
});
