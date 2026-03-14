
import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api'
import Card from '../components/Card'

const initialForm = {
  name: '',
  title_prefix: '',
  niche: '',
  language: 'en',
  default_video_format: 'shorts',
  upload_enabled: false,
  privacy_status: 'private',
  category_id: '27',
  publish_interval_minutes: 60,
  daily_upload_soft_limit: 90,
  notify_subscribers: false,
  tags: [],
  voice_provider_order: ['openai'],
  transcribe_provider_order: ['openai'],
  footage_provider_order: ['pexels', 'pixabay'],
  research_provider_order: ['wikipedia', 'trafilatura', 'scrapling'],
  youtube_client_secrets: 'client_secret.json',
  youtube_token_json: 'token.json',
  disclose_synthetic_media: false,
  allowed_seed_domains: [],
  blocked_words: []
}

export default function ChannelsPage() {
  const [items, setItems] = useState<any[]>([])
  const [form, setForm] = useState<any>(initialForm)
  const [message, setMessage] = useState('')

  const load = () => apiGet<any>('/api/channels').then(r => setItems(r.items))
  useEffect(() => { load() }, [])

  async function submit() {
    const payload = {
      ...form,
      tags: String(form.tags).split(',').map((x: string) => x.trim()).filter(Boolean),
      blocked_words: String(form.blocked_words).split(',').map((x: string) => x.trim()).filter(Boolean),
      allowed_seed_domains: String(form.allowed_seed_domains).split(',').map((x: string) => x.trim()).filter(Boolean)
    }
    const res = await apiPost<any>('/api/channels', payload)
    setMessage(res.message)
    setForm(initialForm)
    load()
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h2>Channels</h2>
          <p>Quản lý niche, lịch đăng, upload policy và provider cho từng kênh.</p>
        </div>
      </div>

      <div className="two-col">
        <Card title="Danh sách kênh">
          <div className="stack">
            {items.map((c) => (
              <div className="channel-box" key={c.name}>
                <strong>{c.name}</strong>
                <span>{c.niche}</span>
                <small>{c.language} · {c.default_video_format} · every {c.publish_interval_minutes} min</small>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Tạo / cập nhật channel" right={<span className="pill">{message || 'ready'}</span>}>
          <div className="form-grid">
            <input placeholder="Channel name" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
            <input placeholder="Title prefix" value={form.title_prefix} onChange={e => setForm({...form, title_prefix: e.target.value})} />
            <input placeholder="Niche" value={form.niche} onChange={e => setForm({...form, niche: e.target.value})} />
            <input placeholder="Language" value={form.language} onChange={e => setForm({...form, language: e.target.value})} />
            <input placeholder="Format" value={form.default_video_format} onChange={e => setForm({...form, default_video_format: e.target.value})} />
            <input placeholder="Category ID" value={form.category_id} onChange={e => setForm({...form, category_id: e.target.value})} />
            <input placeholder="Tags comma separated" value={String(form.tags)} onChange={e => setForm({...form, tags: e.target.value})} />
            <input placeholder="Blocked words comma separated" value={String(form.blocked_words)} onChange={e => setForm({...form, blocked_words: e.target.value})} />
            <input placeholder="Allowed domains comma separated" value={String(form.allowed_seed_domains)} onChange={e => setForm({...form, allowed_seed_domains: e.target.value})} />
          </div>
          <div className="inline-actions">
            <label><input type="checkbox" checked={form.upload_enabled} onChange={e => setForm({...form, upload_enabled: e.target.checked})} /> Upload enabled</label>
            <label><input type="checkbox" checked={form.disclose_synthetic_media} onChange={e => setForm({...form, disclose_synthetic_media: e.target.checked})} /> Disclosure</label>
          </div>
          <button className="primary" onClick={submit}>Save channel</button>
        </Card>
      </div>
    </div>
  )
}
