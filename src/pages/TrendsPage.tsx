import { useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

export default function TrendsPage() {
  const [niche, setNiche] = useState("");
  const [geo, setGeo] = useState("US");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const scan = async () => {
    if (!niche.trim()) return;
    setLoading(true); setMsg("Đang quét xu hướng...");
    try {
      const res = await api.post<{ items: any[] }>("/api/trends/scan", { niche, geo });
      setResults(res.items || []);
      setMsg(`Tìm thấy ${(res.items || []).length} xu hướng`);
    } catch (e: any) { setMsg(`Lỗi: ${e.message}`); }
    setLoading(false);
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Radar xu hướng</h2>
        <p>Quét xu hướng nội dung, tìm ý tưởng video phù hợp với niche của kênh.</p>
      </div>

      <Card title="Quét xu hướng" right={msg ? <span className="chip chip-accent">{msg}</span> : null}>
        <div className="inline-controls">
          <input className="form-input" value={niche} onChange={(e) => setNiche(e.target.value)}
            placeholder="VD: space facts, animal behavior, history..." style={{ flex: 2 }} />
          <input className="form-input" value={geo} onChange={(e) => setGeo(e.target.value)}
            placeholder="Quốc gia (mã ISO)" style={{ width: 80 }} />
          <button className="btn btn-primary" onClick={scan} disabled={loading}>
            {loading ? "Đang quét..." : "🔍 Quét"}
          </button>
        </div>
      </Card>

      {results.length > 0 && (
        <Card title={`Kết quả (${results.length})`}>
          <table className="data-table">
            <thead><tr><th>Chủ đề</th><th>Điểm nóng</th><th>Nguồn</th><th>Gợi ý</th></tr></thead>
            <tbody>
              {results.map((t, i) => (
                <tr key={i}>
                  <td className="cell-title"><strong>{t.topic || t.title}</strong></td>
                  <td>{t.score ?? "–"}</td>
                  <td><span className="chip chip-sm">{t.source || "google"}</span></td>
                  <td>{t.angle || t.suggestion || "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
