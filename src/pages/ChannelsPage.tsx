import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Card } from "../components/Card";
import { FormField, FormCheckbox } from "../components/FormField";

const emptyForm = {
  name: "", title_prefix: "", niche: "", language: "en",
  default_video_format: "shorts", upload_enabled: false,
  privacy_status: "private", category_id: "27",
  publish_interval_minutes: "60", daily_upload_soft_limit: "90",
  notify_subscribers: false, tags: "", disclose_synthetic_media: false,
  blocked_words: "", youtube_client_secrets: "", youtube_token_json: "",
};

export default function ChannelsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [msg, setMsg] = useState("");
  const [editing, setEditing] = useState(false);

  const load = () => api.get<{ items: any[] }>("/api/channels").then((r) => setItems(r.items));
  useEffect(() => { load(); }, []);

  const f = (key: string, val: string | boolean) => setForm({ ...form, [key]: val });

  const submit = async () => {
    const payload = {
      ...form,
      tags: form.tags.split(",").map((x) => x.trim()).filter(Boolean),
      blocked_words: form.blocked_words.split(",").map((x) => x.trim()).filter(Boolean),
      publish_interval_minutes: Number(form.publish_interval_minutes),
      daily_upload_soft_limit: Number(form.daily_upload_soft_limit),
    };
    const res = await api.post<{ message: string }>("/api/channels", payload);
    setMsg(res.message);
    setForm(emptyForm);
    setEditing(false);
    load();
  };

  const editChannel = (ch: any) => {
    setForm({
      name: ch.name || "", title_prefix: ch.title_prefix || "", niche: ch.niche || "",
      language: ch.language || "en", default_video_format: ch.default_video_format || "shorts",
      upload_enabled: ch.upload_enabled || false, privacy_status: ch.privacy_status || "private",
      category_id: ch.category_id || "27",
      publish_interval_minutes: String(ch.publish_interval_minutes || 60),
      daily_upload_soft_limit: String(ch.daily_upload_soft_limit || 90),
      notify_subscribers: ch.notify_subscribers || false,
      tags: (ch.tags || []).join(", "), disclose_synthetic_media: ch.disclose_synthetic_media || false,
      blocked_words: (ch.blocked_words || []).join(", "),
      youtube_client_secrets: ch.youtube_client_secrets || "",
      youtube_token_json: ch.youtube_token_json || "",
    });
    setEditing(true);
  };

  return (
    <div className="page">
      <div className="page-head">
        <h2>Quản lý kênh</h2>
        <p>Cấu hình niche, lịch đăng, chính sách upload và nhà cung cấp cho từng kênh YouTube.</p>
        <button className="btn btn-primary" onClick={() => { setForm(emptyForm); setEditing(true); }}>+ Tạo kênh mới</button>
      </div>

      <div className="grid-2">
        <Card title="Danh sách kênh">
          <div className="list-stack">
            {items.map((c) => (
              <div key={c.name} className="list-item clickable" onClick={() => editChannel(c)}>
                <div className="list-item-main">
                  <strong>{c.name}</strong>
                  <span className="chip chip-sm">{c.niche || "chưa đặt niche"}</span>
                </div>
                <div className="list-item-meta">
                  <span>{c.language} · {c.default_video_format}</span>
                  <span>Upload: <span className={`chip chip-sm chip-${c.upload_enabled ? "done" : "queued"}`}>{c.upload_enabled ? "BẬT" : "TẮT"}</span></span>
                </div>
              </div>
            ))}
            {items.length === 0 && <p className="text-muted">Chưa có kênh nào. Bấm "Tạo kênh mới" để bắt đầu.</p>}
          </div>
        </Card>

        {editing && (
          <Card title={form.name ? `Chỉnh sửa: ${form.name}` : "Tạo kênh mới"} right={<span className="chip chip-accent">{msg || "đang chỉnh sửa"}</span>}>
            <div className="form-grid">
              <FormField label="Tên kênh" value={form.name} onChange={(v) => f("name", v)} placeholder="ten_kenh_youtube" />
              <FormField label="Niche (chủ đề)" value={form.niche} onChange={(v) => f("niche", v)} placeholder="VD: space facts, animals..." />
              <FormField label="Ngôn ngữ video" value={form.language} onChange={(v) => f("language", v)} />
              <FormField label="Định dạng" value={form.default_video_format} onChange={(v) => f("default_video_format", v)} />
              <FormField label="Tiền tố tiêu đề" value={form.title_prefix} onChange={(v) => f("title_prefix", v)} />
              <FormField label="Category ID" value={form.category_id} onChange={(v) => f("category_id", v)} />
              <FormField label="Khoảng cách upload (phút)" value={form.publish_interval_minutes} onChange={(v) => f("publish_interval_minutes", v)} type="number" />
              <FormField label="Giới hạn upload/ngày" value={form.daily_upload_soft_limit} onChange={(v) => f("daily_upload_soft_limit", v)} type="number" />
              <FormField label="Tags (phẩy cách)" value={form.tags} onChange={(v) => f("tags", v)} />
              <FormField label="Từ bị chặn" value={form.blocked_words} onChange={(v) => f("blocked_words", v)} />
              <FormField label="Client secrets path" value={form.youtube_client_secrets} onChange={(v) => f("youtube_client_secrets", v)} />
              <FormField label="Token JSON path" value={form.youtube_token_json} onChange={(v) => f("youtube_token_json", v)} />
            </div>
            <div className="form-checks">
              <FormCheckbox label="Bật upload tự động" checked={form.upload_enabled} onChange={(v) => f("upload_enabled", v)} />
              <FormCheckbox label="Ghi nhận AI tạo" checked={form.disclose_synthetic_media} onChange={(v) => f("disclose_synthetic_media", v)} />
              <FormCheckbox label="Thông báo người đăng ký" checked={form.notify_subscribers} onChange={(v) => f("notify_subscribers", v)} />
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={submit}>Lưu kênh</button>
              <button className="btn" onClick={() => setEditing(false)}>Hủy</button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
