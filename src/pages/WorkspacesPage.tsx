import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface Workspace {
  id: number; name: string; channel_name: string;
  session_status: string; storage_path: string; last_verified_at: string | null;
  created_at: string;
}

const STATUS_VI: Record<string, string> = {
  new: "Mới tạo", active: "Đang hoạt động", expired: "Hết hạn", error: "Lỗi",
};

export default function WorkspacesPage() {
  const [items, setItems] = useState<Workspace[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [newName, setNewName] = useState("");
  const [newChannel, setNewChannel] = useState("");
  const [msg, setMsg] = useState("");

  const load = () => {
    api.get<{ items: Workspace[] }>("/api/v2/workspaces").then((r) => setItems(r.items)).catch(() => setItems([]));
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!newName.trim()) return;
    try {
      const res = await api.post<{ message: string }>("/api/v2/workspaces", { name: newName, channel_name: newChannel || null });
      setMsg(res.message);
      setNewName("");
      setNewChannel("");
      load();
    } catch (e: any) { setMsg(e.message); }
  };

  const launch = async (id: number) => {
    try {
      const res = await api.post<{ message: string }>(`/api/v2/workspaces/${id}/launch`);
      setMsg(res.message);
    } catch (e: any) { setMsg(e.message); }
  };

  const statusColor = (s: string) =>
    s === "active" ? "chip-done" : s === "expired" ? "chip-failed" : s === "new" ? "chip-queued" : "";

  return (
    <div className="page">
      <div className="page-head">
        <h2>Trình duyệt riêng biệt</h2>
        <p>Mỗi kênh có trình duyệt riêng với cookies, phiên đăng nhập và dữ liệu tách biệt hoàn toàn.</p>
      </div>

      <div className="grid-2">
        <Card title="Danh sách workspace">
          <div className="list-stack">
            {items.map((w) => (
              <div key={w.id} className="list-item">
                <div className="list-item-main">
                  <strong>{w.name}</strong>
                  <span className={`chip chip-sm ${statusColor(w.session_status)}`}>{STATUS_VI[w.session_status] || w.session_status}</span>
                </div>
                <div className="list-item-meta">
                  <span>Kênh: {w.channel_name || "–"}</span>
                  <span>Thư mục: <code>{w.storage_path}</code></span>
                </div>
                <div className="list-item-actions">
                  <button className="btn btn-sm" onClick={() => launch(w.id)}>🌐 Mở trình duyệt</button>
                </div>
              </div>
            ))}
            {items.length === 0 && <p className="text-muted">Chưa có workspace nào. Tạo bên cạnh để bắt đầu.</p>}
          </div>
        </Card>

        <Card title="Tạo workspace mới" right={msg ? <span className="chip chip-accent">{msg}</span> : null}>
          <div className="form-grid">
            <div className="form-field">
              <label className="form-label">Tên workspace</label>
              <input className="form-input" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="VD: kenh-space-facts" />
            </div>
            <div className="form-field">
              <label className="form-label">Gắn với kênh (tùy chọn)</label>
              <select className="form-input" value={newChannel} onChange={(e) => setNewChannel(e.target.value)}>
                <option value="">Không gắn kênh</option>
                {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
              </select>
            </div>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={create}>Tạo workspace</button>
          </div>
        </Card>
      </div>
    </div>
  );
}
