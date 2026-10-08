import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import { Providers } from './app/Providers';
import './style.css';
import { AccountGate } from './features/AccountGate';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <AccountGate>
        <App />
      </AccountGate>
    </Providers>
  </StrictMode>,
);
