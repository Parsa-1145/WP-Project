import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ModalProvider } from './modals/ModalHost.js'
import { BrowserRouter } from 'react-router-dom'
import { Toaster, ToastBar, toast } from 'react-hot-toast'

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <ModalProvider>
      <Toaster
        position="right-bottom"
        toastOptions={{
          duration: 3000,
          style: {
            background: 'var(--c-surface)',
            color: 'var(--c-text)',
            border: '1px solid var(--c-border)',
            borderRadius: '0px',
            cursor: 'pointer',
          },
          success: {
            style: { background: 'var(--c-success)', color: '#000' },
            iconTheme: { primary: '#000', secondary: 'var(--c-success)' },
          },
          error: {
            style: { background: 'var(--c-danger)', color: '#000', fontWeight:"bold"},
            iconTheme: { primary: '#000', secondary: 'var(--c-danger)' },
          },
        }}
      >
      </Toaster>
      <App/>
    </ModalProvider>
  </BrowserRouter>
)
