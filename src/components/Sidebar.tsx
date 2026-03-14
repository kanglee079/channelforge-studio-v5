import type { PageId } from "../App";

const NAV: { id: PageId; label: string; icon: string }[] = [
  { id: "dashboard",  label: "Tổng quan",          icon: "📊" },
  { id: "channels",   label: "Kênh",               icon: "📺" },
  { id: "workspaces", label: "Trình duyệt",        icon: "🌐" },
  { id: "jobs",       label: "Hàng đợi",           icon: "⚙️" },
  { id: "trends",     label: "Xu hướng",            icon: "📡" },
  { id: "research",   label: "Nghiên cứu",         icon: "📚" },
  { id: "content",    label: "Nội dung",            icon: "✍️" },
  { id: "factory",    label: "Sản xuất video",      icon: "🎬" },
  { id: "templates",  label: "Mẫu video",          icon: "🎨" },
  { id: "calendar",   label: "Lịch đăng",          icon: "📅" },
  { id: "analytics",  label: "Thống kê",           icon: "📈" },
  { id: "costs",      label: "Chi phí",            icon: "💰" },
  { id: "settings",   label: "Cài đặt",            icon: "⚙️" },
  { id: "logs",       label: "Nhật ký",            icon: "📋" },
];

interface Props { page: PageId; onChange: (p: PageId) => void; }

export function Sidebar({ page, onChange }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">CF</div>
        <div>
          <div className="sidebar-title">ChannelForge</div>
          <div className="sidebar-sub">Studio v5</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {NAV.map((item) => (
          <button
            key={item.id}
            className={`sidebar-item${page === item.id ? " active" : ""}`}
            onClick={() => onChange(item.id)}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
