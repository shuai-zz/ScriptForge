import { Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ChaptersPage from "./pages/Chapters";
import Dashboard from "./pages/Dashboard";
import PipelineProgress from "./pages/PipelineProgress";
import ProjectSettings from "./pages/ProjectSettings";
import ProviderConfig from "./pages/ProviderConfig";
import ScriptEditor from "./pages/ScriptEditor";
import VersionHistory from "./pages/VersionHistory";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects/:projectId" element={<ChaptersPage />} />
        <Route path="/projects/:projectId/settings" element={<ProjectSettings />} />
        <Route path="/projects/:projectId/providers" element={<ProviderConfig />} />
        <Route path="/projects/:projectId/convert" element={<PipelineProgress />} />
        <Route path="/projects/:projectId/script" element={<ScriptEditor />} />
        <Route path="/projects/:projectId/versions" element={<VersionHistory />} />
      </Route>
    </Routes>
  );
}
