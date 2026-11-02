/**
 * File overview
 * Purpose: Retain the project Tailwind configuration file.
 * Responsibilities: List template locations and keep theme extensions and extra plugins empty.
 * Connections: The active Tailwind v4 integration is configured in vite.config.ts and
 *   src/index.css; this file is not explicitly loaded with @config.
 */

/**@type {import('tailwindcss').Config} */
export default{
    // --- Template locations retained from the Tailwind configuration scaffold. ---
    content:[
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    // --- Theme customization section: no project-specific extension is currently declared. ---
    theme:{
        extend:{},
    },
    // --- Additional Tailwind plugins: none are configured in this retained file. ---
    plugins:[],
}
