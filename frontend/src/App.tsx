
import { useEffect, useState } from 'react'
import { apiGet } from './api'
import Sidebar from './components/Sidebar'
import DashboardPage from './pages/DashboardPage'
import ChannelsPage from './pages/ChannelsPage'
import JobsPage from './pages/JobsPage'
import ContentPage from './pages/ContentPage'
import TrendsPage from './pages/TrendsPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [healthy, setHealthy] = useState<boolean | null>(null)

  useEffect(() => {
    apiGet('/api/health').then(() => setHealthy(true)).catch(() => setHealthy(false))
  }, [])

  return (
    <div className="layout">
      <Sidebar page={page} onChange={setPage} />
      <main className="main">
        <div className="topbar">
          <div>
            <strong>System status:</strong> {healthy === null ? 'checking...' : healthy ? 'online' : 'offline'}
          </div>
          <div className="topbar-actions">
            <span className="pill">FastAPI + React</span>
            <span className="pill">Local-first</span>
          </div>
        </div>

        {page === 'dashboard' && <DashboardPage />}
        {page === 'channels' && <ChannelsPage />}
        {page === 'jobs' && <JobsPage />}
        {page === 'content' && <ContentPage />}
        {page === 'trends' && <TrendsPage />}
        {page === 'settings' && <SettingsPage />}
      </main>
    </div>
  )
}
