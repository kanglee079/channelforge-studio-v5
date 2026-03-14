import { Card, StatCard } from "../components/Card";

export default function CostsPage() {
  return (
    <div className="page">
      <div className="page-head">
        <h2>Quản lý chi phí</h2>
        <p>Theo dõi chi phí API, quản lý routing giữa cloud (OpenAI, ElevenLabs) và local (Ollama, Whisper).</p>
      </div>

      <div className="stat-grid">
        <StatCard label="Chi phí tháng" value="$0.00" sub="Chưa có dữ liệu" />
        <StatCard label="Lượt gọi API" value={0} sub="OpenAI + ElevenLabs" />
        <StatCard label="Dùng local" value={0} sub="Ollama / Whisper" />
      </div>

      <div className="grid-2">
        <Card title="Quy tắc chọn provider">
          <div className="list-stack">
            <div className="list-item">
              <div className="list-item-main"><strong>Viết Script</strong><span className="chip chip-sm chip-accent">OpenAI</span></div>
              <div className="list-item-meta"><span>Dùng OpenAI cho scripts chính thức để đảm bảo chất lượng cao</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Giọng đọc</strong><span className="chip chip-sm chip-accent">OpenAI TTS</span></div>
              <div className="list-item-meta"><span>Thứ tự: OpenAI TTS → ElevenLabs → Kokoro → Piper</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Phiên âm</strong><span className="chip chip-sm chip-queued">faster-whisper</span></div>
              <div className="list-item-meta"><span>Ưu tiên chạy local bằng faster-whisper, tiết kiệm chi phí</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Brainstorm ý tưởng</strong><span className="chip chip-sm chip-queued">Ollama</span></div>
              <div className="list-item-meta"><span>Dùng Ollama local cho brainstorm, không tốn tiền</span></div>
            </div>
            <div className="list-item">
              <div className="list-item-main"><strong>Tìm hình/video</strong><span className="chip chip-sm chip-done">Pexels, Pixabay</span></div>
              <div className="list-item-meta"><span>API miễn phí từ Pexels → Pixabay</span></div>
            </div>
          </div>
        </Card>

        <Card title="Lịch sử chi tiêu">
          <p className="text-muted" style={{ padding: 20, textAlign: "center" }}>
            Hệ thống ghi nhận chi phí sẽ hoạt động khi pipeline chạy.<br />
            Chạy thử vài jobs để xem dữ liệu thực tế tại đây.
          </p>
        </Card>
      </div>
    </div>
  );
}
