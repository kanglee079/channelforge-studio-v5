import { useEffect, useState } from "react";
import { api } from "./api/client";
import { ShellLayout } from "./layouts/ShellLayout";
import DashboardPage from "./pages/DashboardPage";
import ChannelsPage from "./pages/ChannelsPage";
import WorkspacesPage from "./pages/WorkspacesPage";
import JobsPage from "./pages/JobsPage";
import TrendsPage from "./pages/TrendsPage";
import ResearchPage from "./pages/ResearchPage";
import ContentPage from "./pages/ContentPage";
import FactoryPage from "./pages/FactoryPage";
import TemplatesPage from "./pages/TemplatesPage";
import CalendarPage from "./pages/CalendarPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import CostsPage from "./pages/CostsPage";
import SettingsPage from "./pages/SettingsPage";
import LogsPage from "./pages/LogsPage";
import ScenePlannerPage from "./pages/ScenePlannerPage";
import ReviewCenterPage from "./pages/ReviewCenterPage";
import MediaIntelligencePage from "./pages/MediaIntelligencePage";
import DiagnosticsPage from "./pages/DiagnosticsPage";

export type PageId =
  | "dashboard" | "channels" | "workspaces" | "trends"
  | "research" | "content" | "factory" | "templates"
  | "calendar" | "analytics" | "costs" | "settings" | "logs" | "jobs" | "scene-planner" | "review" | "media-intel" | "diagnostics";

export default function App() {
  const [page, setPage] = useState<PageId>("dashboard");
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let mounted = true;
    const check = () => {
      api.get<{ ok: boolean }>("/api/health")
        .then(() => mounted && setBackendStatus("online"))
        .catch(() => mounted && setBackendStatus("offline"));
    };
    check();
    const interval = setInterval(check, 8000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const renderPage = () => {
    switch (page) {
      case "dashboard": return <DashboardPage />;
      case "channels": return <ChannelsPage />;
      case "workspaces": return <WorkspacesPage />;
      case "jobs": return <JobsPage />;
      case "trends": return <TrendsPage />;
      case "research": return <ResearchPage />;
      case "content": return <ContentPage />;
      case "factory": return <FactoryPage />;
      case "templates": return <TemplatesPage />;
      case "calendar": return <CalendarPage />;
      case "analytics": return <AnalyticsPage />;
      case "costs": return <CostsPage />;
      case "settings": return <SettingsPage />;
      case "logs": return <LogsPage />;
      case "scene-planner": return <ScenePlannerPage />;
      case "review": return <ReviewCenterPage />;
      case "media-intel": return <MediaIntelligencePage />;
      case "diagnostics": return <DiagnosticsPage />;
      default: return <DashboardPage />;
    }
  };

  return (
    <ShellLayout page={page} onPageChange={setPage} backendStatus={backendStatus}>
      {renderPage()}
    </ShellLayout>
  );
}
