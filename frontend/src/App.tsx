import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import { ROUTES } from './routes/paths'

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
      </Routes>
    </BrowserRouter>
  )
}

export default App