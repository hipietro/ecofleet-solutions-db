/**
 * File overview
 * Purpose: Display the authenticated customer rental history.
 * Responsibilities: Read the token, fetch personal rentals, handle expired sessions, render
 *   rental status, start/end timestamps, final costs and nested vehicle information, and expose
 *   logout and fleet navigation.
 * Connections: Uses config/api, routes/paths and types/fleet; calls the backend rentals router
 *   for customer history and current battery data, and links to Login and Fleet.
 */

// --- Imports and cross-module dependencies ---
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Rental } from '../types/fleet'
import {ROUTES} from '../routes/paths'
import { API_BASE_URL } from '../config/api'

// --- Page state and navigation: read the stored token and prepare the history request. ---
export default function Dashboard() {
  const navigate = useNavigate()
  const token = localStorage.getItem('token')

  const [rentals, setRentals] = useState<Rental[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  // --- History effect: react to token changes and load only the current customer rentals. ---
  useEffect(() => {
    // --- Missing-session branch: return to login before making a protected API request. ---
    if (!token) {
      navigate(ROUTES.LOGIN)
      return
    }

    const fetchRentals = async () => {
      try {
        // --- Authenticated request: send the stored bearer token to the rental-history endpoint. ---
        const response = await fetch(`${API_BASE_URL}/api/rentals/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })

        // --- Expired or rejected session: clear local credentials and return to login. ---
        if (response.status === 401) {
          localStorage.removeItem('token')
          navigate(ROUTES.LOGIN)
          return
        }

        if (!response.ok) {
          throw new Error('Impossibile recuperare i noleggi')
        }

        // --- Successful response: store the typed history for the JSX card list. ---
        const data: Rental[] = await response.json()
        setRentals(data)
      // --- Failure feedback: display an Error message and always finish the loading state. ---
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message)
        }
      } finally {
        setIsLoading(false)
      }
    }

    fetchRentals()
  }, [token, navigate])

  // --- Logout action: remove local credentials and navigate using the shared login path. ---
  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate(ROUTES.LOGIN)
  }

  // --- Render guard: hide protected page content while the missing-token redirect is scheduled. ---
  if (!token) return null

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      
      {/* Header: identify the application and invoke the token-clearing logout handler. */}
      <header className="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center sticky top-0 z-10">
        <h1 className="text-xl font-bold">EcoFleet</h1>
        <button 
          onClick={handleLogout}
          className="text-sm bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded-full transition-colors"
        >
          Esci
        </button>
      </header>

      {/* Rental-history content: request feedback, empty state and individual rental cards. */}
      <main className="flex-1 p-4 pb-24">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">I Miei Noleggi</h2>

        {/* Loading section: keep progress feedback visible while the history request is pending. */}
        {isLoading && (
          <div className="text-center py-8 text-slate-500">
            Caricamento noleggi in corso...
          </div>
        )}

        {/* Error section: display the request failure stored by the effect. */}
        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-xl mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Empty section: explain that the response contains no rental records. */}
        {!isLoading && !error && rentals.length === 0 && (
          <div className="bg-white p-6 rounded-2xl border-2 border-dashed border-slate-200 text-center text-slate-500">
            Nessun noleggio attivo al momento. <br/> Esplora la mappa per prenotare un veicolo!
          </div>
        )}

        {/* Rental cards: use the rental ID as the stable React key and render nested vehicle details. */}
        {!isLoading && rentals.map((rental) => (
          <div key={rental.codicenoleggio} className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 mb-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-bold text-slate-800">
                  {rental.veicolo_dettagli?.marca} {rental.veicolo_dettagli?.modello}
                </h3>
                <p className="text-sm text-slate-500">Targa: {rental.veicolo_dettagli?.targa ?? '—'}</p>
              </div>
              <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                rental.stato === 'attivo'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-slate-100 text-slate-600'
              }`}>
                {rental.stato.toUpperCase()}
              </span>
            </div>

            {/* Rental metadata: show full timestamps and distinguish final costs from active rentals */}
            <div className="mt-3 pt-3 border-t border-slate-100 pt-3 text-sm text-slate-600">
              <p>
                Inizio: {new Date(rental.dataorainizio).toLocaleString('it-IT')}
              </p>
              
              {/*completion timestamp: active rentals have no end date yet. */}
              {rental.dataorafine && (
                <p className='mt-1'>
                  Fine: {new Date(rental.dataorafine).toLocaleString('it-IT')}
                </p>
              )}

              {/*final price: preserve zero amounts and handle missing values explicitily */}
              <p className='mt-2 font-semibold text-slate-800'>
                Costo totale: {rental.costo_totale != null ? Number(rental.costo_totale).toLocaleString('it-IT', {style: 'currency', currency: 'EUR',})
                  :rental.stato==='attivo'
                  ?'Calcolato al termine del noleggio'
                  :'Non disponibile'
                }
              </p>

              {/* Current battery: this value describes the vehicle now, not its historical charge. */}
              <p className="mt-2 text-xs text-slate-500">
                Batteria attuale: {
                  rental.veicolo_dettagli?.livello_batteria != null
                    ? `${rental.veicolo_dettagli.livello_batteria}%`
                    : 'Non disponibile'
                }
              </p>
          
            </div>
          </div>
        ))}
      </main>

      {/* Bottom navigation: the Fleet button is active; the profile button is currently a placeholder. */}
      <nav className="fixed bottom-0 w-full bg-white border-t border-slate-200 p-3 pb-safe flex justify-around items-center shadow-[0_-2px_10px_rgba(0,0,0,0.05)] z-10">
        <button
          onClick={()=>navigate(ROUTES.FLEET)}
          className="flex flex-col items-center p-2 text-slate-400 hover:text-blue-600 transition-colors">
          <span className="text-2xl mb-1">🚙</span>
          <span className="text-[10px] font-semibold">Veicoli</span>
        </button>
        
        <button className="flex flex-col items-center p-2 text-blue-600">
          <span className="text-2xl mb-1">🚗</span>
          <span className="text-[10px] font-semibold">Noleggi</span>
        </button>
        
        <button className="flex flex-col items-center p-2 text-slate-400 hover:text-blue-600 transition-colors">
          <span className="text-2xl mb-1">👤</span>
          <span className="text-[10px] font-semibold">Profilo</span>
        </button>
      </nav>

    </div>
  )
}
