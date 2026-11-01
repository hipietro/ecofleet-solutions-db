export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||'http://localhost:8000'
    //import.meta.env contiene le varibili esposte da Vite. Se VITE_API_BASE_URL non è impostata allora utilizza l'indirizzo locale
    //le variabili VITE_ sono visibili nel browser, servono per configurazione pubblica, non per pw o segreti JWT