import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface AuditEntry {
  id: number; action: string; entity_type: string; entity_id: number;
  details: string; created_at: string;
}

export default function LogsPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.get<{ items: AuditEntry[] }>("/api/v2/audit-logs?limit=100").then((r) => setLogs(r.items)).catch(() => setLogs([]));
    api.get<{ items: any[] }>("/api/jobs?limit=30").then((r) => setJobs(r.items)).catch(() => {});
  }, []);

  // Nếu chưa có audit log, hiện lịch sử jobs như thay thế
  const jobEntries = jobs.map((j) => ({
    id: j.id,
    action: j.state === "done" ? "job_done" : j.state === "failed" ? "job_failed" : j.state === "processing" ? "job_processing" : "job_queued",
    entity_type: "job",
    entity_id: j.id,
    details: `[${j.channel}] ${j.title_seed}${j.error ? " — Lỗi: " + j.error.slice(0, 100) : ""}`,
    created_at: j.updated_at || j.created_at,
  }));

  const allLogs = logs.length > 0 ? logs : jobEntries;
  const filtered = filter ? allLogs.filter((l) => l.action.includes(filter) || l.entity_type?.includes(filter)) : allLogs;

  const ACTION_VI: Record<string, string> = {
    job_done: "✅ Job hoàn thành", job_failed: "❌ Job thất bại",
    job_processing: "⏳ Job đang chạy", job_queued: "📥 Job thêm vào",
    workspace_create: "🌐 Tạo workspace", workspace_launch: "🚀 Mở trình duyệt",
    research_extract: "📚 Trích xuất", content_idea: "💡 Ý tưởng mới",
    script_generate: "🤖 Tạo script AI", template_seed: "🎨 Seed mẫu",
  };

  const ACTION_COLOR: Record<string, string> = {
    job_done: "chip-done", job_failed: "chip-failed",
    job_processing: "chip-queued", job_queued: "",
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Nhật ký hệ thống</h2>
        <p>Theo dõi toàn bộ hoạt động: pipeline, provider calls, workspace, upload.</p>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button className={`btn ${!filter ? "btn-primary" : ""}`} onClick={() => setFilter("")}>Tất cả ({allLogs.length})</button>
        <button className={`btn ${filter === "job_done" ? "btn-primary" : ""}`} onClick={() => setFilter("job_done")}>Hoàn thành</button>
        <button className={`btn ${filter === "job_failed" ? "btn-primary" : ""}`} onClick={() => setFilter("job_failed")}>Thất bại</button>
      </div>

      <Card title={`Nhật ký (${filtered.length})`}>
        <table className="data-table">
          <thead><tr><th>ID</th><th>Hành động</th><th>Chi tiết</th><th>Thời gian</th></tr></thead>
          <tbody>
            {filtered.map((l) => (
              <tr key={l.id}>
                <td className="mono">#{l.entity_id}</td>
                <td><span className={`chip chip-sm ${ACTION_COLOR[l.action] || ""}`}>{ACTION_VI[l.action] || l.action}</span></td>
                <td className="cell-title">{l.details}</td>
                <td className="text-sm">{l.created_at?.slice(0, 16)}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)", padding: 20 }}>Chưa có hoạt động nào. Chạy pipeline để xem nhật ký.</td></tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
