/**
 * File overview
 * Purpose: Mount the React application in the HTML root element.
 * Responsibilities: Load global Tailwind styles and render App inside development StrictMode.
 * Connections: frontend/index.html loads this entry point; App defines navigation and index.css
 *   supplies global styles.
 */

// --- Imports and cross-module dependencies ---
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// --- React bootstrap: #root is supplied by index.html; StrictMode checks effect cleanup in development. ---
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
