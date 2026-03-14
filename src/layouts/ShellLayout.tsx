import type { ReactNode } from "react";
import type { PageId } from "../App";
import { Sidebar } from "../components/Sidebar";

interface Props {
  page: PageId;
  onPageChange: (p: PageId) => void;
  backendStatus: "checking" | "online" | "offline";
  children: ReactNode;
}

const STATUS_MAP = {
  online: { color: "var(--green)", text: "Đang chạy" },
  offline: { color: "var(--red)", text: "Ngắt kết nối" },
  checking: { color: "var(--yellow)", text: "Đang kiểm tra" },
};

export function ShellLayout({ page, onPageChange, backendStatus, children }: Props) {
  const s = STATUS_MAP[backendStatus];

  return (
    <div className="shell">
      <Sidebar page={page} onChange={onPageChange} />
      <main className="shell-main">
        <header className="topbar">
          <div className="topbar-left">
            <span className="status-dot" style={{ background: s.color }} />
            <span className="topbar-label">Máy chủ: <strong>{s.text}</strong></span>
          </div>
          <div className="topbar-right">
            <span className="chip chip-accent">v5.0</span>
            <span className="chip">Tauri + React + Python</span>
          </div>
        </header>
        <div className="shell-content">
          {children}
        </div>
      </main>
    </div>
  );
}
