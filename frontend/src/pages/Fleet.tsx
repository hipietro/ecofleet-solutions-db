import { useNavigate } from "react-router-dom"
import {ROUTES} from '../routes/paths'

export default function Fleet(){
    const navigate = useNavigate()

    return(
        <main className="min-h-screen bg-slate-50 p-6">
            <button 
                onClick={()=>navigate(ROUTES.DASHBOARD)}
                className="mb-6 text-blue-600"
            >
                ← I miei noleggi
            </button>

            <h1 className="text-2xl font-bold text-slate-800">
                Veicoli disponibili
            </h1>
            <p className="mt-2 text-slate-500">
                Trova il veicolo per il tuo prossimo viaggio.
            </p>
        </main>
    )
}