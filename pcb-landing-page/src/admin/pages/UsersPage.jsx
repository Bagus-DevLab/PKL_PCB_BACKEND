import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { ShieldCheck, User, RefreshCw, CloudDownload, Search, Loader2, Crown, Wrench, Eye } from "lucide-react";
import { adminApi, userApi } from "@/lib/api";

function TableSkeleton() {
  return (
    <div className="p-4 space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-24 ml-auto rounded-md" />
        </div>
      ))}
    </div>
  );
}

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Sync state
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newRole, setNewRole] = useState("");
  const [updating, setUpdating] = useState(false);

  const currentUser = JSON.parse(localStorage.getItem("user_info") || "{}");

  const fetchUsers = async () => {
    try {
      const response = await adminApi.getAllUsers();
      setUsers(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal memuat daftar user");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  // Filtered users based on search
  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) return users;
    const q = searchQuery.toLowerCase();
    return users.filter(
      (u) =>
        u.email.toLowerCase().includes(q) ||
        (u.full_name && u.full_name.toLowerCase().includes(q))
    );
  }, [users, searchQuery]);

  const handleSyncFirebase = async () => {
    setSyncing(true);
    setError(null);
    setSyncResult(null);
    try {
      const response = await adminApi.syncFirebaseUsers();
      setSyncResult(response.data);
      await fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal sync user dari Firebase");
    } finally {
      setSyncing(false);
    }
  };

  const openRoleDialog = (user, role) => {
    setSelectedUser(user);
    setNewRole(role);
    setDialogOpen(true);
  };

  const handleUpdateRole = async () => {
    if (!selectedUser) return;
    setUpdating(true);
    try {
      await userApi.updateRole(selectedUser.id, newRole);
      await fetchUsers();
      setDialogOpen(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal mengubah role user");
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Kelola User</h1>
          <p className="text-sm text-slate-400 mt-1">
            {users.length} user terdaftar
          </p>
        </div>
        <Button onClick={handleSyncFirebase} disabled={syncing} variant="outline" size="sm">
          {syncing ? (
            <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
          ) : (
            <CloudDownload className="w-3.5 h-3.5 mr-2" />
          )}
          {syncing ? "Menyinkronkan..." : "Sync Firebase"}
        </Button>
      </div>

      {/* Sync Result */}
      {syncResult && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm"
        >
          <p className="font-medium text-green-800">Sync selesai!</p>
          <p className="text-green-600 mt-0.5">
            {syncResult.synced_count} baru, {syncResult.skipped_count} sudah ada
            {syncResult.failed_count > 0 && `, ${syncResult.failed_count} gagal`}
          </p>
          <button onClick={() => setSyncResult(null)} className="text-xs text-green-500 underline mt-1">Tutup</button>
        </motion.div>
      )}

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg flex justify-between items-center"
        >
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xs underline ml-2">Tutup</button>
        </motion.div>
      )}

      {/* Search */}
      <div className="mb-4 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="Cari berdasarkan email atau nama..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 h-9"
        />
      </div>

      {/* Table */}
      <Card className="border-slate-200/60">
        <CardContent className="p-0">
          {loading ? (
            <TableSkeleton />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead className="hidden sm:table-cell">Nama</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead className="hidden md:table-cell">Provider</TableHead>
                  <TableHead className="text-right">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-slate-400">
                      {searchQuery ? "Tidak ada user yang cocok" : "Belum ada user terdaftar"}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsers.map((user, i) => (
                    <motion.tr
                      key={user.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors"
                    >
                      <TableCell className="font-medium text-sm">{user.email}</TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-slate-500">{user.full_name || "-"}</TableCell>
                      <TableCell>
                        {(() => {
                          const roleConfig = {
                            super_admin: { icon: Crown, label: "Super Admin", cls: "bg-red-100 text-red-700 hover:bg-red-100" },
                            admin: { icon: ShieldCheck, label: "Admin", cls: "bg-purple-100 text-purple-700 hover:bg-purple-100" },
                            operator: { icon: Wrench, label: "Operator", cls: "bg-blue-100 text-blue-700 hover:bg-blue-100" },
                            viewer: { icon: Eye, label: "Viewer", cls: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100" },
                            user: { icon: User, label: "User", cls: "" },
                          };
                          const cfg = roleConfig[user.role] || roleConfig.user;
                          const Icon = cfg.icon;
                          return user.role === "user" ? (
                            <Badge variant="outline" className="text-xs"><Icon className="w-3 h-3 mr-1" />{cfg.label}</Badge>
                          ) : (
                            <Badge className={`text-xs ${cfg.cls}`}><Icon className="w-3 h-3 mr-1" />{cfg.label}</Badge>
                          );
                        })()}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-xs text-slate-400">{user.provider}</TableCell>
                      <TableCell className="text-right">
                        {user.id === currentUser.id ? (
                          <span className="text-xs text-slate-300">Anda</span>
                        ) : user.role === "super_admin" ? (
                          <span className="text-xs text-slate-300">Super Admin</span>
                        ) : (
                          <select
                            className="text-xs border border-slate-200 rounded-md px-2 py-1 bg-white text-slate-700 cursor-pointer hover:border-slate-300"
                            value={user.role}
                            onChange={(e) => openRoleDialog(user, e.target.value)}
                          >
                            {currentUser.role === "super_admin" ? (
                              <>
                                <option value="admin">Admin</option>
                                <option value="operator">Operator</option>
                                <option value="viewer">Viewer</option>
                                <option value="user">User</option>
                              </>
                            ) : (
                              <>
                                <option value="operator">Operator</option>
                                <option value="viewer">Viewer</option>
                                <option value="user">User</option>
                              </>
                            )}
                          </select>
                        )}
                      </TableCell>
                    </motion.tr>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Confirm Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ubah Role User</DialogTitle>
            <DialogDescription>
              Ubah role <strong>{selectedUser?.email}</strong> menjadi <strong>{newRole}</strong>?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={updating}>Batal</Button>
            <Button onClick={handleUpdateRole} disabled={updating}>
              {updating ? <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Memproses...</> : "Ya, Ubah Role"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
