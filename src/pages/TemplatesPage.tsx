import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface Template {
  id: number; name: string; category: string; description: string;
  config: Record<string, any>; is_builtin: number; created_at: string;
}

const CATEGORY_VI: Record<string, string> = { shorts: "Video ngắn", long: "Video dài" };
const CONFIG_VI: Record<string, string> = {
  duration_range: "Thời lượng (giây)", resolution: "Độ phân giải", fps: "FPS",
  subtitle_style: "Kiểu phụ đề", subtitle_font_size: "Cỡ chữ phụ đề",
  subtitle_color: "Màu phụ đề", subtitle_bg: "Nền phụ đề", footage_style: "Kiểu hình ảnh",
  min_clips: "Clip tối thiểu", max_clips: "Clip tối đa", hook_duration_sec: "Hook (giây)",
  cta_placement: "Vị trí CTA", voice_pacing: "Tốc độ giọng", transition: "Hiệu ứng chuyển",
  chapter_markers: "Đánh dấu chương", list_format: "Kiểu danh sách", item_duration_sec: "Mỗi item (giây)",
  number_overlay: "Overlay số", bg_colors: "Màu nền", text_animation: "Hiệu ứng chữ",
  broll_change_interval_sec: "Đổi B-roll (giây)",
};

export default function TemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [selected, setSelected] = useState<Template | null>(null);
  const [filter, setFilter] = useState("");
  const [msg, setMsg] = useState("");

  const load = () => api.get<{ items: Template[] }>("/api/v2/templates").then((r) => setItems(r.items)).catch(() => {});
  useEffect(() => { load(); }, []);

  const seed = async () => {
    const res = await api.post<{ message: string }>("/api/v2/templates/seed");
    setMsg(res.message);
    load();
  };

  const filtered = filter ? items.filter((t) => t.category === filter) : items;

  return (
    <div className="page">
      <div className="page-head">
        <h2>Mẫu video</h2>
        <p>Các bộ mẫu cấu hình sẵn cho từng loại video: Shorts, documentary, slideshow, infographic.</p>
        <div className="page-head-actions">
          <button className="btn" onClick={seed}>🔄 Tạo mẫu mặc định</button>
          {msg && <span className="chip chip-accent">{msg}</span>}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button className={`btn ${!filter ? "btn-primary" : ""}`} onClick={() => setFilter("")}>Tất cả ({items.length})</button>
        <button className={`btn ${filter === "shorts" ? "btn-primary" : ""}`} onClick={() => setFilter("shorts")}>Video ngắn</button>
        <button className={`btn ${filter === "long" ? "btn-primary" : ""}`} onClick={() => setFilter("long")}>Video dài</button>
      </div>

      <div className="grid-2">
        <Card title="Bộ mẫu">
          <div className="list-stack">
            {filtered.map((t) => (
              <div key={t.id} className="list-item clickable" onClick={() => setSelected(t)}>
                <div className="list-item-main">
                  <strong>{t.name}</strong>
                  <span className="chip chip-sm">{CATEGORY_VI[t.category] || t.category}</span>
                  {t.is_builtin ? <span className="chip chip-sm chip-accent">có sẵn</span> : null}
                </div>
                <div className="list-item-meta"><span>{t.description}</span></div>
              </div>
            ))}
            {filtered.length === 0 && <p className="text-muted">Chưa có mẫu nào. Nhấn "Tạo mẫu mặc định" để khởi tạo.</p>}
          </div>
        </Card>

        {selected && (
          <Card title={`Chi tiết: ${selected.name}`}>
            <div className="list-item-meta" style={{ marginBottom: 12 }}>
              <span><strong>Loại:</strong> {CATEGORY_VI[selected.category] || selected.category}</span>
              <span><strong>Có sẵn:</strong> {selected.is_builtin ? "Có" : "Không"}</span>
            </div>
            <p style={{ marginBottom: 12, color: "var(--text-muted)" }}>{selected.description}</p>
            <table className="data-table">
              <thead><tr><th>Thuộc tính</th><th>Giá trị</th></tr></thead>
              <tbody>
                {Object.entries(selected.config || {}).map(([k, v]) => (
                  <tr key={k}>
                    <td>{CONFIG_VI[k] || k}</td>
                    <td>{typeof v === "object" ? JSON.stringify(v) : String(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </div>
  );
}
