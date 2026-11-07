/**
 * File overview
 * Purpose: Present the authenticated customer's account details and current virtual credit.
 * Responsibilities: Load the profile, handle loading and failures, redirect rejected sessions
 *   to Login and provide return navigation to Dashboard.
 * Connections: App registers the page; Dashboard opens it; routes/paths supplies navigation,
 *   config/api supplies the base URL and types/auth describes GET /api/auth/me responses.
 */

//-- imports and cross-module dependencies--
import {useEffect, useState} from 'react'
import {Link, useNavigate} from 'react-router-dom'
import { API_BASE_URL } from '../config/api'
import {ROUTES} from '../routes/paths'
import type { UserProfile } from '../types/auth'

export default function Profile(){
    //---session and request state---
    const navigate = useNavigate()
    const token = localStorage.getItem('token')
    const [profile, setProfile] =useState<UserProfile | null> (null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')

    //--- profile effect: load the current account and cancel obsolete requests---
    useEffect(() => {
        if(!token){
            navigate(ROUTES.LOGIN, {replace: true})
            return
        }

        const controller = new AbortController()

        const fetchProfile = async () => {
            try{
                const response = await fetch(`${API_BASE_URL}/api/auth/me`,{
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                    signal: controller.signal,
                })

                if(controller.signal.aborted) return

                //--- rejected session: remove the token and request a new login
                if(response.status === 401){
                    localStorage.removeItem('token')
                    navigate(ROUTES.LOGIN, {replace:true})
                    return
                }

                if(!response.ok){
                    throw new Error('Unable to load profile')
                }

                const data:UserProfile= await response.json()

                if(!controller.signal.aborted){
                    setProfile(data)
                }
            }catch {
                //--- feedback: ignore cancellation and report request failures---
                if(!controller.signal.aborted){
                    setError('Impossibile caricare il profilo. Riprovare più tardi.')
                }
            } finally {
                if(!controller.signal.aborted){
                    setIsLoading(false)
                }
            }
        }
        fetchProfile()

        return()=>controller.abort()
    }, [token, navigate])

    //--- render guard: hide account content during the missing-session redirect---
    if (!token) return null

    //--- page rendering: navigation, feedback and authenticated account data---
    return(
        <main className='min-h-screen bg-slate-50 p-6'>
            <Link to={ROUTES.DASHBOARD} className='mb-6 inline-block text-blue-600'>
                ← I miei noleggi
            </Link>

            <h1 className='text-2xl font-bold text-slate-800'>
                Il mio profilo
            </h1>

            {isLoading && (
                <p className='mt-6 text-slate-500'>Caricamento profilo...</p>
            )}

            {error && (
                <p role='alert' className='mt-6 text-red-600'>{error}</p>
            )}

            {!isLoading && !error && profile && (
                <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <h2 className="text-lg font-semibold text-slate-800">
                        Dati account
                    </h2>

                    <p className="mt-3 break-words">Email: {profile.email}</p>
                    <p className="mt-2">Codice fiscale: {profile.codicefiscale}</p>

                    {/* Virtual credit: format the current server-provided balance. */}
                    <h2 className="mt-6 font-semibold text-slate-800">
                        Credito virtuale
                    </h2>

                    <p className="mt-2 text-2xl font-bold text-blue-600">
                        {Number(profile.saldo_crediti).toLocaleString('it-IT', {
                            style: 'currency',
                            currency: 'EUR',
                        })}
                    </p>
                </section>
            )}
        </main>
    )
}