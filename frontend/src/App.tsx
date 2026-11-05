/**
 * File overview
 * Purpose: Define the client-side page routes for EcoFleet.
 * Responsibilities: Create BrowserRouter, redirect the home URL to login and map route constants
 *   to page components, including the dynamic vehicle-details route.
 * Connections: main.tsx renders App; routes/paths supplies URLs; Login, Dashboard, Fleet and
 *   VehicleDetails supply page content.
 */

// --- Imports and cross-module dependencies ---
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import { ROUTES } from './routes/paths'
import Fleet from './pages/Fleet'
import VehicleDetails from './pages/VehicleDetails'

// --- Application router: resolve browser URLs to the page components below. ---
function App() {
  return (
    <BrowserRouter>
      {/* Route matching: the home path redirects to login; the other constants select a page. */}
      <Routes>
        <Route
        path={ROUTES.HOME}// JSX braces pass the route constant as a JavaScript expression.
        element={<Navigate to={ROUTES.LOGIN} replace/>}
        />
        {/* Page routes: connect shared URL constants to the corresponding components. */}
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
        <Route path={ROUTES.FLEET} element={<Fleet />} />
        <Route path={ROUTES.VEHICLE_DETAILS} element={<VehicleDetails />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
