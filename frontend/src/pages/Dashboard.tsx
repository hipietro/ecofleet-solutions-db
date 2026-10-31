import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Rental } from '../types/fleet'

export default function Dashboard() {
  const navigate = useNavigate()
  const token = localStorage.getItem('token')

  const [rentals, setRentals] = useState<Rental[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }

    const fetchRentals = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/rentals/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.status === 401) {
          localStorage.removeItem('token')
          navigate('/login')
          return
        }

        if (!response.ok) {
          throw new Error('Impossibile recuperare i noleggi')
        }

        const data: Rental[] = await response.json()
        setRentals(data)
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

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  if (!token) return null

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      
      {/* HEADER */}
      <header className="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center sticky top-0 z-10">
        <h1 className="text-xl font-bold">EcoFleet</h1>
        <button 
          onClick={handleLogout}
          className="text-sm bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded-full transition-colors"
        >
          Esci
        </button>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-1 p-4 pb-24">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">I Miei Noleggi</h2>

        {isLoading && (
          <div className="text-center py-8 text-slate-500">
            Caricamento noleggi in corso...
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-xl mb-4 text-sm">
            {error}
          </div>
        )}

        {!isLoading && !error && rentals.length === 0 && (
          <div className="bg-white p-6 rounded-2xl border-2 border-dashed border-slate-200 text-center text-slate-500">
            Nessun noleggio attivo al momento. <br/> Esplora la mappa per prenotare un veicolo!
          </div>
        )}

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

            <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center text-xs text-slate-500">
              <span>Batteria: {rental.veicolo_dettagli?.livello_batteria != null ? `${rental.veicolo_dettagli.livello_batteria}%` : '—'}</span>
              <span>Inizio: {new Date(rental.dataorainizio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>
        ))}
      </main>

      {/* BOTTOM NAVBAR */}
      <nav className="fixed bottom-0 w-full bg-white border-t border-slate-200 p-3 pb-safe flex justify-around items-center shadow-[0_-2px_10px_rgba(0,0,0,0.05)] z-10">
        <button className="flex flex-col items-center p-2 text-slate-400 hover:text-blue-600 transition-colors">
          <span className="text-2xl mb-1">🗺️</span>
          <span className="text-[10px] font-semibold">Mappa</span>
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
