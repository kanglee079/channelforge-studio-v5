import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface ReviewItem {
  id: number; review_type: string; object_type: string; object_id: number;
  channel_name: string; priority: number; reason_text: string;
  score: number; status: string; created_at: string;
}

interface Summary { open: number; resolved_today: number; by_type: Record<string, number>; }

const TYPE_VI: Record<string, string> = {
  scene_low_conf: "Scene thấp", source_risk: "Nguồn rủi ro",
  policy_conflict: "Vi phạm chính sách", upload_approval: "Duyệt upload",
  budget_anomaly: "Chi phí bất thường", asset_repeat: "Asset trùng lặp",
};

export default function ReviewCenterPage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [filter, setFilter] = useState<"open" | "approved" | "rejected">("open");
  const [msg, setMsg] = useState("");

  const load = () => {
    api.get<{ items: ReviewItem[] }>(`/api/v5/review?status=${filter}`).then((r) => setItems(r.items)).catch(() => setItems([]));
    api.get<Summary>("/api/v5/review/summary").then((r) => setSummary(r)).catch(() => {});
  };
  useEffect(() => { load(); }, [filter]);

  const resolve = async (id: number, status: string) => {
    try {
      const res = await api.post<{ message: string }>(`/api/v5/review/${id}/resolve`, { status });
      setMsg(res.message); load();
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Trung tâm duyệt</h2>
        <p>Quản lý các mục cần review: scene confidence thấp, nguồn rủi ro, budget anomaly.</p>
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      {summary && (
        <div className="stat-grid">
          <div className="stat-card"><div className="stat-label">CHỜ DUYỆT</div><div className="stat-value">{summary.open}</div></div>
          <div className="stat-card"><div className="stat-label">DUYỆT HÔM NAY</div><div className="stat-value">{summary.resolved_today}</div></div>
          {Object.entries(summary.by_type).map(([type, count]) => (
            <div key={type} className="stat-card"><div className="stat-label">{TYPE_VI[type] || type}</div><div className="stat-value">{count}</div></div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 8, margin: "16px 0" }}>
        {(["open", "approved", "rejected"] as const).map((s) => (
          <button key={s} className={`btn btn-sm ${filter === s ? "btn-primary" : ""}`} onClick={() => setFilter(s)}>
            {s === "open" ? "Chờ duyệt" : s === "approved" ? "Đã duyệt" : "Từ chối"} ({items.length})
          </button>
        ))}
      </div>

      <Card title={`Review Items (${items.length})`}>
        {items.length > 0 ? (
          <table className="data-table">
            <thead><tr><th>LOẠI</th><th>KÊNH</th><th>LÝ DO</th><th>ĐIỂM</th><th>THỜI GIAN</th><th>HÀNH ĐỘNG</th></tr></thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id}>
                  <td><span className="chip chip-sm">{TYPE_VI[r.review_type] || r.review_type}</span></td>
                  <td>{r.channel_name || "–"}</td>
                  <td>{r.reason_text || "–"}</td>
                  <td>{r.score > 0 ? `${(r.score * 100).toFixed(0)}%` : "–"}</td>
                  <td style={{ fontSize: "0.8rem" }}>{new Date(r.created_at).toLocaleDateString("vi-VN")}</td>
                  <td>
                    {r.status === "open" && (
                      <div style={{ display: "flex", gap: 4 }}>
                        <button className="btn btn-sm" onClick={() => resolve(r.id, "approved")}>✅</button>
                        <button className="btn btn-sm" onClick={() => resolve(r.id, "rejected")}>❌</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="text-muted">Không có mục nào cần review.</p>}
      </Card>
    </div>
  );
}
