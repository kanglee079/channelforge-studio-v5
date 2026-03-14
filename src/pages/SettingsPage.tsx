import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

interface KeyStatus {
  openai_keys: number; elevenlabs_keys: number; pexels: boolean;
  pixabay: boolean; newsapi: boolean; serpapi: boolean;
  youtube_upload_enabled: boolean; upload_thumbnail: boolean; upload_captions: boolean;
}

interface Sources { research_providers: string[]; footage_providers: string[]; voice_providers: string[]; transcribe_providers: string[]; trend_sources: string[]; }

interface Diagnostics {
  environment: { python_version: string; platform: string; arch: string; engine_dir: string; };
  files: { db_exists: boolean; db_size_mb: number; env_exists: boolean; workspaces_dir: boolean; workspace_count: number; };
  disk: { total_gb: number; used_gb: number; free_gb: number; usage_percent: number; };
  packages: Record<string, { installed: boolean; description: string; required: boolean }>;
  api_keys: Record<string, boolean>;
  db_stats: Record<string, number>;
}

interface SetupStatus { steps: Record<string, boolean>; complete: boolean; progress: number; total: number; }
interface MigrationStatus { needs_migration: boolean; existing_tables?: number; missing_v5_tables?: string[]; v5_ready?: boolean; reason?: string; }

const ROUTE_VI: Record<string, string> = {
  voice_providers: "🎙️ Giọng đọc", transcribe_providers: "📝 Phiên âm",
  footage_providers: "🎞️ Tìm hình/video", research_providers: "🔍 Nghiên cứu",
  trend_sources: "📡 Xu hướng",
};
const STEP_VI: Record<string, string> = {
  env_file: "File .env", database: "Database", api_keys: "API Keys",
  data_dir: "Thư mục data", channels: "Profile kênh",
};

export default function SettingsPage() {
  const [tab, setTab] = useState<"keys" | "diagnostics" | "setup" | "migration">("keys");
  const [keys, setKeys] = useState<KeyStatus | null>(null);
  const [sources, setSources] = useState<Sources | null>(null);
  const [diag, setDiag] = useState<Diagnostics | null>(null);
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [migration, setMigration] = useState<MigrationStatus | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get<KeyStatus>("/api/settings/keys").then(setKeys).catch(() => {});
    api.get<Sources>("/api/sources").then(setSources).catch(() => {});
  }, []);

  const loadDiag = () => api.get<Diagnostics>("/api/v5/system/diagnostics").then(setDiag).catch(() => {});
  const loadSetup = () => api.get<SetupStatus>("/api/v5/system/setup/status").then(setSetup).catch(() => {});
  const loadMigration = () => api.get<MigrationStatus>("/api/v5/system/migration/check").then(setMigration).catch(() => {});

  const initDirs = async () => { try { const r = await api.post<{ message: string }>("/api/v5/system/setup/init-dirs", {}); setMsg(r.message); loadSetup(); } catch (e: any) { setMsg(e.message); } };
  const initEnv = async () => { try { const r = await api.post<{ message: string }>("/api/v5/system/setup/init-env", {}); setMsg(r.message); loadSetup(); } catch (e: any) { setMsg(e.message); } };
  const applyMigration = async () => { try { const r = await api.post<{ message: string }>("/api/v5/system/migration/apply", {}); setMsg(r.message); loadMigration(); } catch (e: any) { setMsg(e.message); } };

  const keyList = keys ? [
    { name: "OpenAI", ok: keys.openai_keys > 0, detail: `${keys.openai_keys} key(s)` },
    { name: "ElevenLabs", ok: keys.elevenlabs_keys > 0, detail: `${keys.elevenlabs_keys} key(s)` },
    { name: "Pexels", ok: keys.pexels, detail: keys.pexels ? "đã cài" : "chưa cài" },
    { name: "Pixabay", ok: keys.pixabay, detail: keys.pixabay ? "đã cài" : "chưa cài" },
    { name: "NewsAPI", ok: keys.newsapi, detail: keys.newsapi ? "đã cài" : "chưa cài" },
  ] : [];

  return (
    <div className="page">
      <div className="page-head">
        <h2>Cài đặt & Hệ thống</h2>
        <p>API keys, diagnostics, setup wizard, V4→V5 migration.</p>
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button className={`btn btn-sm ${tab === "keys" ? "btn-primary" : ""}`} onClick={() => setTab("keys")}>🔑 API Keys</button>
        <button className={`btn btn-sm ${tab === "diagnostics" ? "btn-primary" : ""}`} onClick={() => { setTab("diagnostics"); loadDiag(); }}>🩺 Diagnostics</button>
        <button className={`btn btn-sm ${tab === "setup" ? "btn-primary" : ""}`} onClick={() => { setTab("setup"); loadSetup(); }}>🧙 Setup Wizard</button>
        <button className={`btn btn-sm ${tab === "migration" ? "btn-primary" : ""}`} onClick={() => { setTab("migration"); loadMigration(); }}>🔄 Migration</button>
      </div>

      {/* ── KEYS TAB ── */}
      {tab === "keys" && (
        <div className="grid-2">
          <Card title="API Key">
            <table className="data-table">
              <thead><tr><th>Nhà cung cấp</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {keyList.map((k) => (
                  <tr key={k.name}>
                    <td><strong>{k.name}</strong></td>
                    <td><span className={`chip chip-sm ${k.ok ? "chip-done" : "chip-failed"}`}>{k.detail}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
          <Card title="Thứ tự nhà cung cấp">
            {sources ? Object.entries(sources).map(([key, chain]) => (
              <div key={key} style={{ marginBottom: 14 }}>
                <strong>{ROUTE_VI[key] || key}</strong>
                <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "2px 0 0" }}>
                  {Array.isArray(chain) ? chain.join(" → ") : String(chain)}
                </p>
              </div>
            )) : <p className="text-muted">Đang tải...</p>}
          </Card>
        </div>
      )}

      {/* ── DIAGNOSTICS TAB ── */}
      {tab === "diagnostics" && diag && (
        <>
          <div className="stat-grid">
            <StatCard label="Python" value={diag.environment.python_version.split(" ")[0]} />
            <StatCard label="Platform" value={diag.environment.platform.slice(0, 20)} />
            <StatCard label="DB Size" value={`${diag.files.db_size_mb}MB`} />
            <StatCard label="Disk Free" value={`${diag.disk.free_gb}GB`} sub={`${diag.disk.usage_percent}% used`} />
          </div>
          <div className="grid-2" style={{ marginTop: 16 }}>
            <Card title="Packages">
              <table className="data-table">
                <thead><tr><th>Package</th><th>Mô tả</th><th>Trạng thái</th></tr></thead>
                <tbody>
                  {Object.entries(diag.packages).map(([name, info]) => (
                    <tr key={name}>
                      <td><strong>{name}</strong></td>
                      <td style={{ fontSize: "0.8rem" }}>{info.description}</td>
                      <td><span className={`chip chip-sm ${info.installed ? "chip-done" : info.required ? "chip-failed" : "chip-queued"}`}>
                        {info.installed ? "✓" : info.required ? "❌ Cần cài" : "Tùy chọn"}
                      </span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
            <Card title="API Keys & DB">
              <h4 style={{ margin: "0 0 8px", fontSize: 13 }}>API Keys</h4>
              {Object.entries(diag.api_keys).map(([key, ok]) => (
                <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
                  <span>{key}</span>
                  <span className={`chip chip-sm ${ok ? "chip-done" : "chip-failed"}`}>{ok ? "✓" : "✗"}</span>
                </div>
              ))}
              <h4 style={{ margin: "16px 0 8px", fontSize: 13 }}>Database (tổng {diag.db_stats.table_count} bảng)</h4>
              {Object.entries(diag.db_stats).filter(([k]) => k !== "table_count").slice(0, 10).map(([table, count]) => (
                <div key={table} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0", fontSize: "0.85rem" }}>
                  <span>{table}</span><span>{count}</span>
                </div>
              ))}
            </Card>
          </div>
        </>
      )}
      {tab === "diagnostics" && !diag && <Card title="Loading..."><p className="text-muted">Đang tải diagnostics...</p></Card>}

      {/* ── SETUP WIZARD TAB ── */}
      {tab === "setup" && setup && (
        <Card title={`Setup Wizard — ${setup.progress}/${setup.total} bước hoàn tất`}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ width: "100%", height: 8, background: "rgba(255,255,255,0.1)", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: `${(setup.progress / setup.total) * 100}%`, height: "100%", background: "var(--accent)", borderRadius: 4, transition: "width 0.3s" }} />
            </div>
          </div>
          <div className="list-stack">
            {Object.entries(setup.steps).map(([step, done]) => (
              <div key={step} className="list-item">
                <div className="list-item-main">
                  <span style={{ marginRight: 8 }}>{done ? "✅" : "⬜"}</span>
                  <strong>{STEP_VI[step] || step}</strong>
                  <span className={`chip chip-sm ${done ? "chip-done" : "chip-failed"}`}>{done ? "OK" : "Chưa"}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="form-actions" style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <button className="btn btn-primary" onClick={initDirs}>📁 Tạo thư mục</button>
            <button className="btn" onClick={initEnv}>📝 Tạo .env mẫu</button>
          </div>
        </Card>
      )}
      {tab === "setup" && !setup && <Card title="Loading..."><p className="text-muted">Đang tải...</p></Card>}

      {/* ── MIGRATION TAB ── */}
      {tab === "migration" && migration && (
        <Card title="V4 → V5 Migration">
          <div style={{ marginBottom: 16 }}>
            {migration.v5_ready ? (
              <div className="chip chip-done" style={{ fontSize: "1.1rem", padding: "8px 16px" }}>✅ V5 đã sẵn sàng — tất cả bảng dữ liệu đã tạo</div>
            ) : migration.reason ? (
              <div><p className="text-muted">{migration.reason}</p><p>Chạy setup wizard hoặc pipeline để tạo database.</p></div>
            ) : (
              <div>
                <p>Thiếu {(migration.missing_v5_tables || []).length} bảng V5:</p>
                <ul>{(migration.missing_v5_tables || []).map((t) => <li key={t}><code>{t}</code></li>)}</ul>
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 12, fontSize: "0.9rem", color: "var(--text-muted)" }}>
            <span>Tổng bảng hiện tại: {migration.existing_tables ?? "N/A"}</span>
          </div>
          {migration.needs_migration && (
            <div className="form-actions" style={{ marginTop: 16 }}>
              <button className="btn btn-primary" onClick={applyMigration}>🔄 Áp dụng migration V5</button>
            </div>
          )}
        </Card>
      )}
      {tab === "migration" && !migration && <Card title="Loading..."><p className="text-muted">Đang tải...</p></Card>}
    </div>
  );
}
