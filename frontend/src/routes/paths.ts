/**
 * File overview
 * Purpose: Keep page-navigation URLs in one typed location.
 * Responsibilities: Export literal paths and the vehicle-details pattern with its seriale
 *   parameter for route matching and URL generation.
 * Connections: App registers these paths; Login, Dashboard, Fleet and VehicleDetails share
 *   navigation constants; Fleet uses generatePath to build each vehicle-details URL.
 */

// --- Route definitions: use these values for both declarations and navigation callbacks. ---
export const ROUTES={
    HOME:'/',
    LOGIN:'/login',
    DASHBOARD:'/dashboard',
    FLEET:'/vehicles',
    VEHICLE_DETAILS: '/vehicles/:seriale', //dynamic route: seriale identifies the vehicle selected from Fleet
} as const;// Preserve literal route types and readonly properties at compile time.
