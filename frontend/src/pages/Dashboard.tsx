import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const navigate = useNavigate()
  
  // Leggiamo direttamente il token salvato nel browser
  const token = localStorage.getItem('token')

  // Se il token manca, eseguiamo il reindirizzamento
  useEffect(() => {
    if (!token) {
      navigate('/login')
    }
  }, [token, navigate])

  // Funzione per il logout
  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  // Se il token non c'è, blocchiamo la resa visiva prima del reindirizzamento
  if (!token) return null

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      
      {/* HEADER: Fisso in alto */}
      <header className="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center sticky top-0 z-10">
        <h1 className="text-xl font-bold">EcoFleet</h1>
        <button 
          onClick={handleLogout}
          className="text-sm bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded-full transition-colors"
        >
          Esci
        </button>
      </header>

      {/* CORPO CENTRALE */}
      <main className="flex-1 p-4 pb-24">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">I Miei Noleggi</h2>
        
        {/* Card statica temporanea */}
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 mb-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="font-bold text-slate-800">Fiat 500 Elettrica</h3>
              <p className="text-sm text-slate-500">Targa: GA123AA</p>
            </div>
            <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-full">
              Attivo
            </span>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 text-sm text-slate-600">
            <p>Scadenza: Oggi, 18:00</p>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-2xl border-2 border-dashed border-slate-200 text-center text-slate-500">
          Nessun altro noleggio attivo. <br/> Vai sulla mappa per trovare un veicolo!
        </div>
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