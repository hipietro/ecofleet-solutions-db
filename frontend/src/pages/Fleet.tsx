/**
 * File overview
 * Purpose: Display the vehicles currently available for rental.
 * Responsibilities: Fetch the public filtered fleet, handle loading/error/empty states and render
 *   individual hourly rates.
 * Connections: Uses config/api, routes/paths and types/fleet; calls the backend fleet router and
 *   links back to Dashboard.
 */

// --- Imports and cross-module dependencies ---
import { useNavigate } from "react-router-dom"
import { useEffect, useState } from "react"
import { API_BASE_URL } from "../config/api"
import type { Vehicle } from "../types/fleet"
import {ROUTES} from '../routes/paths'

// --- Page state: navigation, available vehicles and request feedback. ---
export default function Fleet(){
    const navigate = useNavigate()
    const [vehicles, setVehicles] = useState<Vehicle[]>([])// Keep vehicles, loading state and request feedback between renders.
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')

    // --- Fleet effect: load public availability and clean up an obsolete request. ---
    useEffect(()=>{// Start the request when the component mounts.
        const controller = new AbortController()// Abort the pending request when the effect is cleaned up.

        // --- Request section: filter availability on the server and parse the returned vehicle array. ---
        const fetchVechicles = async()=>{
            try{
                const response = await fetch(
                    `${API_BASE_URL}/api/fleet/vehicles?stato=Disponibile`,
                    {signal: controller.signal},
                )

                // --- HTTP failure section: reject unsuccessful responses before attempting to render their body. ---
                if(!response.ok){
                    throw new Error('Unable to load vehicles')
                }
                
                const data: Vehicle[] = await response.json()// Read and parse the JSON body; the interface describes its compile-time shape.

                if(!controller.signal.aborted){
                    setVehicles(data)// Store the result and schedule a render of the vehicle cards.
                }
            // --- Error section: ignore deliberate cancellation and expose genuine request failures. ---
            } catch{
                if(!controller.signal.aborted){
                    setError('Impossibile caricare i veicoli. Riprovare più tardi.')
                }
            // --- Completion section: stop showing the loader only while this effect is still active. ---
            } finally{
                if(!controller.signal.aborted){
                    setIsLoading(false)
                }
            }
        }
        fetchVechicles()

        // --- Cleanup section: cancel fetch when React replaces the effect or unmounts this page. ---
        return()=>controller.abort()
    }, [])

    // --- Page rendering: navigation, introduction, feedback and one card per available vehicle. ---
    return(
        <main className="min-h-screen bg-slate-50 p-6">
            {/* Navigation section: return to the customer dashboard using the shared route constant. */}
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

            {/* Loading section: show progress until the request completes. */}
            {isLoading && (
                <p className="mt-6 text-slate-500">Caricamento veicoli...</p>
            )}

            {/* Error section: announce a failed request through an accessible alert. */}
            {error && (
                <p role="alert" className="mt-6 text-red-600">
                  {error}
                </p>
            )}

            {/* Empty section: distinguish a successful empty response from a loading or network error. */}
            {!isLoading && !error && vehicles.length === 0 && (
                <p className="mt-6 text-slate-500">
                    Nessun veicolo disponibile al momento.
                </p>
            )}

            {/* Vehicle cards: map API rows to stable keyed elements with identity and hourly pricing. */}
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

                    {/* Price display: convert the API Decimal string for localized currency formatting only. */}
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
