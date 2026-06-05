import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import ToastContainer from "./ToastContainer";

export default function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-page">
        <Outlet />
      </main>
      <ToastContainer />
    </div>
  );
}
