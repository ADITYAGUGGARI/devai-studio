import { StrictMode } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import { Providers } from './app/Providers';
import './style.css';
import './desktop.css';
import './tokens.css';
import './studio-v4.css';
import { AccountGate } from './features/AccountGate';

const router = createBrowserRouter([
  {
    path: '*',
    element: (
      <Providers>
        <AccountGate>
          <App />
        </AccountGate>
      </Providers>
    ),
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
