/**
 * File overview
 * Purpose: Display the details of a vehicle selected from Fleet.
 * Responsibilities: Load vehicle data when the URL identifier changes, handle loading, missing
 *   vehicles and request errors, cancel obsolete requests and render identity, status, mileage
 *   and hourly pricing.
 * Connections: App registers the dynamic route; Fleet generates vehicle-specific links;
 *   routes/paths supplies navigation paths; config/api supplies the API base URL; types/fleet
 *   describes the response from the backend fleet detail endpoint.
 */

//---Imports and navigation dependencies ---
import {Link, useParams} from 'react-router-dom'
import {ROUTES} from '../routes/paths'
import { useEffect, useState } from 'react'
import { API_BASE_URL } from '../config/api'
import type { Vehicle } from '../types/fleet'

export default function VehicleDetails(){
    //--- route data: extract the vehicle identifier from the current URL.---
    const {seriale} =useParams()//useParams returns an object with URL's parameters 

    // --- request state: store vehicle details, loading progress and user feedback. --- 
    // -Vehicle here stores a single vehicle, null means we dont have data yet, diff from Fleet
    const [vehicle, setVehicle] = useState<Vehicle | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')

    //---vehicle details: load details whenever the URL identifier changes. ---
    useEffect(()=> {
        const controller = new AbortController()

        const fetchVehicle = async() => {
            //--- reset section: clear the previous result before loading another vehicle ---
            setIsLoading(true)
            setError('')
            setVehicle(null)

            try{
                const response = await fetch(
                    `${API_BASE_URL}/api/fleet/vehicles/${seriale}`,// -${seriale} the identifier becomes part of the address of the request to the backend
                    {signal: controller.signal},
                )

                if (controller.signal.aborted) return

                //---HTTP feedback: distinguish an unknown vehicle from other failures ---
                if(response.status === 404){
                    setError('Veicolo non trovato.')
                    return
                }

                if (!response.ok){
                    throw new Error('Unable to load vehicle details')
                }

                const data: Vehicle = await response.json()

                if(!controller.signal.aborted){
                    setVehicle(data)
                }
            }catch{
                //---error feedback: ignore cancellation and report request failures.---
                if(!controller.signal.aborted){
                    setError('Impossibile caricare il veicolo. Riprovare più tardi.')
                }
            }finally{
                if(!controller.signal.aborted){
                    setIsLoading(false)
                }
            }
        }

        fetchVehicle()

        //--- cleanup: cancel the request when the identifier changes or the page unmounts. ---
        return () => controller.abort()
    }, [seriale]) // -[seriale] react repeats the effect if the vehicle changes in the URL. the cleanup ends the previous request


    // --- Page rendering: show navigation, request feedback and the loaded vehicle details. ---
    return(
        <main className='min-h-screen bg-slate-50 p-6'>
            <Link
                to={ROUTES.FLEET}
                className='mb-6 inline-block text-blue-600'
            >
                ← Veicoli disponibili
            </Link>

            <h1 className='text-2xl font-bold text-slate-800'>
                Dettagli veicolo
            </h1>

            <p className='mt-2 text-slate-500'>
                Veicolo #{seriale}
            </p>

            {/*request feedback: show loading progress or an acessible error message */}
            {isLoading && (
                <p className='mt-6 text-slate-500'>
                    Caricamento dettagli...
                </p>
            )}

            {error && (
                <p role='alert' className='mt-6 text-red-600'>
                    {error}
                </p>
            )}

            {/*vehicle details: render the result only after only after a succesfull request */}
            {!isLoading && !error && vehicle && (//vehicle && (...) enables to read properities such as vehicle.marca only if vehicle contains an object
                <article className='mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm'>
                    <h2 className='text-xl font-semibold text-slate-800'>
                        {vehicle.marca} {vehicle.modello}
                    </h2>

                    <p className='mt-2 text-slate-600'>
                        Targa: {vehicle.targa ?? 'Non disponibile'}
                    </p>

                    <p className='mt-2 text-slate-600'>
                        Stato: {vehicle.statooperativo}
                    </p>

                    <p className='mt-2 text-slate-600'>
                        Chilometraggio: {vehicle.kmtotali.toLocaleString('it-IT')} km
                    </p>

                    {/*price formatting: convert the API string for currency display. */}
                    <p className='mt-4 font-semibold text-blue-600'>
                        {Number(vehicle.costoorario).toLocaleString('it-IT', {
                            style: 'currency',
                            currency: 'EUR',
                        })}/ora
                    </p>
                </article>
            )}
        </main>
    )
}
