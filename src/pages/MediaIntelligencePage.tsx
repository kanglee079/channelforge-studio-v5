import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

/* ── Types ── */
interface MatchRun { id: number; channel_name: string; model_name: string; total_scenes: number; matched_scenes: number; review_scenes: number; status: string; created_at: string; }
interface MatchItem { id: number; scene_index: number; spoken_text: string; visual_goal: string; confidence_score: number; confidence_label: string; fallback_used: string; requires_review: number; candidates_json: string; explain_json: string; }
interface Asset { id: number; asset_key: string; provider: string; asset_type: string; width: number; height: number; duration_sec: number; tags_json: string; embedding_status: string; }

const CONF_COLORS: Record<string, string> = { high: "#22c55e", medium: "#f59e0b", low: "#ef4444", pinned: "#3b82f6" };

export default function MediaIntelligencePage() {
  const [tab, setTab] = useState<"index" | "runs" | "inspector" | "assets">("index");
  const [indexStats, setIndexStats] = useState<any>(null);
  const [runs, setRuns] = useState<MatchRun[]>([]);
  const [selRun, setSelRun] = useState<MatchRun | null>(null);
  const [items, setItems] = useState<MatchItem[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [scriptText, setScriptText] = useState("");
  const [channelName, setChannelName] = useState("");
  const [loading, setLoading] = useState("");

  const fetchIndex = () => { api.get("/api/v2/media-intel/assets").then((d: any) => setIndexStats({ total_assets: d.total, index_size: d.index_size, model: d.embedding_model })).catch(() => {}); };
  const fetchRuns = () => { api.get<{ items: MatchRun[] }>("/api/v2/media-intel/match/runs").then(d => setRuns(d.items)).catch(() => {}); };
  const fetchAssets = () => { api.get<{ items: Asset[] }>("/api/v2/media-intel/assets").then(d => setAssets(d.items)).catch(() => {}); };

  useEffect(() => { fetchIndex(); fetchRuns(); fetchAssets(); }, []);

  const openRun = (run: MatchRun) => {
    setSelRun(run);
    api.get<{ items: MatchItem[] }>(`/api/v2/media-intel/match/runs/${run.id}`).then(d => { setItems(d.items); setTab("inspector"); }).catch(() => {});
  };

  const doRunMatch = async () => {
    if (!scriptText.trim()) return;
    setLoading("running");
    try {
      const res = await api.post<any>("/api/v2/media-intel/match/run", { script_text: scriptText, channel_name: channelName });
      if (res.ok && res.run_id) { fetchRuns(); openRun({ id: res.run_id, channel_name: channelName, model_name: res.model, total_scenes: res.total_scenes, matched_scenes: res.matched_scenes, review_scenes: res.review_scenes, status: "completed", created_at: new Date().toISOString() }); }
    } catch {}
    setLoading("");
  };

  const doRebuildIndex = async () => { setLoading("rebuild"); await api.post("/api/v2/media-intel/index/rebuild"); fetchIndex(); setLoading(""); };
  const doWarmup = async () => { setLoading("warmup"); await api.post("/api/v2/media-intel/index/warmup"); fetchIndex(); setLoading(""); };

  const TABS = [
    { key: "index", label: "🧠 Index Health" },
    { key: "runs", label: "🎯 Match Runs" },
    { key: "inspector", label: "🔍 Scene Inspector" },
    { key: "assets", label: "📦 Asset Library" },
  ] as const;

  return (
    <div>
      <h2>Media Intelligence</h2>
      <p className="text-muted">Semantic retrieval, vector index, rerank, shot planning — nâng cấp visual match engine.</p>

      <div className="tab-bar" style={{ marginBottom: 16 }}>
        {TABS.map(t => (
          <button key={t.key} className={`tab-btn${tab === t.key ? " active" : ""}`} onClick={() => setTab(t.key as typeof tab)}>{t.label}</button>
        ))}
      </div>

      {/* ── INDEX HEALTH ── */}
      {tab === "index" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Card title="Vector Index">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: "0.9rem" }}>
              <span className="text-muted">Tổng assets:</span><strong>{indexStats?.total_assets ?? 0}</strong>
              <span className="text-muted">Index size:</span><strong>{indexStats?.index_size ?? 0} vectors</strong>
              <span className="text-muted">Model:</span><strong>{indexStats?.model ?? "heuristic"}</strong>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn btn-primary" disabled={!!loading} onClick={doRebuildIndex}>🔄 Rebuild Index</button>
              <button className="btn" disabled={!!loading} onClick={doWarmup}>♨️ Warmup</button>
            </div>
          </Card>

          <Card title="Chạy Match Run Mới">
            <textarea value={scriptText} onChange={e => setScriptText(e.target.value)} placeholder="Dán script text vào đây..." rows={5}
              style={{ width: "100%", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, padding: 8, color: "var(--text-primary)", resize: "vertical" }} />
            <input value={channelName} onChange={e => setChannelName(e.target.value)} placeholder="Tên kênh (tùy chọn)"
              style={{ width: "100%", marginTop: 8, padding: 8, background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)" }} />
            <button className="btn btn-primary" style={{ marginTop: 8 }} disabled={!scriptText.trim() || !!loading} onClick={doRunMatch}>
              {loading === "running" ? "⏳ Đang chạy..." : "▶ Chạy Match"}
            </button>
          </Card>
        </div>
      )}

      {/* ── MATCH RUNS ── */}
      {tab === "runs" && (
        <Card title="Match Runs">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Kênh</th><th>Model</th><th>Scenes</th><th>Matched</th><th>Review</th><th>Status</th><th>Thời gian</th><th></th></tr></thead>
            <tbody>
              {runs.map(r => (
                <tr key={r.id}>
                  <td>#{r.id}</td><td>{r.channel_name || "—"}</td><td><code>{r.model_name}</code></td>
                  <td>{r.total_scenes}</td><td>{r.matched_scenes}</td>
                  <td>{r.review_scenes > 0 ? <span style={{color:"#f59e0b"}}>⚠️ {r.review_scenes}</span> : "0"}</td>
                  <td><span className="chip" style={{ background: r.status === "completed" ? "#22c55e" : "#f59e0b", color: "#fff", padding: "2px 8px", borderRadius: 8, fontSize: "0.75rem" }}>{r.status}</span></td>
                  <td className="text-muted" style={{fontSize: "0.8rem"}}>{new Date(r.created_at).toLocaleString("vi")}</td>
                  <td><button className="btn btn-sm" onClick={() => openRun(r)}>🔍 Xem</button></td>
                </tr>
              ))}
              {runs.length === 0 && <tr><td colSpan={9} className="text-muted">Chưa có match run. Paste script và chạy match ở tab Index Health.</td></tr>}
            </tbody>
          </table>
        </Card>
      )}

      {/* ── SCENE INSPECTOR ── */}
      {tab === "inspector" && (
        <div>
          {selRun && <p className="text-muted" style={{ marginBottom: 12 }}>Run #{selRun.id} — {selRun.channel_name || "—"} — {selRun.total_scenes} scenes — model: <code>{selRun.model_name}</code></p>}
          <div style={{ display: "grid", gap: 12 }}>
            {items.map(item => (
              <Card key={item.id} title="">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                      <strong>Scene #{item.scene_index}</strong>
                      <span className="chip" style={{ background: CONF_COLORS[item.confidence_label] || "#6b7280", color: "#fff", padding: "2px 10px", borderRadius: 12, fontSize: "0.8rem" }}>
                        {item.confidence_label} ({(item.confidence_score * 100).toFixed(0)}%)
                      </span>
                      {item.requires_review === 1 && <span style={{ color: "#f59e0b" }}>⚠️ Cần duyệt</span>}
                      {item.fallback_used && <span className="text-muted" style={{ fontSize: "0.8rem" }}>fallback: {item.fallback_used}</span>}
                    </div>
                    <p style={{ margin: "4px 0", fontSize: "0.85rem" }}>📝 {item.spoken_text}</p>
                    <p className="text-muted" style={{ margin: "2px 0", fontSize: "0.8rem" }}>🎯 {item.visual_goal}</p>
                  </div>
                  <div style={{ display: "flex", gap: 4 }}>
                    <button className="btn btn-sm" onClick={() => api.post(`/api/v2/media-intel/match/runs/${selRun?.id}/retry-scene`, { scene_index: item.scene_index }).then(() => selRun && openRun(selRun))}>🔄</button>
                  </div>
                </div>
              </Card>
            ))}
            {items.length === 0 && <Card title=""><p className="text-muted">Chọn run để xem chi tiết scenes.</p></Card>}
          </div>
        </div>
      )}

      {/* ── ASSET LIBRARY ── */}
      {tab === "assets" && (
        <Card title={`Asset Library (${assets.length} assets)`}>
          <table className="data-table">
            <thead><tr><th>Key</th><th>Provider</th><th>Type</th><th>Size</th><th>Duration</th><th>Tags</th></tr></thead>
            <tbody>
              {assets.map(a => (
                <tr key={a.id}>
                  <td><code style={{ fontSize: "0.8rem" }}>{a.asset_key}</code></td>
                  <td>{a.provider}</td>
                  <td>{a.asset_type}</td>
                  <td className="text-muted">{a.width}×{a.height}</td>
                  <td className="text-muted">{a.duration_sec > 0 ? `${a.duration_sec}s` : "—"}</td>
                  <td className="text-muted" style={{ fontSize: "0.75rem", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{a.tags_json}</td>
                </tr>
              ))}
              {assets.length === 0 && <tr><td colSpan={6} className="text-muted">Chưa có assets. Ingest assets bằng API hoặc thông qua pipeline sản xuất video.</td></tr>}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
