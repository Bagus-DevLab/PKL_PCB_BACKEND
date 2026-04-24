import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

/**
 * Layout utama halaman admin.
 * Sidebar di kiri, konten di kanan.
 */
export default function AdminLayout({ user, onLogout }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar user={user} onLogout={onLogout} />
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
