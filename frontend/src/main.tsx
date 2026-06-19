import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from '@/lib/auth'
import { ThemeProvider } from '@/lib/theme'
import { UiProvider } from '@/lib/ui'
import { Toaster } from '@/components/ui/sonner'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <UiProvider>
        <BrowserRouter>
          <AuthProvider>
            <App />
            <Toaster richColors />
          </AuthProvider>
        </BrowserRouter>
      </UiProvider>
    </ThemeProvider>
  </StrictMode>,
)
