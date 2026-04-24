import { NavLink } from "react-router-dom";
import { LayoutDashboard, Users, Cpu, LogOut, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
  { label: "Dashboard", to: "/admin/dashboard", icon: LayoutDashboard },
  { label: "Kelola User", to: "/admin/users", icon: Users },
  { label: "Kelola Device", to: "/admin/devices", icon: Cpu },
];

function SidebarContent({ user, onLogout, onClose }) {
  return (
    <div className="flex flex-col h-full bg-pcb-primary text-white">
      {/* Header */}
      <div className="p-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">PCB Admin</h1>
          <p className="text-xs text-pcb-sage mt-0.5">Smart Kandang Panel</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="lg:hidden text-pcb-sage hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="mx-4 border-t border-white/10" />

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-white/15 text-white shadow-sm"
                  : "text-pcb-sage hover:bg-white/10 hover:text-white"
              }`
            }
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mx-4 border-t border-white/10" />

      {/* User Info + Logout */}
      <div className="p-4">
        <div className="mb-3 px-1">
          <p className="text-sm font-medium text-white truncate">
            {user?.full_name || user?.email}
          </p>
          <p className="text-xs text-pcb-sage truncate">{user?.email}</p>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-pcb-sand hover:text-white hover:bg-white/10 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Keluar
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({ user, onLogout, isOpen, onClose }) {
  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 min-h-screen flex-col">
        <SidebarContent user={user} onLogout={onLogout} />
      </aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="fixed top-0 left-0 bottom-0 w-72 z-50 lg:hidden shadow-xl"
            >
              <SidebarContent user={user} onLogout={onLogout} onClose={onClose} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
