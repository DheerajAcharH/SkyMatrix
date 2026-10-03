import React from 'react'
import ReactDOM from 'react-dom/client'
import { initializeFirebase } from './services/firebase'
import { DashboardView } from './views/DashboardView'
import './styles.css'

initializeFirebase()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <DashboardView />
  </React.StrictMode>,
)
