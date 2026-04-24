import { NavLink } from "react-router-dom";
import { LayoutDashboard, Users, Cpu, LogOut, X } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
  { label: "Dashboard", to: "/admin/dashboard", icon: LayoutDashboard },
  { label: "Kelola User", to: "/admin/users", icon: Users },
  { label: "Kelola Device", to: "/admin/devices", icon: Cpu },
];

function SidebarContent({ user, onLogout, onClose }) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">PCB Admin</h1>
          <p className="text-xs text-slate-400 mt-0.5">Smart Kandang Panel</p>
        </div>
        {onClose && (
          <Button variant="ghost" size="icon-sm" onClick={onClose} className="lg:hidden">
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      <Separator />

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
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <Separator />

      {/* User Info + Logout */}
      <div className="p-4">
        <div className="mb-3 px-1">
          <p className="text-sm font-medium text-slate-900 truncate">
            {user?.full_name || user?.email}
          </p>
          <p className="text-xs text-slate-400 truncate">{user?.email}</p>
        </div>
        <Button
          variant="ghost"
          onClick={onLogout}
          className="w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50 text-sm"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Keluar
        </Button>
      </div>
    </div>
  );
}

export default function Sidebar({ user, onLogout, isOpen, onClose }) {
  return (
    <>
      {/* Desktop Sidebar — always visible on lg+ */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-slate-200 min-h-screen flex-col">
        <SidebarContent user={user} onLogout={onLogout} />
      </aside>

      {/* Mobile Drawer — overlay + slide-in */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
            />
            {/* Drawer */}
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="fixed top-0 left-0 bottom-0 w-72 bg-white border-r border-slate-200 z-50 lg:hidden shadow-xl"
            >
              <SidebarContent user={user} onLogout={onLogout} onClose={onClose} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
