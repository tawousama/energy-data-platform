import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout/Layout'
import HomePage from './pages/HomePage'
import SitesPage from './pages/SitesPage'
import AnalyticsPage from './pages/AnalyticsPage'
import './index.css'

// Configuration React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="sites" element={<SitesPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={
              <div className="text-white text-center py-20">
                <h1 className="text-3xl font-bold mb-4">Settings</h1>
                <p className="text-gray-400">Page en construction...</p>
              </div>
            } />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)