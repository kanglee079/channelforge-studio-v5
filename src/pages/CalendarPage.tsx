import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

const STATE_VI: Record<string, string> = {
  queued: "Chờ xử lý", processing: "Đang chạy", done: "Hoàn thành",
  uploaded: "Đã upload", failed: "Thất bại", retry: "Thử lại",
};

export default function CalendarPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);

  useEffect(() => {
    api.get<{ items: any[] }>("/api/jobs?limit=100").then((r) => setJobs(r.items)).catch(() => {});
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
  }, []);

  const doneJobs = jobs.filter((j) => j.state === "done" || j.state === "uploaded");
  const queuedJobs = jobs.filter((j) => j.state === "queued");

  const byChannel = jobs.reduce((acc, j) => {
    acc[j.channel] = acc[j.channel] || [];
    acc[j.channel].push(j);
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div className="page">
      <div className="page-head">
        <h2>Lịch đăng video</h2>
        <p>Lên lịch upload, theo dõi trạng thái và quản lý hàng đợi theo từng kênh.</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Sẵn sàng upload" value={doneJobs.length} />
        <StatCard label="Đang chờ xử lý" value={queuedJobs.length} />
        <StatCard label="Số kênh" value={channels.length} />
      </div>

      {Object.entries(byChannel).map(([ch, chJobs]) => {
        const channelJobs = chJobs as any[];
        return (
        <Card key={ch} title={`📺 ${ch}`} right={<span className="chip">{channelJobs.length} jobs</span>}>
          <table className="data-table">
            <thead><tr><th>ID</th><th>Tiêu đề</th><th>Trạng thái</th><th>Ngày tạo</th></tr></thead>
            <tbody>
              {channelJobs.slice(0, 20).map((j) => (
                <tr key={j.id}>
                  <td className="mono">#{j.id}</td>
                  <td className="cell-title">{j.title_seed}</td>
                  <td><span className={`chip chip-sm chip-${j.state}`}>{STATE_VI[j.state] || j.state}</span></td>
                  <td className="text-sm">{j.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        );
      })}
    </div>
  );
}
