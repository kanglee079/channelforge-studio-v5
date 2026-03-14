import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface SceneMatch {
  id: number; scene_index: number; scene_json: string;
  selected_asset_id: number | null; final_score: number;
  confidence_label: string; status: string;
  selected_clip_start_sec: number; selected_clip_end_sec: number;
  candidates: Candidate[];
}

interface Candidate {
  id: number; asset_id: number; final_score: number;
  semantic_score: number; object_match_score: number;
  quality_score: number; style_match_score: number;
  negative_penalty: number; duplicate_penalty: number;
  explain_json: string; rank: number;
}

interface Script {
  id: number; title: string; channel_name: string;
  word_count: number; estimated_duration_sec: number;
}

const CONF_COLOR: Record<string, string> = {
  high: "chip-done", medium: "chip-retry", low: "chip-failed",
};
const CONF_VI: Record<string, string> = {
  high: "Cao", medium: "Trung bình", low: "Thấp",
};

export default function ScenePlannerPage() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [selectedScript, setSelectedScript] = useState<number | null>(null);
  const [scenes, setScenes] = useState<SceneMatch[]>([]);
  const [selectedScene, setSelectedScene] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get<{ items: Script[] }>("/api/v2/content/scripts").then((r) => setScripts(r.items)).catch(() => {});
  }, []);

  const loadMatches = (scriptId: number) => {
    setSelectedScript(scriptId);
    api.get<{ items: SceneMatch[] }>(`/api/v5/visual-match/projects/${scriptId}`)
      .then((r) => setScenes(r.items))
      .catch(() => setScenes([]));
  };

  const runMatch = async () => {
    if (!selectedScript) return;
    setLoading(true); setMsg("Đang phân tích scenes và tìm media...");
    try {
      const res = await api.post<{ message: string; total_scenes: number; high_confidence: number; medium_confidence: number; low_confidence: number }>(
        `/api/v5/visual-match/projects/${selectedScript}/run`, {}
      );
      setMsg(`${res.message} — Cao: ${res.high_confidence}, TB: ${res.medium_confidence}, Thấp: ${res.low_confidence}`);
      loadMatches(selectedScript);
    } catch (e: any) { setMsg(e.message); }
    setLoading(false);
  };

  const rerunLow = async () => {
    if (!selectedScript) return;
    setLoading(true); setMsg("Đang chạy lại các scene confidence thấp...");
    try {
      const res = await api.post<{ message: string }>(`/api/v5/visual-match/projects/${selectedScript}/rerun-low-confidence`, {});
      setMsg(res.message);
      loadMatches(selectedScript);
    } catch (e: any) { setMsg(e.message); }
    setLoading(false);
  };

  const parseScene = (json: string) => {
    try { return JSON.parse(json); } catch { return {}; }
  };

  const currentScene = scenes.find((s) => s.scene_index === selectedScene);

  return (
    <div className="page">
      <div className="page-head">
        <h2>Scene Planner — Visual Match</h2>
        <p>Phân tích script → tách scene → tìm media phù hợp nhất cho từng scene. AI tự chấm điểm và đề xuất.</p>
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      {/* Script selector */}
      <Card title="Chọn Script">
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <select className="form-input" style={{ maxWidth: 400 }} value={selectedScript || ""} onChange={(e) => { const id = Number(e.target.value); if (id) loadMatches(id); }}>
            <option value="">Chọn script để phân tích</option>
            {scripts.map((s) => (
              <option key={s.id} value={s.id}>[{s.channel_name}] {s.title} ({s.word_count} từ)</option>
            ))}
          </select>
          <button className="btn btn-primary" onClick={runMatch} disabled={!selectedScript || loading}>
            {loading ? "⏳ Đang xử lý..." : "🎬 Chạy Visual Match"}
          </button>
          {scenes.some((s) => s.confidence_label === "low") && (
            <button className="btn" onClick={rerunLow} disabled={loading}>🔄 Chạy lại Scene Thấp</button>
          )}
        </div>
      </Card>

      {/* 3-column layout */}
      {scenes.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr 1fr", gap: 16, marginTop: 16 }}>
          {/* Column 1: Scene list */}
          <Card title={`Scenes (${scenes.length})`}>
            <div className="list-stack">
              {scenes.map((s) => {
                const scene = parseScene(s.scene_json);
                return (
                  <div
                    key={s.scene_index}
                    className={`list-item ${selectedScene === s.scene_index ? "list-item-active" : ""}`}
                    style={{ cursor: "pointer", borderLeft: selectedScene === s.scene_index ? "3px solid var(--accent)" : "3px solid transparent" }}
                    onClick={() => setSelectedScene(s.scene_index)}
                  >
                    <div className="list-item-main">
                      <strong>Scene #{s.scene_index + 1}</strong>
                      <span className={`chip chip-sm ${CONF_COLOR[s.confidence_label]}`}>{CONF_VI[s.confidence_label]}</span>
                    </div>
                    <div className="list-item-meta" style={{ fontSize: "0.8rem" }}>
                      <span>{(scene.visual_intent || "").slice(0, 60)}...</span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      Điểm: {(s.final_score * 100).toFixed(0)}% · {s.status}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Column 2: Selected scene detail */}
          <Card title={currentScene ? `Scene #${currentScene.scene_index + 1} — Chi tiết` : "Chọn scene"}>
            {currentScene ? (() => {
              const scene = parseScene(currentScene.scene_json);
              return (
                <div>
                  <div style={{ marginBottom: 12 }}>
                    <h4 style={{ color: "var(--accent)", margin: "0 0 4px 0" }}>🎯 Visual Intent</h4>
                    <p style={{ margin: 0 }}>{scene.visual_intent}</p>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <h4 style={{ margin: "0 0 4px 0" }}>🗣️ Lời thoại</h4>
                    <p style={{ margin: 0, fontSize: "0.9rem", fontStyle: "italic", color: "var(--text-muted)" }}>{scene.spoken_text}</p>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: "0.85rem" }}>
                    <div><strong>Cần có:</strong> {(scene.must_have_objects || []).join(", ") || "–"}</div>
                    <div><strong>Không hiện:</strong> {(scene.must_not_show || []).join(", ") || "–"}</div>
                    <div><strong>Mood:</strong> {scene.mood}</div>
                    <div><strong>Vị trí:</strong> {scene.location_hint || "–"}</div>
                    <div><strong>Loại asset:</strong> {scene.asset_preference}</div>
                    <div><strong>Thời lượng:</strong> {scene.duration_sec}s</div>
                  </div>
                  <div style={{ marginTop: 16, padding: 8, background: "rgba(255,255,255,0.05)", borderRadius: 8 }}>
                    <strong>Kết quả matching:</strong>
                    <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
                      <span className={`chip chip-sm ${CONF_COLOR[currentScene.confidence_label]}`}>
                        {CONF_VI[currentScene.confidence_label]} ({(currentScene.final_score * 100).toFixed(0)}%)
                      </span>
                      <span>Trạng thái: {currentScene.status}</span>
                      <span>Candidates: {currentScene.candidates.length}</span>
                    </div>
                  </div>
                </div>
              );
            })() : <p className="text-muted">Chọn một scene từ danh sách bên trái để xem chi tiết.</p>}
          </Card>

          {/* Column 3: Candidate tray */}
          <Card title={currentScene ? `Top Candidates` : "Candidates"}>
            {currentScene && currentScene.candidates.length > 0 ? (
              <div className="list-stack">
                {currentScene.candidates.map((c, i) => (
                  <div key={c.id} className="list-item" style={{ borderLeft: c.asset_id === currentScene.selected_asset_id ? "3px solid #00ff88" : "3px solid transparent" }}>
                    <div className="list-item-main">
                      <strong>#{i + 1}</strong>
                      <span className={`chip chip-sm ${c.final_score >= 0.7 ? "chip-done" : c.final_score >= 0.45 ? "chip-retry" : "chip-failed"}`}>
                        {(c.final_score * 100).toFixed(0)}%
                      </span>
                      {c.asset_id === currentScene.selected_asset_id && <span className="chip chip-sm chip-done">✓ Đã chọn</span>}
                    </div>
                    <div className="list-item-meta" style={{ fontSize: "0.75rem" }}>
                      <span>Semantic: {(c.semantic_score * 100).toFixed(0)}%</span>
                      <span>Object: {(c.object_match_score * 100).toFixed(0)}%</span>
                      <span>Quality: {(c.quality_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted">{currentScene ? "Không có candidates cho scene này" : "Chọn scene để xem candidates"}</p>
            )}
          </Card>
        </div>
      )}

      {/* Empty state */}
      {scenes.length === 0 && selectedScript && (
        <Card title="Chưa có kết quả">
          <p className="text-muted">Chọn script và bấm "Chạy Visual Match" để bắt đầu phân tích scenes.</p>
        </Card>
      )}

      {/* Summary stats */}
      {scenes.length > 0 && (
        <div className="stat-grid" style={{ marginTop: 16 }}>
          <div className="stat-card"><div className="stat-label">TỔNG SCENES</div><div className="stat-value">{scenes.length}</div></div>
          <div className="stat-card"><div className="stat-label">ĐỘ TIN CẬY CAO</div><div className="stat-value">{scenes.filter(s => s.confidence_label === "high").length}</div></div>
          <div className="stat-card"><div className="stat-label">TRUNG BÌNH</div><div className="stat-value">{scenes.filter(s => s.confidence_label === "medium").length}</div></div>
          <div className="stat-card"><div className="stat-label">CẦN REVIEW</div><div className="stat-value">{scenes.filter(s => s.confidence_label === "low").length}</div></div>
        </div>
      )}
    </div>
  );
}
