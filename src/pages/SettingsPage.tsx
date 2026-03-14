import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";

interface KeyStatus {
  openai_keys: number; elevenlabs_keys: number; pexels: boolean;
  pixabay: boolean; newsapi: boolean; serpapi: boolean;
  youtube_upload_enabled: boolean; upload_thumbnail: boolean; upload_captions: boolean;
}

interface Sources {
  research_providers: string[]; footage_providers: string[];
  voice_providers: string[]; transcribe_providers: string[];
  trend_sources: string[];
}

const ROUTE_VI: Record<string, string> = {
  voice_providers: "🎙️ Giọng đọc", transcribe_providers: "📝 Phiên âm",
  footage_providers: "🎞️ Tìm hình/video", research_providers: "🔍 Nghiên cứu",
  trend_sources: "📡 Nguồn xu hướng",
};

export default function SettingsPage() {
  const [keys, setKeys] = useState<KeyStatus | null>(null);
  const [sources, setSources] = useState<Sources | null>(null);

  useEffect(() => {
    api.get<KeyStatus>("/api/settings/keys").then(setKeys).catch(() => {});
    api.get<Sources>("/api/sources").then(setSources).catch(() => {});
  }, []);

  const keyList = keys ? [
    { name: "OpenAI", ok: keys.openai_keys > 0, detail: `${keys.openai_keys} key(s)` },
    { name: "ElevenLabs", ok: keys.elevenlabs_keys > 0, detail: `${keys.elevenlabs_keys} key(s)` },
    { name: "Pexels", ok: keys.pexels, detail: keys.pexels ? "đã cài" : "chưa cài" },
    { name: "Pixabay", ok: keys.pixabay, detail: keys.pixabay ? "đã cài" : "chưa cài" },
    { name: "NewsAPI", ok: keys.newsapi, detail: keys.newsapi ? "đã cài" : "chưa cài" },
    { name: "SerpAPI", ok: keys.serpapi, detail: keys.serpapi ? "đã cài" : "chưa cài" },
  ] : [];

  const features = keys ? [
    { name: "Upload YouTube tự động", on: keys.youtube_upload_enabled },
    { name: "Upload thumbnail", on: keys.upload_thumbnail },
    { name: "Upload phụ đề", on: keys.upload_captions },
  ] : [];

  return (
    <div className="page">
      <div className="page-head">
        <h2>Cài đặt</h2>
        <p>Trạng thái API key, tính năng upload, và thứ tự lựa chọn nhà cung cấp.</p>
      </div>

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
          {features.length > 0 && (
            <>
              <h4 style={{ margin: "16px 0 8px", color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: 1 }}>Tính năng</h4>
              <table className="data-table">
                <tbody>
                  {features.map((f) => (
                    <tr key={f.name}>
                      <td>{f.name}</td>
                      <td><span className={`chip chip-sm ${f.on ? "chip-done" : "chip-failed"}`}>{f.on ? "BẬT" : "TẮT"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
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
    </div>
  );
}
