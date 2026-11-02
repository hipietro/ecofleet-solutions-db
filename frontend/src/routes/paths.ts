/**
 * File overview
 * Purpose: Keep page-navigation URLs in one typed location.
 * Responsibilities: Export literal route constants reused by route definitions, redirects and
 *   navigation callbacks.
 * Connections: App registers these paths; Login, Dashboard and Fleet navigate with the same
 *   constants.
 */

// --- Route definitions: use these values for both declarations and navigation callbacks. ---
export const ROUTES={
    HOME:'/',
    LOGIN:'/login',
    DASHBOARD:'/dashboard',
    FLEET:'/vehicles'
} as const;// Preserve literal route types and readonly properties at compile time.
