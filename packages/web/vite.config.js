import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const backend = "http://127.0.0.1:8081";

export default defineConfig({
  plugins: [tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": backend,
      "/health.json": backend,
      "/invite/request": {
        target: backend,
        bypass(req) {
          if (req.url.split("?")[0] !== "/invite/request") return req.url;
        },
      },
      "/invite/redeem": {
        target: backend,
        bypass(req) {
          if (req.method === "GET") return "/index.html";
        },
      },
    },
  },
});
