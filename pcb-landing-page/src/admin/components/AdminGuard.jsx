import { Navigate } from "react-router-dom";

/**
 * Proteksi route admin.
 * Jika belum login atau bukan admin, redirect ke /admin/login.
 */
export default function AdminGuard({ user, loading, children }) {
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-500">Memuat...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/admin/login" replace />;
  }

  if (user.role !== "admin") {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
}
