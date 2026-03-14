
import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api'
import Card from '../components/Card'

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [channels, setChannels] = useState<any[]>([])
  const [profile, setProfile] = useState('')
  const [niche, setNiche] = useState('interesting animal facts')
  const [count, setCount] = useState(5)
  const [message, setMessage] = useState('')

  const load = () => apiGet<any>('/api/jobs?limit=100').then(r => setJobs(r.items))
  useEffect(() => {
    load()
    apiGet<any>('/api/channels').then(r => {
      setChannels(r.items)
      if (r.items?.[0]?.name) setProfile(r.items[0].name)
    })
  }, [])

  async function enqueue() {
    const res = await apiPost<any>('/api/jobs/enqueue', { profile, count, niche, format: 'shorts' })
    setMessage(res.message)
    load()
  }

  async function runWorker() {
    const res = await apiPost<any>('/api/workers/run', { profile, limit: 3 })
    setMessage(res.message)
    load()
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Jobs & Queue</h2>
          <p>Tạo hàng loạt job, chạy worker và theo dõi retry / failed / uploaded.</p>
        </div>
      </div>

      <Card title="Queue actions" right={<span className="pill">{message || 'idle'}</span>}>
        <div className="inline-actions">
          <select value={profile} onChange={e => setProfile(e.target.value)}>
            {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
          <input value={niche} onChange={e => setNiche(e.target.value)} placeholder="Niche / seed topic" />
          <input type="number" value={count} onChange={e => setCount(Number(e.target.value))} />
          <button className="primary" onClick={enqueue}>Enqueue</button>
          <button onClick={runWorker}>Run worker</button>
        </div>
      </Card>

      <Card title="Jobs">
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>ID</th><th>Channel</th><th>Seed</th><th>State</th><th>Retries</th><th>Updated</th></tr></thead>
            <tbody>
              {jobs.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td>{row.channel}</td>
                  <td>{row.title_seed}</td>
                  <td><span className="status">{row.state}</span></td>
                  <td>{row.retries}</td>
                  <td>{row.updated_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
