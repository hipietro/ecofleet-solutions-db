/**
 * File overview
 * Purpose: Provide the frontend backend-server base URL.
 * Responsibilities: Use the public Vite environment override when set, otherwise fall back to the
 *   local API address.
 * Connections: Imported by Login, Dashboard and Fleet; backend/core/config.py separately manages
 *   server-side secrets.
 */

// --- Public API configuration: evaluate the Vite override or retain the local development fallback. ---
export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||'http://localhost:8000'
    // Vite exposes this configuration to the browser; an unset value uses the local fallback.
    // VITE_ variables are public browser configuration, not storage for passwords or JWT secrets.
