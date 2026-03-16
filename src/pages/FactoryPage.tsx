import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

/* ━━━━━━━━━━ Types ━━━━━━━━━━ */
interface YTStatus {
  configured: boolean;
  authenticated: boolean;
  client_secret_path: string;
  token_path: string;
  token_exists: boolean;
}
interface YTChannel {
  ok: boolean;
  channel_id?: string;
  title?: string;
  thumbnail?: string;
  subscriber_count?: string;
  video_count?: string;
  view_count?: string;
  custom_url?: string;
}
interface ShortResult {
  job_id: string;
  video_path: string;
  thumbnail_path: string;
  title: string;
  description: string;
  tags: string[];
  duration_sec: number;
  status: string;
  error?: string;
  youtube_id?: string;
  youtube_url?: string;
}

/* ━━━━━━━━━━ Main Page ━━━━━━━━━━ */
export default function FactoryPage() {
  // YouTube auth state
  const [ytStatus, setYtStatus] = useState<YTStatus | null>(null);
  const [ytChannel, setYtChannel] = useState<YTChannel | null>(null);
  const [connecting, setConnecting] = useState(false);

  // Shorts creation state
  const [topic, setTopic] = useState("");
  const [voice, setVoice] = useState("nova");
  const [niche, setNiche] = useState("animals");
  const [generating, setGenerating] = useState(false);
  const [genStatus, setGenStatus] = useState("");

  // History
  const [shorts, setShorts] = useState<ShortResult[]>([]);
  const [uploading, setUploading] = useState<string | null>(null);

  // Old pipeline
  const [jobs, setJobs] = useState<any[]>([]);

  /* ━━━━━━━━━━ Data Loading ━━━━━━━━━━ */
  const loadYouTube = useCallback(async () => {
    try {
      const status = await api.get<YTStatus>("/api/v5/youtube/auth/status");
      setYtStatus(status);
      if (status.authenticated) {
        const ch = await api.get<YTChannel>("/api/v5/youtube/channel");
        setYtChannel(ch);
      }
    } catch { setYtStatus(null); }
  }, []);

  const loadShorts = useCallback(async () => {
    try {
      const r = await api.get<{ shorts: ShortResult[]; count: number }>("/api/v5/shorts/list");
      setShorts(r.shorts);
    } catch { setShorts([]); }
  }, []);

  const loadJobs = useCallback(async () => {
    try {
      const r = await api.get<{ items: any[] }>("/api/jobs?limit=50");
      setJobs(r.items);
    } catch {}
  }, []);

  useEffect(() => {
    loadYouTube();
    loadShorts();
    loadJobs();
  }, [loadYouTube, loadShorts, loadJobs]);

  /* ━━━━━━━━━━ Actions ━━━━━━━━━━ */
  const connectYouTube = async () => {
    setConnecting(true);
    try {
      await api.post("/api/v5/youtube/auth/connect");
      await loadYouTube();
    } catch (e: any) {
      alert("Kết nối thất bại: " + e.message);
    }
    setConnecting(false);
  };

  const disconnectYouTube = async () => {
    if (!confirm("Xác nhận hủy kết nối YouTube?")) return;
    await api.post("/api/v5/youtube/auth/revoke");
    setYtChannel(null);
    await loadYouTube();
  };

  const generateShort = async () => {
    if (!topic.trim()) return alert("Nhập chủ đề video!");
    setGenerating(true);
    setGenStatus("Đang tạo script AI...");
    try {
      const result = await api.post<ShortResult>("/api/v5/shorts/generate", {
        topic: topic.trim(), voice, channel_niche: niche,
      });
      setGenStatus(result.status === "ready"
        ? `✅ Hoàn thành! "${result.title}" (${result.duration_sec.toFixed(0)}s)`
        : `❌ Lỗi: ${result.error}`
      );
      await loadShorts();
      setTopic("");
    } catch (e: any) {
      setGenStatus("❌ " + e.message);
    }
    setGenerating(false);
  };

  const uploadShort = async (jobId: string) => {
    setUploading(jobId);
    try {
      const r = await api.post<{ ok: boolean; url?: string; video_id?: string }>(
        "/api/v5/shorts/upload", { job_id: jobId, privacy_status: "public" }
      );
      if (r.ok) setGenStatus(`✅ Đã upload! ${r.url}`);
      await loadShorts();
    } catch (e: any) {
      setGenStatus("❌ Upload lỗi: " + e.message);
    }
    setUploading(null);
  };

  /* ━━━━━━━━━━ Stats ━━━━━━━━━━ */
  const readyCount = shorts.filter(s => s.status === "ready").length;
  const uploadedCount = shorts.filter(s => s.status === "uploaded").length;
  const jobStates = jobs.reduce((acc, j) => { acc[j.state] = (acc[j.state] || 0) + 1; return acc; }, {} as Record<string, number>);

  /* ━━━━━━━━━━ Render ━━━━━━━━━━ */
  return (
    <div className="page">
      {/* ── Header ── */}
      <div className="page-head">
        <h2>🎬 Trung tâm sản xuất</h2>
        <p>Tạo video Shorts tự động: AI Script → TTS Voice → Stock Footage → Upload YouTube — tất cả từ một nơi.</p>
      </div>

      {/* ── Stats ── */}
      <div className="stat-grid">
        <StatCard label="YouTube" value={ytStatus?.authenticated ? "✅ Kết nối" : "❌ Chưa"} />
        <StatCard label="Shorts sẵn sàng" value={readyCount} />
        <StatCard label="Đã upload" value={uploadedCount} />
        <StatCard label="Tổng Shorts" value={shorts.length} />
        <StatCard label="Jobs Pipeline" value={jobs.length} />
        <StatCard label="Videos kênh" value={ytChannel?.video_count || "—"} />
      </div>

      {/* ── Row 1: YouTube + Create ── */}
      <div className="grid-2">
        {/* YouTube Connection */}
        <Card title="📺 Kênh YouTube" right={
          ytStatus?.authenticated
            ? <span className="chip chip-done">Đã kết nối</span>
            : <span className="chip chip-failed">Chưa kết nối</span>
        }>
          {ytStatus?.authenticated && ytChannel?.ok ? (
            <div className="yt-channel-info">
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                {ytChannel.thumbnail && (
                  <img src={ytChannel.thumbnail} alt="" style={{ width: 48, height: 48, borderRadius: "50%" }} />
                )}
                <div>
                  <strong style={{ fontSize: 16 }}>{ytChannel.title}</strong>
                  <div className="text-sm text-muted">{ytChannel.custom_url || ytChannel.channel_id}</div>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 12 }}>
                <div className="mini-stat"><div className="mini-stat-value">{ytChannel.subscriber_count}</div><div className="mini-stat-label">Subscribers</div></div>
                <div className="mini-stat"><div className="mini-stat-value">{ytChannel.video_count}</div><div className="mini-stat-label">Videos</div></div>
                <div className="mini-stat"><div className="mini-stat-value">{ytChannel.view_count}</div><div className="mini-stat-label">Views</div></div>
              </div>
              <button className="btn btn-sm" onClick={disconnectYouTube}>Hủy kết nối</button>
            </div>
          ) : (
            <div>
              <p className="text-muted" style={{ marginBottom: 12 }}>
                Kết nối tài khoản YouTube để upload video trực tiếp từ dashboard.
              </p>
              <button className="btn btn-primary" onClick={connectYouTube} disabled={connecting}>
                {connecting ? "⏳ Đang mở trình duyệt..." : "🔗 Kết nối YouTube"}
              </button>
              {!ytStatus?.configured && (
                <p className="text-sm text-muted" style={{ marginTop: 8 }}>
                  ⚠️ Chưa có file client_secret.json. Tải từ Google Cloud Console.
                </p>
              )}
            </div>
          )}
        </Card>

        {/* Shorts Creator */}
        <Card title="🎥 Tạo YouTube Short" right={
          genStatus ? <span className="chip chip-accent" style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis" }}>{genStatus}</span> : null
        }>
          <div className="form-grid">
            <div className="form-field" style={{ gridColumn: "span 2" }}>
              <label className="form-label">Chủ đề video</label>
              <input
                className="form-input"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="VD: Amazing Octopus Intelligence, Lion Hunting Strategies..."
                onKeyDown={(e) => e.key === "Enter" && !generating && generateShort()}
              />
            </div>
            <div className="form-field">
              <label className="form-label">Giọng đọc</label>
              <select className="form-input" value={voice} onChange={(e) => setVoice(e.target.value)}>
                <option value="nova">Nova (nữ, tự nhiên)</option>
                <option value="alloy">Alloy (trung tính)</option>
                <option value="echo">Echo (nam)</option>
                <option value="fable">Fable (kể chuyện)</option>
                <option value="onyx">Onyx (nam trầm)</option>
                <option value="shimmer">Shimmer (nữ nhẹ)</option>
              </select>
            </div>
            <div className="form-field">
              <label className="form-label">Niche kênh</label>
              <select className="form-input" value={niche} onChange={(e) => setNiche(e.target.value)}>
                <option value="animals">🐾 Animals</option>
                <option value="science">🔬 Science</option>
                <option value="history">📜 History</option>
                <option value="space">🚀 Space</option>
                <option value="technology">💻 Technology</option>
                <option value="nature">🌿 Nature</option>
              </select>
            </div>
          </div>
          <div className="form-actions" style={{ marginTop: 12 }}>
            <button className="btn btn-primary" onClick={generateShort} disabled={generating || !topic.trim()}>
              {generating ? "⏳ Đang tạo video... (30-60s)" : "🚀 Tạo Short"}
            </button>
          </div>
          <p style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>
            Pipeline: 📝 AI Script → 🎙️ TTS Voice → 🎬 Stock Footage → 📐 Compose → ✅ Sẵn sàng upload
          </p>
        </Card>
      </div>

      {/* ── History: Generated Shorts ── */}
      <Card title={`📋 Shorts đã tạo (${shorts.length})`}>
        {shorts.length === 0 ? (
          <p className="text-muted">Chưa có video nào. Nhập chủ đề ở trên và bấm "Tạo Short" để bắt đầu.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Tiêu đề</th>
                <th>Thời lượng</th>
                <th>Trạng thái</th>
                <th>YouTube</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {shorts.map((s) => (
                <tr key={s.job_id}>
                  <td className="mono">#{s.job_id}</td>
                  <td className="cell-title" title={s.title}>{s.title || "—"}</td>
                  <td>{s.duration_sec > 0 ? `${s.duration_sec.toFixed(0)}s` : "—"}</td>
                  <td>
                    <span className={`chip chip-sm chip-${s.status === "ready" ? "done" : s.status === "uploaded" ? "uploaded" : s.status === "error" ? "failed" : "queued"}`}>
                      {s.status === "ready" ? "✅ Sẵn sàng" : s.status === "uploaded" ? "📺 Đã upload" : s.status === "error" ? "❌ Lỗi" : s.status}
                    </span>
                  </td>
                  <td>
                    {s.youtube_url ? (
                      <a href={s.youtube_url} target="_blank" rel="noreferrer" className="link-external">
                        🔗 Xem trên YouTube
                      </a>
                    ) : "—"}
                  </td>
                  <td>
                    {s.status === "ready" && ytStatus?.authenticated && (
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => uploadShort(s.job_id)}
                        disabled={uploading === s.job_id}
                      >
                        {uploading === s.job_id ? "⏳ ..." : "📤 Upload"}
                      </button>
                    )}
                    {s.status === "error" && (
                      <span className="text-sm text-muted" title={s.error}>⚠️ {s.error?.slice(0, 40)}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* ── Old Pipeline Jobs ── */}
      {jobs.length > 0 && (
        <Card title={`📦 Pipeline Jobs cũ (${jobs.length})`}>
          <table className="data-table">
            <thead><tr><th>ID</th><th>Kênh</th><th>Tiêu đề</th><th>Trạng thái</th><th>Ngày tạo</th></tr></thead>
            <tbody>
              {jobs.slice(0, 10).map((j) => (
                <tr key={j.id}>
                  <td className="mono">#{j.id}</td>
                  <td>{j.channel}</td>
                  <td className="cell-title">{j.title_seed}</td>
                  <td><span className={`chip chip-sm chip-${j.state}`}>{j.state}</span></td>
                  <td className="text-sm">{j.created_at?.slice(0, 16)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
