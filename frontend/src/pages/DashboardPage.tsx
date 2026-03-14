
import { useEffect, useState } from 'react'
import { apiGet } from '../api'
import Card from '../components/Card'

export default function DashboardPage() {
  const [data, setData] = useState<any>(null)

  useEffect(() => { apiGet('/api/dashboard').then(setData).catch(console.error) }, [])

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Dashboard</h2>
          <p>Quan sát toàn bộ hệ thống video, queue, channel và output.</p>
        </div>
      </div>

      <div className="stats-grid">
        <Card title="Total Jobs"><div className="metric">{data?.total_jobs ?? '-'}</div></Card>
        <Card title="Channels"><div className="metric">{data?.channels_count ?? '-'}</div></Card>
        <Card title="Queued"><div className="metric">{data?.job_counts?.queued ?? 0}</div></Card>
        <Card title="Uploaded"><div className="metric">{data?.job_counts?.uploaded ?? 0}</div></Card>
      </div>

      <div className="two-col">
        <Card title="Recent Jobs">
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>ID</th><th>Channel</th><th>Seed</th><th>State</th></tr></thead>
              <tbody>
                {(data?.recent_jobs ?? []).map((row: any) => (
                  <tr key={row.id}><td>{row.id}</td><td>{row.channel}</td><td>{row.title_seed}</td><td>{row.state}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Channels">
          <div className="stack">
            {(data?.channels ?? []).map((c: any) => (
              <div className="channel-box" key={c.name}>
                <strong>{c.name}</strong>
                <span>{c.niche}</span>
                <small>{c.language} · {c.default_video_format} · upload: {String(c.upload_enabled)}</small>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
