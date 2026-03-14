import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

interface DashboardData {
  total_jobs: number;
  channels_count: number;
  job_counts: Record<string, number>;
  recent_jobs: { id: number; channel: string; title_seed: string; state: string }[];
  channels: { name: string; niche: string; language: string; default_video_format: string; upload_enabled: boolean }[];
}

const STATE_VI: Record<string, string> = {
  queued: "Chờ xử lý", processing: "Đang chạy", done: "Hoàn thành",
  uploaded: "Đã upload", failed: "Thất bại", retry: "Thử lại",
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => { api.get<DashboardData>("/api/dashboard").then(setData).catch(console.error); }, []);

  return (
    <div className="page">
      <div className="page-head">
        <h2>Tổng quan</h2>
        <p>Theo dõi hoạt động sản xuất video, hàng đợi và kênh YouTube của bạn.</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Tổng Jobs" value={data?.total_jobs ?? "–"} />
        <StatCard label="Số kênh" value={data?.channels_count ?? "–"} />
        <StatCard label="Chờ xử lý" value={data?.job_counts?.queued ?? 0} />
        <StatCard label="Hoàn thành" value={data?.job_counts?.done ?? 0} />
        <StatCard label="Đã upload" value={data?.job_counts?.uploaded ?? 0} />
        <StatCard label="Thất bại" value={data?.job_counts?.failed ?? 0} />
      </div>

      <div className="grid-2">
        <Card title="Jobs gần đây">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Kênh</th><th>Tiêu đề</th><th>Trạng thái</th></tr></thead>
            <tbody>
              {(data?.recent_jobs ?? []).map((r) => (
                <tr key={r.id}>
                  <td className="mono">#{r.id}</td>
                  <td>{r.channel}</td>
                  <td>{r.title_seed}</td>
                  <td><span className={`chip chip-${r.state}`}>{STATE_VI[r.state] || r.state}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="Danh sách kênh">
          <div className="list-stack">
            {(data?.channels ?? []).map((c) => (
              <div key={c.name} className="list-item">
                <strong>{c.name}</strong>
                <span className="text-muted">{c.niche}</span>
                <span className="text-sm">{c.language} · {c.default_video_format}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
