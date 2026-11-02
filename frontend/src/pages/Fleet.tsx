import { useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"
import { API_BASE_URL } from "../config/api"
import type { Vehicle } from "../types/fleet"
import {ROUTES} from '../routes/paths'

export default function Fleet(){
    const navigate = useNavigate()
    const [vehicles, setVehicles] = useState<Vehicle[]>([])//useState conserva i dati, stato di caricamento ed eventuale errore
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(()=>{//useEffect avvia la richiesta quando il componente viene montato
        const controller = new AbortController()//abortController annulla la richiesta se esci dalla pagina. La funzione restituita da useEffect esegue questa pulizia.

        const fetchVechicles = async()=>{
            try{
                const response = await fetch(
                    `${API_BASE_URL}/api/fleet/vehicles?stato=Disponibile`,
                    {signal: controller.signal},
                )

                if(!response.ok){
                    throw new Error('Unable to load vehicles')
                }
                
                const data: Vehicle[] = await response.json()//await aspetta la risposta, response.json() ne legge il contenuto che arriverà in formato JSON

                if(!controller.signal.aborted){
                    setVehicles(data)// aggiorna lo stato e React ridisegna la pagina
                }
            } catch{
                if(!controller.signal.aborted){
                    setError('Impossibile caricare i veicoli. Riprovare più tardi.')
                }
            } finally{
                if(!controller.signal.aborted){
                    setIsLoading(false)
                }
            }
        }
        fetchVechicles()

        return()=>controller.abort()
    }, [])

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

            {isLoading && (
                <p className="mt-6 text-slate-500">Caricamento veicoli...</p>
            )}

            {error && (
                <p role="alert" className="mt-6 text-red-600">
                  {error}
                </p>
            )}

            {!isLoading && !error && vehicles.length === 0 && (
                <p className="mt-6 text-slate-500">
                    Nessun veicolo disponibile al momento.
                </p>
            )}

            {!isLoading && !error && vehicles.map((vehicle) => (
                <article
                    key={vehicle.serialeveicolo}
                    className="mt-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                >
                    <h2 className="text-lg font-semibold text-slate-800">
                        {vehicle.marca} {vehicle.modello}
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                        Targa: {vehicle.targa ?? 'Non disponibile'}
                    </p>

                    <p className="mt-3 font-semibold text-blue-600">
                        {Number(vehicle.costoorario).toLocaleString('it-IT', {
                            style: 'currency',
                            currency: 'EUR',
                        })}/ora
                    </p>
                </article>
            ))}
            
        </main>
    )
}