
import { useEffect, useState } from 'react'
import { apiGet } from '../api'
import Card from '../components/Card'

export default function ContentPage() {
  const [items, setItems] = useState<any[]>([])
  useEffect(() => { apiGet<any>('/api/content?limit=100').then(r => setItems(r.items)) }, [])
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Content Studio</h2>
          <p>Xem thư viện video đã render, thumbnail, description, tags và upload result.</p>
        </div>
      </div>

      <div className="content-grid">
        {items.map((item, idx) => (
          <Card key={idx} title={item.title}>
            <div className="stack">
              <small>{item.channel}</small>
              <small>{item.video}</small>
              <small>{item.thumbnail}</small>
              <small>{(item.tags || []).join(', ')}</small>
              <small>{item.upload ? JSON.stringify(item.upload) : 'not uploaded yet'}</small>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
