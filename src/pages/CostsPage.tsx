import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card, StatCard } from "../components/Card";

interface CostBreakdown {
  provider: string; task_type: string; requests: number;
  total_tokens: number; total_cost: number; cache_hits: number;
}

interface BudgetProfile {
  id: number; name: string; monthly_limit: number;
  quality_mode: string; active: number;
}

export default function CostsPage() {
  const [breakdown, setBreakdown] = useState<CostBreakdown[]>([]);
  const [budgets, setBudgets] = useState<BudgetProfile[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [totalReqs, setTotalReqs] = useState(0);
  const [cacheRate, setCacheRate] = useState(0);
  const [tab, setTab] = useState<"overview" | "budgets" | "rules">("overview");
  const [msg, setMsg] = useState("");

  // Budget form
  const [bName, setBName] = useState("");
  const [bLimit, setBLimit] = useState("100");
  const [bMode, setBMode] = useState("balanced");

  useEffect(() => {
    api.get<{ breakdown: CostBreakdown[]; total_cost: number; total_requests: number; cache_hit_rate: number }>(
      "/api/v5/cost/summary?days=30"
    ).then((r) => {
      setBreakdown(r.breakdown || []);
      setTotalCost(r.total_cost);
      setTotalReqs(r.total_requests);
      setCacheRate(r.cache_hit_rate);
    }).catch(() => {});
    api.get<{ items: BudgetProfile[] }>("/api/v5/cost/budgets").then((r) => setBudgets(r.items)).catch(() => {});
  }, []);

  const addBudget = async () => {
    if (!bName.trim()) return;
    try {
      const res = await api.post<{ message: string }>("/api/v5/cost/budgets", {
        name: bName, monthly_limit: parseFloat(bLimit), quality_mode: bMode,
      });
      setMsg(res.message); setBName("");
      api.get<{ items: BudgetProfile[] }>("/api/v5/cost/budgets").then((r) => setBudgets(r.items));
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Quản lý chi phí</h2>
        <p>Theo dõi chi phí API, routing provider, budget profiles — đảm bảo chi phí hợp lý nhất.</p>
      </div>

      {msg && <div className="chip chip-accent" style={{ marginBottom: 12 }}>{msg}</div>}

      <div className="stat-grid">
        <StatCard label="Chi phí tháng" value={`$${totalCost.toFixed(2)}`} sub="30 ngày qua" />
        <StatCard label="Lượt gọi API" value={totalReqs} sub="Tất cả providers" />
        <StatCard label="Cache hit" value={`${cacheRate}%`} sub="Tỷ lệ cache" />
        <StatCard label="Budget Profiles" value={budgets.length} />
      </div>

      <div style={{ display: "flex", gap: 8, margin: "16px 0" }}>
        <button className={`btn btn-sm ${tab === "overview" ? "btn-primary" : ""}`} onClick={() => setTab("overview")}>Chi tiết chi phí</button>
        <button className={`btn btn-sm ${tab === "budgets" ? "btn-primary" : ""}`} onClick={() => setTab("budgets")}>Budget Profiles</button>
        <button className={`btn btn-sm ${tab === "rules" ? "btn-primary" : ""}`} onClick={() => setTab("rules")}>Quy tắc routing</button>
      </div>

      {/* OVERVIEW */}
      {tab === "overview" && (
        <Card title="Chi phí theo Provider / Task">
          {breakdown.length > 0 ? (
            <table className="data-table">
              <thead><tr><th>PROVIDER</th><th>TASK TYPE</th><th>REQUESTS</th><th>TOKENS</th><th>CHI PHÍ</th><th>CACHE</th></tr></thead>
              <tbody>
                {breakdown.map((b, i) => (
                  <tr key={i}>
                    <td><span className="chip chip-sm chip-accent">{b.provider}</span></td>
                    <td>{b.task_type}</td>
                    <td>{b.requests}</td>
                    <td>{b.total_tokens.toLocaleString()}</td>
                    <td><strong>${b.total_cost.toFixed(4)}</strong></td>
                    <td>{b.cache_hits}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="text-muted" style={{ textAlign: "center", padding: 20 }}>Chạy pipeline để xem dữ liệu chi phí thực tế.</p>}
        </Card>
      )}

      {/* BUDGETS */}
      {tab === "budgets" && (
        <div className="grid-2">
          <Card title="Budget Profiles">
            <div className="list-stack">
              {budgets.map((b) => (
                <div key={b.id} className="list-item">
                  <div className="list-item-main">
                    <strong>{b.name}</strong>
                    <span className={`chip chip-sm ${b.active ? "chip-done" : ""}`}>{b.active ? "Active" : "Inactive"}</span>
                  </div>
                  <div className="list-item-meta">
                    <span>Hạn mức: ${b.monthly_limit}/tháng</span>
                    <span>Chế độ: {b.quality_mode}</span>
                  </div>
                </div>
              ))}
              {budgets.length === 0 && <p className="text-muted">Chưa có budget profile.</p>}
            </div>
          </Card>
          <Card title="Tạo budget mới">
            <div className="form-grid">
              <div className="form-field">
                <label className="form-label">Tên</label>
                <input className="form-input" value={bName} onChange={(e) => setBName(e.target.value)} placeholder="VD: Dev Testing" />
              </div>
              <div className="form-field">
                <label className="form-label">Giới hạn ($/tháng)</label>
                <input className="form-input" type="number" value={bLimit} onChange={(e) => setBLimit(e.target.value)} />
              </div>
              <div className="form-field">
                <label className="form-label">Chế độ chất lượng</label>
                <select className="form-input" value={bMode} onChange={(e) => setBMode(e.target.value)}>
                  <option value="budget">Budget (tiết kiệm)</option>
                  <option value="balanced">Balanced (cân bằng)</option>
                  <option value="premium">Premium (chất lượng cao)</option>
                </select>
              </div>
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={addBudget}>Tạo budget</button>
            </div>
          </Card>
        </div>
      )}

      {/* RULES */}
      {tab === "rules" && (
        <Card title="Quy tắc chọn provider">
          <div className="list-stack">
            <div className="list-item">
              <div className="list-item-main"><strong>Viết Script</strong><span className="chip chip-sm chip-accent">OpenAI</span></div>
              <div className="list-item-meta"><span>Ưu tiên chất lượng: GPT-4o → GPT-4o-mini → Ollama</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Giọng đọc</strong><span className="chip chip-sm chip-accent">OpenAI TTS</span></div>
              <div className="list-item-meta"><span>OpenAI TTS → ElevenLabs → Kokoro → Piper</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Phiên âm</strong><span className="chip chip-sm chip-queued">faster-whisper</span></div>
              <div className="list-item-meta"><span>Ưu tiên local: faster-whisper → OpenAI Whisper</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Brainstorm</strong><span className="chip chip-sm chip-queued">Ollama</span></div>
              <div className="list-item-meta"><span>Local free: Ollama → OpenAI (fallback)</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Footage</strong><span className="chip chip-sm chip-done">Pexels, Pixabay</span></div>
              <div className="list-item-meta"><span>Free APIs: Pexels → Pixabay → Local cache</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Hình ảnh</strong><span className="chip chip-sm chip-accent">DALL-E</span></div>
              <div className="list-item-meta"><span>DALL-E 3 → Stable Diffusion local</span></div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
