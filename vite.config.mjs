// Configuración de Vite: compila el código React de frontend/ para que Django lo sirva.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  root: "frontend",                 // Vite solo mira esta carpeta (no .venv, media, etc.)
  base: "/static/dist/",            // = STATIC_URL + "dist/": así coinciden las rutas con Django
  server: {
    port: 5173,
    strictPort: true,               // si el puerto está ocupado, falla en vez de cambiarlo
    origin: "http://localhost:5173",
  },
  build: {
    outDir: "../static/dist",       // el resultado acaba en static/dist (lo ignora git)
    emptyOutDir: true,
    manifest: "manifest.json",      // django-vite lee este índice para saber qué archivos cargar
    rollupOptions: {
      input: "src/tienda/main.jsx",
    },
  },
});
