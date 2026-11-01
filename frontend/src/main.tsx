import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Início do painel: desenha o componente principal dentro do <div id="root"> de index.html.
// StrictMode ativa verificações extras do React durante o desenvolvimento.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
