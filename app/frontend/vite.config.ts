import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    base: "/", // Ensure assets are served from root
    build: {
        outDir: "dist", // Standard output directory for Docker
        emptyOutDir: true,
        sourcemap: true,
        // Optimize for production
        minify: true,
        rollupOptions: {
            output: {
                // Better chunking for caching
                manualChunks: {
                    vendor: ['react', 'react-dom'],
                    ui: ['@radix-ui/react-label', '@radix-ui/react-select', '@radix-ui/react-slider', '@radix-ui/react-slot'],
                    utils: ['clsx', 'class-variance-authority', 'tailwind-merge']
                }
            }
        }
    },
    resolve: {
        preserveSymlinks: true,
        alias: {
            "@": path.resolve(__dirname, "./src")
        }
    },
    server: {
        host: "0.0.0.0", // Allow external connections in development
        port: 5173,
        proxy: {
            "/ws": {
                target: "ws://localhost:8000", // Match your FastAPI backend
                ws: true,
                changeOrigin: true
            },
            "/api": {
                target: "http://localhost:8000", // For any API calls
                changeOrigin: true
            }
        }
    },
    preview: {
        host: "0.0.0.0",
        port: 4173
    }
});