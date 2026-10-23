export default function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <header className="bg-white p-4 shadow-sm">
        <h1 className="text-xl font-bold text-blue-600">I Miei Noleggi</h1>
      </header>
      <main className="p-4">
        <p className="text-slate-600">Qui metteremo la mappa o la lista veicoli.</p>
      </main>
      
      {/* Finta Bottom Navbar (Mobile-First) */}
      <nav className="fixed bottom-0 w-full bg-white border-t border-slate-200 p-4 flex justify-around text-slate-500">
        <span>🚗 Mappa</span>
        <span>🔑 Noleggio</span>
        <span>👤 Profilo</span>
      </nav>
    </div>
  )
}