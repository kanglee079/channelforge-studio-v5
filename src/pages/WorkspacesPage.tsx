import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

/* ── Types ── */
interface Workspace {
  id: number; name: string; channel_name: string; session_status: string;
  proxy_config: string; storage_path: string; notes: string;
  last_login_at: string; last_verified_at: string;
  health?: { storage_exists: boolean; has_profile: boolean; has_downloads: boolean };
}
interface RuntimeState {
  workspace_id: number; runtime_status: string; browser_pid: number;
  context_attached: number; current_route_mode: string; current_outbound_ip: string;
  last_launch_at: string; last_seen_alive_at: string; last_error_message: string;
  in_registry?: boolean;
}
interface ProxyProfile { id: number; name: string; server: string; port: number; protocol: string; status: string; last_tested_at: string; }
interface PolicyEvent { id: number; workspace_id: number; job_type: string; policy_mode: string; decision: string; outbound_ip: string; created_at: string; }
interface SessionCheck { id: number; workspace_id: number; check_type: string; status: string; details_json: string; screenshot_path: string; created_at: string; }

/* ── Status colors ── */
const STATUS_COLORS: Record<string, string> = {
  running: "#22c55e", upload_ready: "#22c55e", active: "#22c55e",
  launching: "#f59e0b", verifying: "#f59e0b", closing: "#f59e0b",
  stopped: "#6b7280", inactive: "#6b7280", new: "#6b7280",
  login_required: "#f97316", degraded: "#ef4444", blocked: "#dc2626", crashed: "#dc2626",
};

const POLICY_COLORS: Record<string, string> = {
  DIRECT: "#22c55e", WORKSPACE_ROUTE: "#3b82f6", BLOCK: "#ef4444",
};

export default function WorkspacesPage() {
  const [tab, setTab] = useState<"grid" | "routes" | "policy" | "sessions">("grid");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [runtimes, setRuntimes] = useState<RuntimeState[]>([]);
  const [proxies, setProxies] = useState<ProxyProfile[]>([]);
  const [events, setEvents] = useState<PolicyEvent[]>([]);
  const [sessionChecks, setSessionChecks] = useState<SessionCheck[]>([]);
  const [selWs, setSelWs] = useState<number>(0);
  const [loading, setLoading] = useState("");

  const fetchAll = () => {
    api.get<{ items: Workspace[] }>("/api/v2/workspaces").then(d => setWorkspaces(d.items)).catch(() => {});
    api.get<{ items: RuntimeState[] }>("/api/v2/workspaces/runtime/all").then(d => setRuntimes(d.items)).catch(() => setRuntimes([]));
    api.get<{ items: ProxyProfile[] }>("/api/v2/workspaces/proxy-profiles").then(d => setProxies(d.items)).catch(() => {});
    api.get<{ items: PolicyEvent[] }>("/api/v2/workspaces/network-events/all").then(d => setEvents(d.items)).catch(() => setEvents([]));
  };
  useEffect(() => { fetchAll(); const iv = setInterval(fetchAll, 10000); return () => clearInterval(iv); }, []);

  const getRuntime = (wsId: number) => runtimes.find(r => r.workspace_id === wsId);

  const doAction = async (wsId: number, action: string) => {
    setLoading(`${action}-${wsId}`);
    try {
      await api.post(`/api/v2/workspaces/${wsId}/${action}`);
      setTimeout(fetchAll, 500);
    } catch {}
    setLoading("");
  };

  const loadSessionChecks = (wsId: number) => {
    setSelWs(wsId);
    api.get<{ items: SessionCheck[] }>(`/api/v2/workspaces/${wsId}/session-checks`).then(d => setSessionChecks(d.items)).catch(() => setSessionChecks([]));
  };

  const TABS = [
    { key: "grid", label: "🖥️ Workspaces" },
    { key: "routes", label: "🔀 Route Profiles" },
    { key: "policy", label: "📡 Policy Events" },
    { key: "sessions", label: "🔐 Session Checks" },
  ] as const;

  return (
    <div>
      <h2>Workspace Supervisor</h2>
      <p className="text-muted">Quản lý lifecycle, network policy, session verification cho từng channel workspace.</p>

      {/* Tab bar */}
      <div className="tab-bar" style={{ marginBottom: 16 }}>
        {TABS.map(t => (
          <button key={t.key} className={`tab-btn${tab === t.key ? " active" : ""}`} onClick={() => setTab(t.key as typeof tab)}>{t.label}</button>
        ))}
      </div>

      {/* ── GRID TAB ── */}
      {tab === "grid" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))", gap: 16 }}>
          {workspaces.map(ws => {
            const rt = getRuntime(ws.id);
            const status = rt?.runtime_status || ws.session_status || "stopped";
            const color = STATUS_COLORS[status] || "#6b7280";
            const routeMode = rt?.current_route_mode || "DIRECT";
            return (
              <Card key={ws.id} title="">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div>
                    <strong style={{ fontSize: "1.1rem" }}>{ws.name}</strong>
                    {ws.channel_name && <span className="text-muted" style={{ marginLeft: 8 }}>({ws.channel_name})</span>}
                  </div>
                  <span className="chip" style={{ background: color, color: "#fff", padding: "2px 10px", borderRadius: 12, fontSize: "0.8rem" }}>
                    {status}
                  </span>
                </div>

                {/* Runtime info */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: "0.85rem", marginBottom: 12 }}>
                  <span className="text-muted">Route: <strong style={{ color: POLICY_COLORS[routeMode] || "#6b7280" }}>{routeMode}</strong></span>
                  <span className="text-muted">PID: {rt?.browser_pid || "—"}</span>
                  <span className="text-muted">IP: {rt?.current_outbound_ip || "local"}</span>
                  <span className="text-muted">Verified: {ws.last_verified_at ? new Date(ws.last_verified_at).toLocaleString("vi") : "—"}</span>
                </div>

                {rt?.last_error_message && (
                  <div style={{ background: "rgba(239,68,68,0.15)", padding: 8, borderRadius: 6, fontSize: "0.8rem", marginBottom: 8, color: "#f87171" }}>
                    ⚠️ {rt.last_error_message.slice(0, 120)}
                  </div>
                )}

                {/* Action buttons */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {(!rt || status === "stopped" || status === "crashed") && (
                    <button className="btn btn-sm btn-primary" disabled={!!loading} onClick={() => doAction(ws.id, "open")}>▶ Mở</button>
                  )}
                  {(status === "running" || status === "upload_ready") && (
                    <>
                      <button className="btn btn-sm" disabled={!!loading} onClick={() => doAction(ws.id, "verify-session")}>🔍 Verify</button>
                      <button className="btn btn-sm" disabled={!!loading} onClick={() => doAction(ws.id, "capture-screenshot")}>📸</button>
                      <button className="btn btn-sm" style={{ color: "#f59e0b" }} disabled={!!loading} onClick={() => doAction(ws.id, "close")}>⏹ Đóng</button>
                    </>
                  )}
                  {(status === "degraded" || status === "login_required") && (
                    <button className="btn btn-sm" disabled={!!loading} onClick={() => doAction(ws.id, "relaunch")}>🔄 Relaunch</button>
                  )}
                  {rt && status !== "stopped" && (
                    <button className="btn btn-sm" style={{ color: "#ef4444" }} disabled={!!loading} onClick={() => doAction(ws.id, "force-kill")}>💀 Kill</button>
                  )}
                  <button className="btn btn-sm" onClick={() => { loadSessionChecks(ws.id); setTab("sessions"); }}>📋 Logs</button>
                </div>
              </Card>
            );
          })}
          {workspaces.length === 0 && <Card title=""><p className="text-muted">Chưa có workspace. Tạo workspace mới để bắt đầu.</p></Card>}
        </div>
      )}

      {/* ── ROUTES TAB ── */}
      {tab === "routes" && (
        <Card title="Route Profiles (Proxy)">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Tên</th><th>Server</th><th>Port</th><th>Protocol</th><th>Status</th><th>Tested</th><th>Hành động</th></tr></thead>
            <tbody>
              {proxies.map(p => (
                <tr key={p.id}>
                  <td>#{p.id}</td>
                  <td>{p.name}</td>
                  <td>{p.server}</td>
                  <td>{p.port}</td>
                  <td>{p.protocol}</td>
                  <td><span className="chip" style={{ background: p.status === "active" ? "#22c55e" : "#ef4444", color: "#fff", padding: "2px 8px", borderRadius: 8, fontSize: "0.75rem" }}>{p.status}</span></td>
                  <td className="text-muted">{p.last_tested_at ? new Date(p.last_tested_at).toLocaleString("vi") : "—"}</td>
                  <td><button className="btn btn-sm" onClick={() => api.post(`/api/v2/workspaces/proxy-profiles/${p.id}/test`).then(fetchAll)}>🧪 Test</button></td>
                </tr>
              ))}
              {proxies.length === 0 && <tr><td colSpan={8} className="text-muted">Chưa có proxy profile.</td></tr>}
            </tbody>
          </table>
        </Card>
      )}

      {/* ── POLICY EVENTS TAB ── */}
      {tab === "policy" && (
        <Card title="Network Policy Events">
          <table className="data-table">
            <thead><tr><th>Thời gian</th><th>WS</th><th>Job Type</th><th>Policy</th><th>Decision</th><th>IP</th></tr></thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id}>
                  <td className="text-muted" style={{ fontSize: "0.8rem" }}>{new Date(e.created_at).toLocaleString("vi")}</td>
                  <td>#{e.workspace_id}</td>
                  <td><code>{e.job_type}</code></td>
                  <td><span style={{ color: POLICY_COLORS[e.policy_mode] || "#6b7280", fontWeight: 600 }}>{e.policy_mode}</span></td>
                  <td>{e.decision === "allow" ? "✅" : e.decision === "block" ? "🚫" : "⚠️"} {e.decision}</td>
                  <td className="text-muted">{e.outbound_ip || "—"}</td>
                </tr>
              ))}
              {events.length === 0 && <tr><td colSpan={6} className="text-muted">Chưa có policy events.</td></tr>}
            </tbody>
          </table>
        </Card>
      )}

      {/* ── SESSION CHECKS TAB ── */}
      {tab === "sessions" && (
        <Card title={`Session Checks${selWs ? ` — Workspace #${selWs}` : ""}`}>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            {workspaces.map(ws => (
              <button key={ws.id} className={`btn btn-sm${selWs === ws.id ? " btn-primary" : ""}`} onClick={() => loadSessionChecks(ws.id)}>
                {ws.name}
              </button>
            ))}
          </div>
          <table className="data-table">
            <thead><tr><th>Thời gian</th><th>Loại</th><th>Trạng thái</th><th>Screenshot</th></tr></thead>
            <tbody>
              {sessionChecks.map(sc => (
                <tr key={sc.id}>
                  <td className="text-muted" style={{ fontSize: "0.8rem" }}>{new Date(sc.created_at).toLocaleString("vi")}</td>
                  <td>{sc.check_type}</td>
                  <td>
                    <span className="chip" style={{ background: STATUS_COLORS[sc.status] || "#6b7280", color: "#fff", padding: "2px 8px", borderRadius: 8, fontSize: "0.75rem" }}>
                      {sc.status}
                    </span>
                  </td>
                  <td className="text-muted">{sc.screenshot_path ? "📸 Có" : "—"}</td>
                </tr>
              ))}
              {sessionChecks.length === 0 && <tr><td colSpan={4} className="text-muted">{selWs ? "Chưa có session checks." : "Chọn workspace để xem."}</td></tr>}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
