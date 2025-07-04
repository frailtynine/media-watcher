import { Provider } from './components/ui/provider.tsx'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ComponentProvider } from './hooks/Сomponent.tsx'

createRoot(document.getElementById('root')!).render(
  <ComponentProvider>
    <StrictMode>
      <Provider>
        <App />
      </Provider>
    </StrictMode>
  </ComponentProvider>
)
