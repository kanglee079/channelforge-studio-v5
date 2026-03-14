import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

const STATE_VI: Record<string, string> = {
  queued: "Chờ xử lý", processing: "Đang chạy", done: "Hoàn thành",
  uploaded: "Đã upload", failed: "Thất bại", retry: "Thử lại",
};

export default function FactoryPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState("");
  const [profile, setProfile] = useState("");
  const [limit, setLimit] = useState("1");
  const [channels, setChannels] = useState<any[]>([]);
  const [content, setContent] = useState<any[]>([]);

  const load = () => {
    api.get<{ items: any[] }>("/api/jobs?limit=50").then((r) => setJobs(r.items)).catch(() => {});
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
    api.get<{ items: any[] }>("/api/content").then((r) => setContent(r.items)).catch(() => setContent([]));
  };
  useEffect(() => { load(); }, []);

  const runWorker = async () => {
    setRunning(true); setMsg("Đang chạy pipeline...");
    try {
      const body: any = { limit: Number(limit) };
      if (profile) body.profile = profile;
      const res = await api.post<{ message: string }>("/api/workers/run", body);
      setMsg(res.message);
      load();
    } catch (e: any) { setMsg(`Lỗi: ${e.message}`); }
    setRunning(false);
  };

  const states = jobs.reduce((acc, j) => { acc[j.state] = (acc[j.state] || 0) + 1; return acc; }, {} as Record<string, number>);

  return (
    <div className="page">
      <div className="page-head">
        <h2>Sản xuất video</h2>
        <p>Pipeline tự động: thêm job → nghiên cứu → viết script → TTS → tìm hình → render → xuất MP4.</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Tổng Jobs" value={jobs.length} />
        <StatCard label="Chờ xử lý" value={states.queued || 0} />
        <StatCard label="Đang chạy" value={states.processing || 0} />
        <StatCard label="Hoàn thành" value={states.done || 0} />
        <StatCard label="Thất bại" value={states.failed || 0} />
        <StatCard label="Video" value={content.length} />
      </div>

      <div className="grid-2">
        <Card title="Chạy Pipeline" right={msg ? <span className="chip chip-accent">{msg}</span> : null}>
          <div className="form-grid">
            <div className="form-field">
              <label className="form-label">Kênh (tùy chọn)</label>
              <select className="form-input" value={profile} onChange={(e) => setProfile(e.target.value)}>
                <option value="">Tất cả kênh</option>
                {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label className="form-label">Số jobs xử lý 1 lần</label>
              <input className="form-input" type="number" value={limit} onChange={(e) => setLimit(e.target.value)} min="1" max="10" />
            </div>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={runWorker} disabled={running}>
              {running ? "⏳ Đang xử lý..." : "▶ Chạy Pipeline"}
            </button>
          </div>
          <p style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
            Mỗi job tự động chạy: 🔍 Nghiên cứu → ✍️ Script → 🎙️ TTS → 🎞️ Footage → 🎬 Render → 📄 Phụ đề
          </p>
        </Card>

        <Card title="Video đã hoàn thành">
          <div className="list-stack">
            {content.map((c, i) => (
              <div key={i} className="list-item">
                <div className="list-item-main">
                  <strong>{c.title || c.slug}</strong>
                  <span className="chip chip-sm chip-done">xong</span>
                </div>
                <div className="list-item-meta">
                  <span>Kênh: {c.channel}</span>
                  {c.video && <span>📁 <code style={{ fontSize: 11 }}>{c.video}</code></span>}
                </div>
              </div>
            ))}
            {content.length === 0 && <p className="text-muted">Chưa có video hoàn thành. Thêm jobs ở trang "Hàng đợi" và chạy pipeline.</p>}
          </div>
        </Card>
      </div>

      <Card title={`Hàng đợi (${jobs.length} jobs)`}>
        <table className="data-table">
          <thead><tr><th>ID</th><th>Kênh</th><th>Tiêu đề</th><th>Trạng thái</th><th>Lần thử</th><th>Ngày tạo</th></tr></thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td className="mono">#{j.id}</td>
                <td>{j.channel}</td>
                <td className="cell-title">{j.title_seed}</td>
                <td><span className={`chip chip-sm chip-${j.state}`}>{STATE_VI[j.state] || j.state}</span></td>
                <td>{j.retries}</td>
                <td className="text-sm">{j.created_at?.slice(0, 16)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
