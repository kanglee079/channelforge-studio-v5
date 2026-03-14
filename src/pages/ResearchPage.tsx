import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface Research {
  id: number; title: string; source_url: string; source_title: string;
  extractor: string; cleaned_text: string; channel_name: string; created_at: string;
}

export default function ResearchPage() {
  const [items, setItems] = useState<Research[]>([]);
  const [url, setUrl] = useState("");
  const [channel, setChannel] = useState("");
  const [channels, setChannels] = useState<any[]>([]);
  const [extracting, setExtracting] = useState(false);
  const [msg, setMsg] = useState("");
  const [selected, setSelected] = useState<Research | null>(null);

  const load = () => api.get<{ items: Research[] }>("/api/v2/research?limit=50").then((r) => setItems(r.items)).catch(() => {});
  useEffect(() => {
    load();
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
  }, []);

  const extract = async () => {
    if (!url.trim()) return;
    setExtracting(true); setMsg("Đang trích xuất...");
    try {
      const res = await api.post<{ title: string; extractor: string; text_length: number }>("/api/v2/research/extract", {
        url, channel_name: channel || null, extractor: "auto",
      });
      setMsg(`✅ ${res.title} (${res.extractor}, ${res.text_length} ký tự)`);
      setUrl("");
      load();
    } catch (e: any) { setMsg(`❌ ${e.message}`); }
    setExtracting(false);
  };

  const del = async (id: number) => {
    await api.del(`/api/v2/research/${id}`);
    setSelected(null);
    load();
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Research Library</h2>
        <p>Thu thập, trích xuất và lưu trữ tài liệu nghiên cứu từ nhiều nguồn.</p>
      </div>

      <Card title="Trích xuất từ URL" right={msg ? <span className="chip chip-accent">{msg}</span> : null}>
        <div className="inline-controls">
          <input className="form-input" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://en.wikipedia.org/wiki/..." style={{ flex: 2 }} />
          <select className="form-input" value={channel} onChange={(e) => setChannel(e.target.value)} style={{ width: 160 }}>
            <option value="">Tất cả channels</option>
            {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
          <button className="btn btn-primary" onClick={extract} disabled={extracting}>{extracting ? "Đang xử lý..." : "Trích xuất"}</button>
        </div>
      </Card>

      <div className="grid-2" style={{ marginTop: 16 }}>
        <Card title={`Tài liệu (${items.length})`}>
          <div className="list-stack">
            {items.map((r) => (
              <div key={r.id} className="list-item clickable" onClick={() => setSelected(r)}>
                <div className="list-item-main">
                  <strong>{r.title}</strong>
                  <span className="chip chip-sm">{r.extractor}</span>
                </div>
                <div className="list-item-meta">
                  <span>{r.channel_name || "—"}</span>
                  <span className="text-sm">{r.created_at?.slice(0, 16)}</span>
                </div>
              </div>
            ))}
            {items.length === 0 && <p className="text-muted">Chưa có tài liệu. Hãy trích xuất từ URL ở trên.</p>}
          </div>
        </Card>

        {selected && (
          <Card title={selected.title} right={
            <button className="btn btn-sm" style={{ color: "var(--red)" }} onClick={() => del(selected.id)}>Xóa</button>
          }>
            <div className="list-item-meta" style={{ marginBottom: 8 }}>
              <span>Nguồn: <a href={selected.source_url} target="_blank" rel="noreferrer">{selected.source_url}</a></span>
              <span>Extractor: {selected.extractor}</span>
            </div>
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: "var(--text-muted)", maxHeight: 400, overflow: "auto", background: "var(--bg-0)", padding: 12, borderRadius: 6 }}>
              {selected.cleaned_text || "(trống)"}
            </pre>
          </Card>
        )}
      </div>
    </div>
  );
}
