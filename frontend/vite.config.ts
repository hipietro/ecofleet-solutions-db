/**
 * File overview
 * Purpose: Configure the frontend development server and production bundler.
 * Responsibilities: Enable React transformation and the Tailwind CSS Vite integration.
 * Connections: npm scripts in package.json invoke Vite; index.html and src/main.tsx are the
 *   application entry points.
 */

// --- Imports and cross-module dependencies ---
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// --- Build pipeline: React handles TSX and Tailwind generates the utility styles used by pages. ---
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
