/**
 * File overview
 * Purpose: Present the authenticated customer's account details and virtual-wallet controls.
 * Responsibilities: Load the profile, handle request feedback, redirect rejected sessions to
 *   Login and coordinate virtual top-ups with the server-provided balance.
 * Connections: App registers the page; Dashboard opens it; routes/paths supplies navigation,
 *   config/api supplies the base URL and types/auth describes account and wallet responses
 *   from GET /api/auth/me and POST /api/auth/wallet/topup.
 */

//-- imports and cross-module dependencies--
import {useEffect, useState} from 'react'
import {Link, useNavigate} from 'react-router-dom'
import { API_BASE_URL } from '../config/api'
import {ROUTES} from '../routes/paths'
import type { UserProfile, WalletTopupResponse } from '../types/auth'

export default function Profile(){
    //---session and request state---
    const navigate = useNavigate()
    const token = localStorage.getItem('token')
    const [profile, setProfile] =useState<UserProfile | null> (null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')
    //---top-up state: track submission progress and separate wallet feedback---
    const [isToppingUp, setIsToppingUp] = useState(false)
    const [topupError, setTopupError] = useState('')//separated from error because a problem during the balance recharge has to let the profile data
    const [topupMessage, setTopupMessage] = useState('')

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

    // --- Top-up action: request virtual credit and use the balance returned by the server. ---
    const handleTopup = async (amount: number) => {
        if (!token || !profile || isToppingUp) return

        setIsToppingUp(true)
        setTopupError('')
        setTopupMessage('')

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/wallet/topup`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ importo: amount }),//converts the JS obj into JSON required by the API
            })

            // --- Rejected session: clear credentials and return to login. ---
            if (response.status === 401) {
                localStorage.removeItem('token')
                navigate(ROUTES.LOGIN, { replace: true })
                return
            }

            if (!response.ok) {
                throw new Error('Unable to confirm wallet top-up')
            }

            const data: WalletTopupResponse = await response.json()

            // --- Balance update: preserve account fields and use the server-provided balance. ---
            setProfile((current) => current
                ? { ...current, saldo_crediti: data.nuovo_saldo }
                : current
            )

            setTopupMessage(data.message)
        } catch {
            // --- Unconfirmed result: ask the user to check their balance before retrying. ---
            setTopupError(
                'Impossibile confermare la ricarica. Riapri il profilo per controllare il saldo prima di riprovare.',
            )
        } finally {
            setIsToppingUp(false)
        }
    }

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
                    {/* Top-up controls: offer fixed amounts and prevent repeated submissions while pending. */}
                    <h3 className="mt-6 font-semibold text-slate-800">
                        Ricarica il tuo credito
                    </h3>

                    <p className="mt-2 text-sm text-slate-500">
                        Le ricariche aggiungono credito virtuale senza addebiti reali.
                    </p>

                    <div className="mt-4 flex flex-wrap gap-3">
                        {[5, 10, 20].map((amount) => (
                            <button
                                key={amount}
                                type="button"
                                disabled={isToppingUp}
                                onClick={() => handleTopup(amount)}
                                className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:cursor-wait disabled:opacity-50"
                            >
                                +{amount} €
                            </button>
                        ))}
                    </div>

                    {/* Wallet feedback: announce pending, failed and confirmed operations. */}
                    {isToppingUp && (
                        <p role="status" className="mt-3 text-sm text-slate-500">
                            Ricarica in corso...
                        </p>
                    )}

                    {topupError && (
                        <p role="alert" className="mt-3 text-sm text-red-600">
                            {topupError}
                        </p>
                    )}

                    {topupMessage && (
                        <p role="status" className="mt-3 text-sm text-green-700">
                            {topupMessage}
                        </p>
                    )}
                </section>
            )}
        </main>
    )
}
