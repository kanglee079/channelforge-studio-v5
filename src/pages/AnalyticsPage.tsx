import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

const STATE_VI: Record<string, string> = {
  queued: "Chờ xử lý", processing: "Đang chạy", done: "Hoàn thành",
  uploaded: "Đã upload", failed: "Thất bại", retry: "Thử lại",
};

export default function AnalyticsPage() {
  const [jobs, setJobs] = useState<any[]>([]);

  useEffect(() => {
    api.get<{ items: any[] }>("/api/jobs?limit=200").then((r) => setJobs(r.items)).catch(() => {});
  }, []);

  const states = jobs.reduce((acc, j) => { acc[j.state] = (acc[j.state] || 0) + 1; return acc; }, {} as Record<string, number>);
  const byChannel = jobs.reduce((acc, j) => { acc[j.channel] = (acc[j.channel] || 0) + 1; return acc; }, {} as Record<string, number>);

  const completionRate = jobs.length > 0 ? Math.round(((states.done || 0) / jobs.length) * 100) : 0;
  const failureRate = jobs.length > 0 ? Math.round(((states.failed || 0) / jobs.length) * 100) : 0;

  return (
    <div className="page">
      <div className="page-head">
        <h2>Thống kê</h2>
        <p>Theo dõi hiệu suất pipeline, tỷ lệ thành công, và phân tích sản lượng theo kênh.</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Tổng Jobs" value={jobs.length} />
        <StatCard label="Hoàn thành" value={states.done || 0} sub={`${completionRate}% tỷ lệ`} />
        <StatCard label="Thất bại" value={states.failed || 0} sub={`${failureRate}% tỷ lệ`} />
        <StatCard label="Đang chờ" value={(states.queued || 0) + (states.retry || 0)} />
      </div>

      <div className="grid-2">
        <Card title="Phân tích theo kênh">
          <table className="data-table">
            <thead><tr><th>Kênh</th><th>Số jobs</th><th>Tỷ lệ</th></tr></thead>
            <tbody>
              {Object.entries(byChannel)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([ch, count]) => (
                  <tr key={ch}>
                    <td><strong>{ch}</strong></td>
                    <td>{count as number}</td>
                    <td>{Math.round(((count as number) / jobs.length) * 100)}%</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>

        <Card title="Phân tích theo trạng thái">
          <table className="data-table">
            <thead><tr><th>Trạng thái</th><th>Số lượng</th><th>Tỷ lệ</th></tr></thead>
            <tbody>
              {Object.entries(states)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([state, count]) => (
                  <tr key={state}>
                    <td><span className={`chip chip-sm chip-${state}`}>{STATE_VI[state] || state}</span></td>
                    <td>{count as number}</td>
                    <td>{Math.round(((count as number) / jobs.length) * 100)}%</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
