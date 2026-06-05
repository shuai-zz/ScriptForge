import { Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import ProviderConfig from "./pages/ProviderConfig";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects/:projectId/providers" element={<ProviderConfig />} />
      </Route>
    </Routes>
  );
}
