import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/AppLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ComingSoonPage } from '@/pages/ComingSoonPage'
import { ConfigPage } from '@/pages/ConfigPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ExtratoPage } from '@/pages/ExtratoPage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'

function Protected({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<Protected><DashboardPage /></Protected>} />
      <Route
        path="/investimentos"
        element={<Protected><ComingSoonPage title="Investimentos" /></Protected>}
      />
      <Route path="/extrato" element={<Protected><ExtratoPage /></Protected>} />
      <Route
        path="/metas"
        element={<Protected><ComingSoonPage title="Metas e orçamento" /></Protected>}
      />
      <Route path="/config" element={<Protected><ConfigPage /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
