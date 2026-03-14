import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface TrendItem {
  id: number; source_type: string; title: string; snippet: string;
  url: string; region: string; fetched_at: string; status: string;
  // Scoring fields (optional)
  final_score?: number; recommended_action?: string;
  relevance_score?: number; contentability_score?: number;
}

interface Watchlist {
  id: number; channel_name: string; name: string;
  watch_type: string; query: string; active: number;
}

const ACTION_VI: Record<string, string> = {
  produce: "🎬 Sản xuất", research: "📚 Nghiên cứu", watch: "👁️ Theo dõi", skip: "⏭️ Bỏ qua",
};
const ACTION_COLOR: Record<string, string> = {
  produce: "chip-done", research: "chip-retry", watch: "chip-queued", skip: "",
};

export default function TrendsPage() {
  const [tab, setTab] = useState<"ingest" | "scored" | "watchlists">("ingest");
  const [query, setQuery] = useState("");
  const [geo, setGeo] = useState("US");
  const [sources, setSources] = useState(["google_trends", "newsapi"]);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [scored, setScored] = useState<TrendItem[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [selectedChannel, setSelectedChannel] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  // Watchlist form
  const [wlName, setWlName] = useState("");
  const [wlQuery, setWlQuery] = useState("");

  useEffect(() => {
    api.get<{ items: any[] }>("/api/channels").then((r) => { setChannels(r.items); if (r.items.length) setSelectedChannel(r.items[0].name); }).catch(() => {});
    api.get<{ items: TrendItem[] }>("/api/v5/research/trends").then((r) => setTrends(r.items)).catch(() => {});
    api.get<{ items: Watchlist[] }>("/api/v5/research/watchlists").then((r) => setWatchlists(r.items)).catch(() => {});
  }, []);

  const ingest = async () => {
    setLoading(true); setMsg("Đang thu thập xu hướng...");
    try {
      const res = await api.post<{ total: number; message: string }>("/api/v5/research/trends/ingest", {
        sources, query: query || undefined, region: geo, max_per_source: 15,
      });
      setMsg(res.message);
      api.get<{ items: TrendItem[] }>("/api/v5/research/trends").then((r) => setTrends(r.items));
    } catch (e: any) { setMsg(e.message); }
    setLoading(false);
  };

  const scoreTrends = async () => {
    if (!selectedChannel) return;
    setLoading(true); setMsg(`Đang chấm điểm trends cho ${selectedChannel}...`);
    try {
      const res = await api.post<{ items: TrendItem[]; produce: number; research: number }>("/api/v5/research/trends/score", { channel_name: selectedChannel });
      setScored(res.items); setTab("scored");
      setMsg(`${res.produce} "Sản xuất" · ${res.research} "Nghiên cứu"`);
    } catch (e: any) { setMsg(e.message); }
    setLoading(false);
  };

  const generateIdeas = async (title: string) => {
    if (!selectedChannel) return;
    setMsg(`Đang tạo ý tưởng từ "${title}"...`);
    try {
      const res = await api.post<{ count: number }>("/api/v5/research/ideas/generate", {
        trend_title: title, channel_name: selectedChannel,
      });
      setMsg(`Đã tạo ${res.count} ý tưởng video → xem tại trang Nội dung`);
    } catch (e: any) { setMsg(e.message); }
  };

  const createWatchlist = async () => {
    if (!wlName.trim() || !wlQuery.trim() || !selectedChannel) return;
    try {
      const res = await api.post<{ message: string }>("/api/v5/research/watchlists", {
        channel_name: selectedChannel, name: wlName, query: wlQuery,
      });
      setMsg(res.message); setWlName(""); setWlQuery("");
      api.get<{ items: Watchlist[] }>("/api/v5/research/watchlists").then((r) => setWatchlists(r.items));
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Radar xu hướng 2.0</h2>
        <p>Thu thập đa nguồn, chấm điểm theo kênh, tạo ý tưởng video tự động.</p>
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      {/* Channel selector + tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
        <select className="form-input" style={{ maxWidth: 200 }} value={selectedChannel} onChange={(e) => setSelectedChannel(e.target.value)}>
          {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
        </select>
        <button className={`btn btn-sm ${tab === "ingest" ? "btn-primary" : ""}`} onClick={() => setTab("ingest")}>Thu thập ({trends.length})</button>
        <button className={`btn btn-sm ${tab === "scored" ? "btn-primary" : ""}`} onClick={() => setTab("scored")}>Đã chấm ({scored.length})</button>
        <button className={`btn btn-sm ${tab === "watchlists" ? "btn-primary" : ""}`} onClick={() => setTab("watchlists")}>Watchlists ({watchlists.length})</button>
      </div>

      {/* ── INGEST TAB ── */}
      {tab === "ingest" && (
        <>
          <Card title="Thu thập xu hướng">
            <div className="inline-controls">
              <input className="form-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Từ khóa (để trống = trending)" style={{ flex: 2 }} />
              <input className="form-input" value={geo} onChange={(e) => setGeo(e.target.value)} placeholder="Region" style={{ width: 60 }} />
              <button className="btn btn-primary" onClick={ingest} disabled={loading}>{loading ? "⏳..." : "📡 Thu thập"}</button>
              <button className="btn" onClick={scoreTrends} disabled={loading || !selectedChannel}>📊 Chấm điểm</button>
            </div>
          </Card>

          {trends.length > 0 && (
            <Card title={`Trends gần đây (${trends.length})`}>
              <table className="data-table">
                <thead><tr><th>CHỦ ĐỀ</th><th>NGUỒN</th><th>KHU VỰC</th><th>THỜI GIAN</th><th></th></tr></thead>
                <tbody>
                  {trends.slice(0, 30).map((t) => (
                    <tr key={t.id}>
                      <td className="cell-title"><strong>{t.title}</strong>{t.snippet && <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{t.snippet.slice(0, 80)}</div>}</td>
                      <td><span className="chip chip-sm">{t.source_type}</span></td>
                      <td>{t.region}</td>
                      <td style={{ fontSize: "0.8rem" }}>{t.fetched_at ? new Date(t.fetched_at).toLocaleDateString("vi-VN") : "–"}</td>
                      <td><button className="btn btn-sm" onClick={() => generateIdeas(t.title)}>💡 Tạo ý tưởng</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </>
      )}

      {/* ── SCORED TAB ── */}
      {tab === "scored" && (
        <Card title={`Xu hướng đã chấm — ${selectedChannel} (${scored.length})`}>
          {scored.length > 0 ? (
            <table className="data-table">
              <thead><tr><th>CHỦ ĐỀ</th><th>ĐIỂM</th><th>HÀNH ĐỘNG</th><th>PHÙ HỢP</th><th>NỘI DUNG</th><th></th></tr></thead>
              <tbody>
                {scored.map((t, i) => (
                  <tr key={i}>
                    <td className="cell-title"><strong>{t.title}</strong></td>
                    <td><strong>{((t.final_score || 0) * 100).toFixed(0)}%</strong></td>
                    <td><span className={`chip chip-sm ${ACTION_COLOR[t.recommended_action || "skip"]}`}>{ACTION_VI[t.recommended_action || "skip"]}</span></td>
                    <td>{((t.relevance_score || 0) * 100).toFixed(0)}%</td>
                    <td>{((t.contentability_score || 0) * 100).toFixed(0)}%</td>
                    <td>
                      {(t.recommended_action === "produce" || t.recommended_action === "research") && (
                        <button className="btn btn-sm" onClick={() => generateIdeas(t.title)}>💡 Ý tưởng</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="text-muted">Chưa có kết quả. Bấm "📊 Chấm điểm" ở tab Thu thập.</p>}
        </Card>
      )}

      {/* ── WATCHLISTS TAB ── */}
      {tab === "watchlists" && (
        <div className="grid-2">
          <Card title="Watchlists">
            <div className="list-stack">
              {watchlists.map((w) => (
                <div key={w.id} className="list-item">
                  <div className="list-item-main"><strong>{w.name}</strong><span className="chip chip-sm">{w.watch_type}</span></div>
                  <div className="list-item-meta"><span>Query: {w.query}</span><span>Kênh: {w.channel_name}</span></div>
                </div>
              ))}
              {watchlists.length === 0 && <p className="text-muted">Chưa có watchlist nào.</p>}
            </div>
          </Card>
          <Card title="Thêm watchlist">
            <div className="form-grid">
              <div className="form-field">
                <label className="form-label">Tên</label>
                <input className="form-input" value={wlName} onChange={(e) => setWlName(e.target.value)} placeholder="VD: Space trending" />
              </div>
              <div className="form-field">
                <label className="form-label">Từ khóa / Query</label>
                <input className="form-input" value={wlQuery} onChange={(e) => setWlQuery(e.target.value)} placeholder="VD: space exploration" />
              </div>
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={createWatchlist}>Thêm watchlist</button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
