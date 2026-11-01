import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import { ROUTES } from './routes/paths'
import Fleet from './pages/Fleet'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
        path={ROUTES.HOME}//le parentesi graffe permettono di passare un valore Javascript agli attributi JSX
        element={<Navigate to={ROUTES.LOGIN} replace/>}
        />
        {/* Pagine dell'app */}
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
        <Route path={ROUTES.FLEET} element={<Fleet />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App