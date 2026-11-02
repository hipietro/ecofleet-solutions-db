/**
 * File overview
 * Purpose: Provide the PostCSS configuration discovered by frontend tooling.
 * Responsibilities: Keep the PostCSS plugin list empty; Tailwind is integrated through the Vite
 *   plugin instead.
 * Connections: Read alongside vite.config.ts; it does not add a second Tailwind processing
 *   pipeline.
 */

export default {
  // --- PostCSS plugin registry: intentionally empty because Tailwind runs through its Vite integration. ---
  plugins: {},
}
