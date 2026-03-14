
import { useEffect, useState } from 'react'
import { apiGet } from '../api'
import Card from '../components/Card'

export default function SettingsPage() {
  const [keys, setKeys] = useState<any>(null)
  const [sources, setSources] = useState<any>(null)

  useEffect(() => {
    apiGet('/api/settings/keys').then(setKeys)
    apiGet('/api/sources').then(setSources)
  }, [])

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Settings & Integrations</h2>
          <p>Xem nhanh key status, provider đang bật và trend/data sources đã nối.</p>
        </div>
      </div>

      <div className="two-col">
        <Card title="API key status">
          <pre className="pre">{JSON.stringify(keys, null, 2)}</pre>
        </Card>
        <Card title="Sources">
          <pre className="pre">{JSON.stringify(sources, null, 2)}</pre>
        </Card>
      </div>
    </div>
  )
}
