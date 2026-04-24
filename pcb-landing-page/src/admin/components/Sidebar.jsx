import { NavLink } from "react-router-dom";
import { LayoutDashboard, Users, Cpu, LogOut } from "lucide-react";
import { Separator } from "@/components/ui/separator";

const navItems = [
  {
    label: "Dashboard",
    to: "/admin/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Kelola User",
    to: "/admin/users",
    icon: Users,
  },
  {
    label: "Kelola Device",
    to: "/admin/devices",
    icon: Cpu,
  },
];

export default function Sidebar({ user, onLogout }) {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 min-h-screen flex flex-col">
      {/* Header */}
      <div className="p-6">
        <h1 className="text-lg font-bold text-slate-900">PCB Admin</h1>
        <p className="text-sm text-slate-500 mt-1">Smart Kandang Panel</p>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <Separator />

      {/* User Info + Logout */}
      <div className="p-4">
        <div className="mb-3">
          <p className="text-sm font-medium text-slate-900 truncate">
            {user?.full_name || user?.email}
          </p>
          <p className="text-xs text-slate-500 truncate">{user?.email}</p>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Keluar
        </button>
      </div>
    </aside>
  );
}
