import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './i18n';
import './index.css';
import App from './App';
import ErrorBoundary from './components/common/ErrorBoundary';
import { AuthProvider } from './context/AuthContext';
import { AppProvider } from './context/AppContext';
import { ToastProvider } from './context/ToastContext';
import { readStored } from './services/storage';
document.documentElement.classList.toggle('high-contrast', readStored('contrast', false));
const container = document.getElementById('root');
if (!container)
  throw new Error('Aero Health could not find its root element.');
createRoot(container).render(<StrictMode>
  <ErrorBoundary>
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <AppProvider>
            <App />
          </AppProvider>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  </ErrorBoundary>
</StrictMode>);
