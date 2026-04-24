import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ShieldCheck, User } from "lucide-react";
import { adminApi, userApi } from "@/lib/api";

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    fetchUsers();
  }, []);

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
      // Refresh list
      await fetchUsers();
      setDialogOpen(false);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Gagal mengubah role user"
      );
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">Memuat daftar user...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Kelola User</h1>
        <p className="text-slate-500 mt-1">
          Manage role user di sistem ({users.length} user terdaftar)
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 underline"
          >
            Tutup
          </button>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Nama</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead className="text-right">Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.email}</TableCell>
                  <TableCell>{user.full_name || "-"}</TableCell>
                  <TableCell>
                    {user.role === "admin" ? (
                      <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                        <ShieldCheck className="w-3 h-3 mr-1" />
                        Admin
                      </Badge>
                    ) : (
                      <Badge variant="outline">
                        <User className="w-3 h-3 mr-1" />
                        User
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-slate-500">
                    {user.provider}
                  </TableCell>
                  <TableCell className="text-right">
                    {user.id === currentUser.id ? (
                      <span className="text-xs text-slate-400">Anda</span>
                    ) : user.role === "admin" ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openRoleDialog(user, "user")}
                      >
                        Jadikan User
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openRoleDialog(user, "admin")}
                      >
                        Jadikan Admin
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Konfirmasi Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ubah Role User</DialogTitle>
            <DialogDescription>
              Apakah kamu yakin ingin mengubah role{" "}
              <strong>{selectedUser?.email}</strong> menjadi{" "}
              <strong>{newRole}</strong>?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={updating}
            >
              Batal
            </Button>
            <Button onClick={handleUpdateRole} disabled={updating}>
              {updating ? "Memproses..." : "Ya, Ubah Role"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
