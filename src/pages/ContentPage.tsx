import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";
import { FormField } from "../components/FormField";

export default function ContentPage() {
  const [ideas, setIdeas] = useState<any[]>([]);
  const [briefs, setBriefs] = useState<any[]>([]);
  const [scripts, setScripts] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [tab, setTab] = useState<"ideas" | "briefs" | "scripts">("ideas");
  const [msg, setMsg] = useState("");

  // --- New idea form ---
  const [newIdea, setNewIdea] = useState({ channel_name: "", title: "", angle: "", source: "" });

  const load = () => {
    api.get<{ items: any[] }>("/api/v2/content/ideas?limit=100").then((r) => setIdeas(r.items)).catch(() => {});
    api.get<{ items: any[] }>("/api/v2/content/briefs?limit=50").then((r) => setBriefs(r.items)).catch(() => {});
    api.get<{ items: any[] }>("/api/v2/content/scripts?limit=50").then((r) => setScripts(r.items)).catch(() => {});
    api.get<{ items: any[] }>("/api/channels").then((r) => setChannels(r.items)).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const addIdea = async () => {
    if (!newIdea.channel_name || !newIdea.title) return;
    await api.post("/api/v2/content/ideas", newIdea);
    setNewIdea({ channel_name: "", title: "", angle: "", source: "" });
    setMsg("Ý tưởng đã thêm ✅");
    load();
  };

  const approveIdea = async (id: number) => {
    await api.put(`/api/v2/content/ideas/${id}/status`, { status: "approved" });
    load();
  };

  const createBrief = async (idea: any) => {
    await api.post("/api/v2/content/briefs", {
      idea_id: idea.id, channel_name: idea.channel_name, title: idea.title,
    });
    setMsg(`Brief tạo cho "${idea.title}" ✅`);
    load();
  };

  const [generating, setGenerating] = useState(false);
  const generateScript = async (brief: any) => {
    setGenerating(true);
    setMsg("Đang tạo script bằng AI...");
    try {
      const res = await api.post<{ word_count: number; message: string }>("/api/v2/content/scripts/generate", {
        brief_id: brief.id, channel_name: brief.channel_name,
      });
      setMsg(`✅ ${res.message}`);
      load();
    } catch (e: any) { setMsg(`❌ ${e.message}`); }
    setGenerating(false);
  };

  const deleteIdea = async (id: number) => {
    await api.del(`/api/v2/content/ideas/${id}`);
    load();
  };

  const statusColor = (s: string) =>
    s === "inbox" ? "" : s === "approved" ? "chip-done" : s === "rejected" ? "chip-failed" : s === "briefed" ? "chip-queued" : "chip-accent";

  return (
    <div className="page">
      <div className="page-head">
        <h2>Content Studio</h2>
        <p>Pipeline: Ý tưởng → Brief → Script → Sản xuất. Quản lý toàn bộ quy trình nội dung.</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Ý tưởng" value={ideas.length} sub={`${ideas.filter((i) => i.status === "inbox").length} trong inbox`} />
        <StatCard label="Briefs" value={briefs.length} sub={`${briefs.filter((b) => b.status === "draft").length} draft`} />
        <StatCard label="Scripts" value={scripts.length} sub={`${scripts.filter((s) => s.status === "draft").length} draft`} />
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button className={`btn ${tab === "ideas" ? "btn-primary" : ""}`} onClick={() => setTab("ideas")}>Ý tưởng ({ideas.length})</button>
        <button className={`btn ${tab === "briefs" ? "btn-primary" : ""}`} onClick={() => setTab("briefs")}>Briefs ({briefs.length})</button>
        <button className={`btn ${tab === "scripts" ? "btn-primary" : ""}`} onClick={() => setTab("scripts")}>Scripts ({scripts.length})</button>
      </div>

      {tab === "ideas" && (
        <div className="grid-2">
          <Card title="Idea Inbox">
            <div className="list-stack">
              {ideas.map((i) => (
                <div key={i.id} className="list-item">
                  <div className="list-item-main">
                    <strong>{i.title}</strong>
                    <span className={`chip chip-sm ${statusColor(i.status)}`}>{i.status}</span>
                  </div>
                  <div className="list-item-meta">
                    <span>{i.channel_name}</span>
                    {i.angle && <span>Góc: {i.angle}</span>}
                  </div>
                  <div className="list-item-actions">
                    {i.status === "inbox" && <button className="btn btn-sm" onClick={() => approveIdea(i.id)}>✓ Approve</button>}
                    {i.status === "approved" && <button className="btn btn-sm btn-primary" onClick={() => createBrief(i)}>→ Tạo Brief</button>}
                    <button className="btn btn-sm" style={{ color: "var(--red)" }} onClick={() => deleteIdea(i.id)}>×</button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Thêm ý tưởng mới">
            <div className="form-grid">
              <div className="form-field">
                <label className="form-label">Channel</label>
                <select className="form-input" value={newIdea.channel_name} onChange={(e) => setNewIdea({ ...newIdea, channel_name: e.target.value })}>
                  <option value="">Chọn channel</option>
                  {channels.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
                </select>
              </div>
              <FormField label="Tiêu đề" value={newIdea.title} onChange={(v) => setNewIdea({ ...newIdea, title: v })} placeholder="Ý tưởng video..." />
              <FormField label="Góc tiếp cận" value={newIdea.angle} onChange={(v) => setNewIdea({ ...newIdea, angle: v })} placeholder="Khía cạnh độc đáo..." />
              <FormField label="Nguồn" value={newIdea.source} onChange={(v) => setNewIdea({ ...newIdea, source: v })} placeholder="URL hoặc ghi chú nguồn" />
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={addIdea}>Thêm vào Inbox</button>
            </div>
          </Card>
        </div>
      )}

      {tab === "briefs" && (
        <Card title="Content Briefs">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Channel</th><th>Tiêu đề</th><th>Format</th><th>Duration</th><th>Status</th><th>Hành động</th></tr></thead>
            <tbody>
              {briefs.map((b) => (
                <tr key={b.id}>
                  <td className="mono">#{b.id}</td>
                  <td>{b.channel_name}</td>
                  <td className="cell-title">{b.title}</td>
                  <td><span className="chip chip-sm">{b.target_format}</span></td>
                  <td>{b.target_duration_sec}s</td>
                  <td><span className={`chip chip-sm ${b.status === "draft" ? "chip-queued" : "chip-done"}`}>{b.status}</span></td>
                  <td>
                    {b.status === "draft" && (
                      <button className="btn btn-sm btn-primary" onClick={() => generateScript(b)} disabled={generating}>
                        {generating ? "..." : "🤖 Tạo Script"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {tab === "scripts" && (
        <Card title="Script Drafts">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Channel</th><th>Tiêu đề</th><th>Từ</th><th>~Thời lượng</th><th>Fact Check</th><th>Provider</th></tr></thead>
            <tbody>
              {scripts.map((s) => (
                <tr key={s.id}>
                  <td className="mono">#{s.id}</td>
                  <td>{s.channel_name}</td>
                  <td className="cell-title">{s.title}</td>
                  <td>{s.word_count}</td>
                  <td>{s.estimated_duration_sec}s</td>
                  <td><span className={`chip chip-sm ${s.fact_check_status === "pending" ? "chip-queued" : "chip-done"}`}>{s.fact_check_status}</span></td>
                  <td><span className="chip chip-sm">{s.provider_used}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
