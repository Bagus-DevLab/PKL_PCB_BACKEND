import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import Sidebar from "./Sidebar";
import PageTransition from "@/components/shared/PageTransition";

const pageTitles = {
  "/admin/dashboard": "Dashboard",
  "/admin/users": "Kelola User",
  "/admin/devices": "Kelola Device",
};

export default function AdminLayout({ user, onLogout }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const pageTitle = pageTitles[location.pathname] || "Admin";

  return (
    <div className="flex min-h-screen bg-pcb-mint/10">
      <Sidebar
        user={user}
        onLogout={onLogout}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-pcb-sage/30 px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden"
            >
              <Menu className="w-4 h-4" />
            </Button>
            <h1 className="text-sm font-semibold text-pcb-primary">{pageTitle}</h1>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 text-xs text-pcb-secondary">
              <Cpu className="w-3.5 h-3.5" />
              <span>PCB Admin</span>
            </div>
            <div className="w-7 h-7 rounded-full bg-pcb-primary flex items-center justify-center text-white text-xs font-medium">
              {(user?.full_name || user?.email || "A").charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
          <PageTransition key={location.pathname}>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  );
}
