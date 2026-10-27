import { useState } from 'react'//importo gli strumenti necessari da React e dal router
//useState serve a creare variabili che, se modificate, aggiornano l'interfaccia in tempo reale
import { useNavigate } from 'react-router-dom'//useNavigate fa cambiare pagina via codice


//definisco componente Login, creo 3 scatole di stati(email, pw, messaggi d'errore). userò poi le funzioni
//setEmail, setPassword e setError per riempire queste scatole quando l'utente digita qualcosa.
export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()


//questa funzione viene scatenata quando l'utente clicca su "Accedi"
//e.preventDefault() impedisce al browser di ricaricare l'intera pagina, cosa che succede di default con i form HTML
const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')//svuoto errori assegnati precedentemente

    // FastAPI con OAuth2 si aspetta i dati in questo formato esatto
    const formData = new URLSearchParams()//URLSearchParams impacchetta email e pw nel formato x-www-form-urlencoded che è quello che si aspetta il backend
    formData.append('username', email) // OAuth2 richiede sempre che il campo si chiami 'username'
    formData.append('password', password)

    
    //uso fetch per effettuare una chiamata POST al backend
    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {//await mette in pausa la funzione finchè FastAPI non risponde
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',//specifico il formato preparato e in body infilo i dati impacchettati qualche riga sopra
        },
        body: formData,
      })

      //è true se il backend risponde con un codice di successo (es 200). se FastAPI riturna un errore 401 o 422 lancia manualmente un errore 
      //che bloccherà l'esecuzione e passerà direttamente al catch
      if (!response.ok) {
        throw new Error('Credenziali errate o utente inesistente')
      }


      //se il login ha successo estrae la risposta in formato JSON e FastAPI restituisce un oggetto contentente un access_token(JWT)
      const data = await response.json()
      //salva questo token nel localStorage del browser consentendo di non dover rifare l'accesso per le chiamate future 
      localStorage.setItem('token', data.access_token)
      navigate('/dashboard')
    
    } catch (err) {
      //se FastAPI rifiuta la pw o il server è spento si finisce qua 
      if (err instanceof Error) {//instanceof assicura a TypeScript che stiamo gestendo un errore valido
        setError(err.message)//infine mette il messaggio di errore nella scatola di stato error, così il JSX la disegnerà a schermo con lo sfondo rosso
      } else {
        setError('Si è verificato un errore imprevisto')
      }
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 flex flex-col justify-center">
      <h1 className="text-3xl font-bold text-center text-blue-600 mb-8">EcoFleet</h1>
      
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h2 className="text-xl font-semibold mb-6 text-slate-800">Accedi al tuo account</h2>
        
        {/*rendering condizionale.
        si può usare la logica booleana per mostrare o nascondere elementi. L'espressione error &&(<div> .... </div>)
        significa letteralmente che se la variabile di stato error contiene qualcosa è vera e quindi disegna a schermo
        il box con sfondo rosso e stampa dentro l'errore, cioè la cosa dichiarata nel <div> */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/*invece di usare il classico attributo action dell'HTML che cambierebbe la pagina, 
        dice al form che quando l'utente preme invio o clicca il pulsante submit, blocca tutto e lancia la funzione personalizzata*/}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label> {/*queste classi non sono altro che il CSS di tailwind */}
            <input 
              type="email" /*forza l'input a mostrare esattamente quello che c'è nella nostra 'scatola' di stato dell'email */
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}/*ogni volta che l'utente preme un tasto sulla tastiera questo evento scatta, prende la lettera appena digitata (e.target.value) e la salva usando setEmail */
              className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="esempio@email.com"
            />
          </div>
          
          <div>
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