import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface HealthInfo {
  storage_exists: boolean;
  has_profile: boolean;
  has_downloads: boolean;
}

interface Workspace {
  id: number; name: string; channel_name: string;
  session_status: string; storage_path: string;
  proxy_config?: string;
  last_login_at: string | null; last_verified_at: string | null;
  created_at: string; health?: HealthInfo;
}

interface ProxyProfile {
  id: number; name: string; protocol: string; server: string; port: number;
  status: string; last_tested_at: string | null; notes: string;
}

interface HealthEvent {
  id: number; event_type: string; severity: string; message: string; created_at: string;
}

const STATUS_VI: Record<string, string> = {
  new: "Mới tạo", active: "Đang hoạt động", expired: "Hết hạn", error: "Lỗi",
  degraded: "Suy giảm", archived: "Đã lưu trữ",
};

const SEV_COLOR: Record<string, string> = {
  info: "chip-done", warning: "chip-retry", error: "chip-failed", critical: "chip-failed",
};

export default function WorkspacesPage() {
  const [items, setItems] = useState<Workspace[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [proxies, setProxies] = useState<ProxyProfile[]>([]);
  const [newName, setNewName] = useState("");
  const [newChannel, setNewChannel] = useState("");
  const [msg, setMsg] = useState("");
  const [tab, setTab] = useState<"workspaces" | "proxy" | "health">("workspaces");
  const [healthEvents, setHealthEvents] = useState<HealthEvent[]>([]);
  const [selectedWs, setSelectedWs] = useState<number | null>(null);

  // Proxy form
  const [pName, setPName] = useState("");
  const [pServer, setPServer] = useState("");
  const [pPort, setPPort] = useState("8080");
  const [pProtocol, setPProtocol] = useState("http");

  const load = () => {
    api.get<{ items: Workspace[] }>("/api/v2/workspaces").then((r) => setItems(r.items)).catch(() => setItems([]));
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
    api.get<{ items: ProxyProfile[] }>("/api/v2/workspaces/proxy-profiles").then((r) => setProxies(r.items)).catch(() => setProxies([]));
  };
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!newName.trim()) return;
    try {
      const res = await api.post<{ message: string }>("/api/v2/workspaces", { name: newName, channel_name: newChannel || null });
      setMsg(res.message); setNewName(""); setNewChannel(""); load();
    } catch (e: any) { setMsg(e.message); }
  };

  const launch = async (id: number) => {
    setMsg("Đang mở trình duyệt...");
    try {
      const res = await api.post<{ message: string }>(`/api/v2/workspaces/${id}/launch`);
      setMsg(res.message);
    } catch (e: any) { setMsg(e.message); }
  };

  const healthCheck = async (id: number) => {
    setMsg("Đang kiểm tra...");
    try {
      const res = await api.post<{ overall: string; checks: any[] }>(`/api/v2/workspaces/${id}/healthcheck`);
      setMsg(`Sức khỏe: ${res.overall} (${res.checks.filter((c: any) => c.passed).length}/${res.checks.length} passed)`);
      load();
    } catch (e: any) { setMsg(e.message); }
  };

  const archive = async (id: number) => {
    try {
      const res = await api.post<{ message: string }>(`/api/v2/workspaces/${id}/archive`);
      setMsg(res.message); load();
    } catch (e: any) { setMsg(e.message); }
  };

  const restore = async (id: number) => {
    try {
      const res = await api.post<{ message: string }>(`/api/v2/workspaces/${id}/restore`);
      setMsg(res.message); load();
    } catch (e: any) { setMsg(e.message); }
  };

  const clearTemp = async (id: number) => {
    try {
      const res = await api.post<{ message: string; cleared: number }>(`/api/v2/workspaces/${id}/clear-temp`);
      setMsg(res.message);
    } catch (e: any) { setMsg(e.message); }
  };

  const createProxy = async () => {
    if (!pName.trim() || !pServer.trim()) return;
    try {
      const res = await api.post<{ message: string }>("/api/v2/workspaces/proxy-profiles", {
        name: pName, server: pServer, port: parseInt(pPort), protocol: pProtocol,
      });
      setMsg(res.message); setPName(""); setPServer(""); load();
    } catch (e: any) { setMsg(e.message); }
  };

  const testProxy = async (id: number) => {
    setMsg("Đang test proxy...");
    try {
      const res = await api.post<{ message: string }>(`/api/v2/workspaces/proxy-profiles/${id}/test`);
      setMsg(res.message); load();
    } catch (e: any) { setMsg(e.message); }
  };

  const loadHealthEvents = async (wsId: number) => {
    setSelectedWs(wsId); setTab("health");
    try {
      const res = await api.get<{ items: HealthEvent[] }>(`/api/v2/workspaces/${wsId}/health-events`);
      setHealthEvents(res.items);
    } catch { setHealthEvents([]); }
  };

  const statusColor = (s: string) =>
    s === "active" ? "chip-done" : s === "degraded" ? "chip-retry" : s === "archived" ? "" : s === "new" ? "chip-queued" : "chip-failed";

  return (
    <div className="page">
      <div className="page-head">
        <h2>Trình duyệt & Workspace</h2>
        <p>Mỗi kênh có trình duyệt riêng, proxy riêng, phiên đăng nhập tách biệt hoàn toàn.</p>
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button className={`btn btn-sm ${tab === "workspaces" ? "btn-primary" : ""}`} onClick={() => setTab("workspaces")}>
          Workspace ({items.length})
        </button>
        <button className={`btn btn-sm ${tab === "proxy" ? "btn-primary" : ""}`} onClick={() => setTab("proxy")}>
          Proxy ({proxies.length})
        </button>
        {selectedWs && (
          <button className={`btn btn-sm ${tab === "health" ? "btn-primary" : ""}`} onClick={() => setTab("health")}>
            Nhật ký sức khỏe
          </button>
        )}
      </div>

      {/* ── WORKSPACES TAB ── */}
      {tab === "workspaces" && (
        <div className="grid-2">
          <Card title="Danh sách workspace">
            <div className="list-stack">
              {items.map((w) => (
                <div key={w.id} className="list-item">
                  <div className="list-item-main">
                    <strong>{w.name}</strong>
                    <span className={`chip chip-sm ${statusColor(w.session_status)}`}>
                      {STATUS_VI[w.session_status] || w.session_status}
                    </span>
                    {w.health && (
                      <span className={`chip chip-sm ${w.health.storage_exists && w.health.has_profile ? "chip-done" : "chip-retry"}`}>
                        {w.health.storage_exists && w.health.has_profile ? "✓ Đầy đủ" : "⚠ Thiếu dữ liệu"}
                      </span>
                    )}
                  </div>
                  <div className="list-item-meta">
                    <span>Kênh: {w.channel_name || "–"}</span>
                    <span>Proxy: {w.proxy_config || "Trực tiếp"}</span>
                    {w.last_login_at && <span>Đăng nhập cuối: {new Date(w.last_login_at).toLocaleDateString("vi-VN")}</span>}
                  </div>
                  <div className="list-item-actions" style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                    <button className="btn btn-sm" onClick={() => launch(w.id)}>🌐 Mở</button>
                    <button className="btn btn-sm" onClick={() => healthCheck(w.id)}>🩺 Kiểm tra</button>
                    <button className="btn btn-sm" onClick={() => clearTemp(w.id)}>🧹 Dọn temp</button>
                    <button className="btn btn-sm" onClick={() => loadHealthEvents(w.id)}>📋 Logs</button>
                    {w.session_status === "archived" ? (
                      <button className="btn btn-sm" onClick={() => restore(w.id)}>♻️ Khôi phục</button>
                    ) : (
                      <button className="btn btn-sm" onClick={() => archive(w.id)}>📦 Lưu trữ</button>
                    )}
                  </div>
                </div>
              ))}
              {items.length === 0 && <p className="text-muted">Chưa có workspace nào.</p>}
            </div>
          </Card>

          <Card title="Tạo workspace mới">
            <div className="form-grid">
              <div className="form-field">
                <label className="form-label">Tên workspace</label>
                <input className="form-input" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="VD: kenh-space-facts" />
              </div>
              <div className="form-field">
                <label className="form-label">Gắn với kênh</label>
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
      )}

      {/* ── PROXY TAB ── */}
      {tab === "proxy" && (
        <div className="grid-2">
          <Card title="Proxy Profiles">
            <div className="list-stack">
              {proxies.map((p) => (
                <div key={p.id} className="list-item">
                  <div className="list-item-main">
                    <strong>{p.name}</strong>
                    <span className={`chip chip-sm ${p.status === "active" ? "chip-done" : p.status === "failed" ? "chip-failed" : "chip-queued"}`}>
                      {p.status}
                    </span>
                  </div>
                  <div className="list-item-meta">
                    <span>{p.protocol}://{p.server}:{p.port}</span>
                    {p.last_tested_at && <span>Test cuối: {new Date(p.last_tested_at).toLocaleDateString("vi-VN")}</span>}
                  </div>
                  <div className="list-item-actions">
                    <button className="btn btn-sm" onClick={() => testProxy(p.id)}>🧪 Test</button>
                  </div>
                </div>
              ))}
              {proxies.length === 0 && <p className="text-muted">Chưa có proxy profile nào.</p>}
            </div>
          </Card>

          <Card title="Thêm proxy">
            <div className="form-grid">
              <div className="form-field">
                <label className="form-label">Tên</label>
                <input className="form-input" value={pName} onChange={(e) => setPName(e.target.value)} placeholder="VD: proxy-us-1" />
              </div>
              <div className="form-field">
                <label className="form-label">Giao thức</label>
                <select className="form-input" value={pProtocol} onChange={(e) => setPProtocol(e.target.value)}>
                  <option value="http">HTTP</option>
                  <option value="https">HTTPS</option>
                  <option value="socks5">SOCKS5</option>
                </select>
              </div>
              <div className="form-field">
                <label className="form-label">Server</label>
                <input className="form-input" value={pServer} onChange={(e) => setPServer(e.target.value)} placeholder="proxy.example.com" />
              </div>
              <div className="form-field">
                <label className="form-label">Port</label>
                <input className="form-input" type="number" value={pPort} onChange={(e) => setPPort(e.target.value)} />
              </div>
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={createProxy}>Thêm proxy</button>
            </div>
          </Card>
        </div>
      )}

      {/* ── HEALTH EVENTS TAB ── */}
      {tab === "health" && selectedWs && (
        <Card title={`Nhật ký sức khỏe — Workspace #${selectedWs}`}>
          <table className="data-table">
            <thead>
              <tr>
                <th>THỜI GIAN</th>
                <th>SỰ KIỆN</th>
                <th>MỨC ĐỘ</th>
                <th>CHI TIẾT</th>
              </tr>
            </thead>
            <tbody>
              {healthEvents.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.created_at).toLocaleString("vi-VN")}</td>
                  <td>{e.event_type}</td>
                  <td><span className={`chip chip-sm ${SEV_COLOR[e.severity] || ""}`}>{e.severity}</span></td>
                  <td>{e.message}</td>
                </tr>
              ))}
              {healthEvents.length === 0 && <tr><td colSpan={4} className="text-muted">Chưa có nhật ký sức khỏe nào</td></tr>}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
