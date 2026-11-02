/**
 * File overview
 * Purpose: Present the sign-in page and exchange credentials for an access token.
 * Responsibilities: Control form inputs, send the OAuth2 form, display failures and navigate
 *   after a successful login.
 * Connections: Uses config/api and routes/paths; the backend auth router issues the token that
 *   Dashboard later sends.
 */

// --- Imports and cross-module dependencies ---
import { useState } from 'react'// Import state and navigation hooks used by the login component.
// State updates schedule a new render so the controlled inputs and feedback stay current.
import { useNavigate } from 'react-router-dom'// Navigate between React pages without a full browser reload.
import {ROUTES} from '../routes/paths'
import { API_BASE_URL } from '../config/api'


// --- Login component: credentials, feedback and successful-login navigation ---
export default function Login() {
  // --- Controlled input state: each setter updates the value shown in the form. ---
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()


// --- Form submission: prevent navigation and authenticate with the backend ---
// Prevent the default HTML form submission so React can handle the result.
const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')// Clear feedback from the previous attempt.

    // Encode credentials using the form format expected by OAuth2PasswordRequestForm.
    const formData = new URLSearchParams()// URLSearchParams produces an application/x-www-form-urlencoded request body.
    formData.append('username', email) // The backend interprets OAuth2's username field as the email address.
    formData.append('password', password)

    
    // --- HTTP request: submit the credential form to the shared API base URL ---
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {// Wait for the HTTP response before examining its status.
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',// Describe the encoded form body to FastAPI.
        },
        body: formData,
      })

      // --- Response handling: non-success statuses enter the existing generic login error path ---
      if (!response.ok) {
        throw new Error('Credenziali errate o utente inesistente')
      }


      // Parse the successful response containing access_token and the account summary.
      const data = await response.json()
      // Persist the bearer token for protected API requests made by other pages.
      localStorage.setItem('token', data.access_token)
      navigate(ROUTES.DASHBOARD)
    
    } catch (err) {
      // --- Failure handling: expose request or credential errors in the form ---
      if (err instanceof Error) {// Narrow the caught value before accessing Error.message.
        setError(err.message)// Update the message rendered by the conditional feedback box.
      } else {
        setError('Si è verificato un errore imprevisto')
      }
    }
  }

  // --- Page rendering: branding, request feedback and the credential form. ---
  return (
    <div className="min-h-screen bg-slate-50 p-6 flex flex-col justify-center">
      <h1 className="text-3xl font-bold text-center text-blue-600 mb-8">EcoFleet</h1>
      
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h2 className="text-xl font-semibold mb-6 text-slate-800">Accedi al tuo account</h2>
        
        {/* Feedback section: render the error box only when the error state contains a message. */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Form section: submit through handleLogin instead of performing a native page navigation. */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            {/* Email field: browser validation plus React-controlled input state. */}
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label> {/* Tailwind utility classes style the form controls. */}
            <input 
              type="email" /* Browser email validation complements the controlled value and onChange below. */
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}/* Store the latest field value so React state and the displayed input stay in sync. */
              className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="esempio@email.com"
            />
          </div>
          
          <div>
            {/* Password field: conceal entered characters and keep the submitted value in state. */}
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
            />
          </div>

          {/* Submit action: the form onSubmit handler runs for a click or Enter key. */}
          <button 
            type="submit" 
            className="w-full bg-blue-600 text-white font-semibold p-3 rounded-lg hover:bg-blue-700 transition-colors mt-2"
          >
            Accedi
          </button>
        </form>
      </div>
    </div>
  )
}
