import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { frontendPorts } from "@tanim/config";

export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: frontendPorts.landing, strictPort: true },
});
