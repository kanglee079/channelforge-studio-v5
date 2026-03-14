
import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api'
import Card from '../components/Card'

export default function TrendsPage() {
  const [data, setData] = useState<any>(null)
  const [niche, setNiche] = useState('history facts')
  const [geo, setGeo] = useState('VN')

  const load = () => apiGet<any>('/api/trends').then(setData)
  useEffect(() => { load() }, [])

  async function scan() {
    const res = await apiPost<any>('/api/trends/scan', { niche, geo, max_items: 50 })
    setData(res)
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Trend Radar</h2>
          <p>Trợ lý trend quét nhiều nguồn để tìm topic mới, angle mới và niche đang tăng nhiệt.</p>
        </div>
      </div>

      <Card title="Trend query">
        <div className="inline-actions">
          <input value={niche} onChange={e => setNiche(e.target.value)} placeholder="Niche" />
          <input value={geo} onChange={e => setGeo(e.target.value)} placeholder="Geo code" />
          <button className="primary" onClick={scan}>Scan now</button>
        </div>
      </Card>

      <Card title={`Trend items (${data?.items?.length ?? 0})`}>
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Title</th><th>Source</th><th>Score</th><th>Published</th></tr></thead>
            <tbody>
              {(data?.items ?? []).map((row: any, i: number) => (
                <tr key={i}>
                  <td><a href={row.url} target="_blank">{row.title}</a></td>
                  <td>{row.source}</td>
                  <td>{row.score}</td>
                  <td>{row.published_at || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
