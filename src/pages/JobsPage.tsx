import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

const STATE_VI: Record<string, string> = {
  queued: "Chờ xử lý", processing: "Đang chạy", done: "Hoàn thành",
  uploaded: "Đã upload", failed: "Thất bại", retry: "Thử lại",
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState("");

  // Enqueue form
  const [enqProfile, setEnqProfile] = useState("");
  const [enqCount, setEnqCount] = useState("3");
  const [enqNiche, setEnqNiche] = useState("");
  const [enqFormat, setEnqFormat] = useState("shorts");
  const [enqMsg, setEnqMsg] = useState("");
  const [enqueuing, setEnqueuing] = useState(false);

  const load = () => {
    api.get<{ items: any[] }>("/api/jobs?limit=50").then((r) => setJobs(r.items)).catch(console.error);
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const runWorker = async () => {
    setRunning(true); setRunMsg("Đang xử lý...");
    try {
      const res = await api.post<{ message: string }>("/api/workers/run", { limit: 1 });
      setRunMsg(res.message);
      load();
    } catch (e: any) { setRunMsg(`Lỗi: ${e.message}`); }
    setRunning(false);
  };

  const enqueue = async () => {
    if (!enqProfile) { setEnqMsg("Chọn kênh trước"); return; }
    setEnqueuing(true); setEnqMsg("Đang thêm vào hàng đợi...");
    try {
      const res = await api.post<{ message: string }>("/api/jobs/enqueue", {
        profile: enqProfile, count: Number(enqCount),
        niche: enqNiche || undefined, format: enqFormat,
      });
      setEnqMsg(`✅ ${res.message}`);
      load();
    } catch (e: any) { setEnqMsg(`❌ ${e.message}`); }
    setEnqueuing(false);
  };

  const states = jobs.reduce((acc, j) => { acc[j.state] = (acc[j.state] || 0) + 1; return acc; }, {} as Record<string, number>);

  return (
    <div className="page">
      <div className="page-head">
        <h2>Hàng đợi sản xuất</h2>
        <p>Thêm jobs mới, xử lý pipeline, và theo dõi tiến trình sản xuất video.</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Tổng" value={jobs.length} />
        <StatCard label="Chờ xử lý" value={states.queued || 0} />
        <StatCard label="Đang chạy" value={states.processing || 0} />
        <StatCard label="Hoàn thành" value={states.done || 0} />
        <StatCard label="Thất bại" value={states.failed || 0} />
      </div>

      <div className="grid-2">
        <Card title="Thêm jobs mới" right={enqMsg ? <span className="chip chip-accent">{enqMsg}</span> : null}>
          <div className="form-grid">
            <div className="form-field">
              <label className="form-label">Kênh *</label>
              <select className="form-input" value={enqProfile} onChange={(e) => setEnqProfile(e.target.value)}>
                <option value="">Chọn kênh</option>
                {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label className="form-label">Số video cần tạo</label>
              <input className="form-input" type="number" value={enqCount} onChange={(e) => setEnqCount(e.target.value)} min="1" max="20" />
            </div>
            <div className="form-field">
              <label className="form-label">Niche (tùy chọn, ghi đè)</label>
              <input className="form-input" value={enqNiche} onChange={(e) => setEnqNiche(e.target.value)} placeholder="Để trống = dùng niche của kênh" />
            </div>
            <div className="form-field">
              <label className="form-label">Định dạng</label>
              <select className="form-input" value={enqFormat} onChange={(e) => setEnqFormat(e.target.value)}>
                <option value="shorts">Shorts (dọc)</option>
                <option value="long">Long-form (ngang)</option>
              </select>
            </div>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={enqueue} disabled={enqueuing}>
              {enqueuing ? "Đang thêm..." : "📥 Thêm vào hàng đợi"}
            </button>
          </div>
        </Card>

        <Card title="Chạy Pipeline" right={runMsg ? <span className="chip chip-accent">{runMsg}</span> : null}>
          <p style={{ color: "var(--text-muted)", marginBottom: 12 }}>
            Xử lý 1 job từ hàng đợi: nghiên cứu → viết script → TTS → tìm hình → render video.
          </p>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={runWorker} disabled={running}>
              {running ? "⏳ Đang xử lý..." : "▶ Chạy 1 Job"}
            </button>
            <button className="btn" onClick={load}>🔄 Làm mới</button>
          </div>
        </Card>
      </div>

      <Card title={`Tất cả Jobs (${jobs.length})`}>
        <table className="data-table">
          <thead><tr><th>ID</th><th>Kênh</th><th>Tiêu đề</th><th>Trạng thái</th><th>Lần thử</th><th>Lỗi</th><th>Ngày tạo</th></tr></thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td className="mono">#{j.id}</td>
                <td>{j.channel}</td>
                <td className="cell-title">{j.title_seed}</td>
                <td><span className={`chip chip-sm chip-${j.state}`}>{STATE_VI[j.state] || j.state}</span></td>
                <td>{j.retries}</td>
                <td className="cell-title text-sm" style={{ maxWidth: 200, color: j.error ? "var(--red)" : "var(--text-muted)" }}>
                  {j.error ? j.error.slice(0, 80) : "–"}
                </td>
                <td className="text-sm">{j.created_at?.slice(0, 16)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
