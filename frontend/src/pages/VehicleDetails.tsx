/**
 * file overview
 * purpose: provide the details page for a vehicle selected from Fleet
 * responsibilities: Read the vehicle identifier from the URL and provide fleet navigation
 * connections: App registers the dynamic route; Fleet generates vehicle-specific links;
 *      routes/paths supplies the shared navigation paths.
 */

//---Imports and navigation dependencies ---
import {Link, useParams} from 'react-router-dom'
import {ROUTES} from '../routes/paths'

export default function VehicleDetails(){
    //--- route data: extract the vehicle identifier from the current URL.---
    const {seriale} =useParams()//useParams returns an object with URL's parameters 

    // --- page rendering: shows the selected identifier and return navigation ---
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
        </main>
    )
}