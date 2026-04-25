import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Plus, Cpu, RefreshCw, Loader2, CheckCircle2, ShieldAlert, Pencil, Trash2, Wifi, WifiOff } from "lucide-react";
import { deviceApi, getErrorMessage } from "@/lib/api";

function TableSkeleton() {
  return (
    <div className="p-4 space-y-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export default function DevicesPage() {
  const [allDevices, setAllDevices] = useState([]);
  const [unclaimedDevices, setUnclaimedDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState("all"); // "all" | "unclaimed"

  // Register form state
  const [macAddress, setMacAddress] = useState("");
  const [registering, setRegistering] = useState(false);

  // Edit dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editDevice, setEditDevice] = useState(null);
  const [editName, setEditName] = useState("");
  const [editing, setEditing] = useState(false);

  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteDevice, setDeleteDevice] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const currentUser = JSON.parse(localStorage.getItem("user_info") || "{}");
  const isSuperAdmin = currentUser.role === "super_admin";

  const fetchDevices = async () => {
    try {
      const [allRes, unclaimedRes] = await Promise.all([
        deviceApi.getAll(1, 100),
        deviceApi.getUnclaimed(1, 100),
      ]);
      setAllDevices(allRes.data.data || allRes.data);
      setUnclaimedDevices(unclaimedRes.data.data || unclaimedRes.data);
    } catch (err) {
      setError(getErrorMessage(err, "Gagal memuat daftar device"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDevices(); }, []);

  // Auto-dismiss success
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  // Register device
  const handleRegister = async (e) => {
    e.preventDefault();
    setRegistering(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await deviceApi.register(macAddress);
      setSuccess(`Device ${response.data.mac_address} berhasil didaftarkan!`);
      setMacAddress("");
      await fetchDevices();
    } catch (err) {
      setError(getErrorMessage(err, "Gagal mendaftarkan device"));
    } finally {
      setRegistering(false);
    }
  };

  // Edit device
  const openEditDialog = (device) => {
    setEditDevice(device);
    setEditName(device.name || "");
    setEditDialogOpen(true);
  };

  const handleEdit = async () => {
    if (!editDevice || !editName.trim()) return;
    setEditing(true);
    try {
      await deviceApi.update(editDevice.id, editName.trim());
      setSuccess(`Device berhasil diubah menjadi "${editName.trim()}"`);
      setEditDialogOpen(false);
      await fetchDevices();
    } catch (err) {
      setError(getErrorMessage(err, "Gagal mengubah nama device"));
    } finally {
      setEditing(false);
    }
  };

  // Delete device
  const openDeleteDialog = (device) => {
    setDeleteDevice(device);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    if (!deleteDevice) return;
    setDeleting(true);
    try {
      const res = await deviceApi.remove(deleteDevice.id);
      setSuccess(res.data.message);
      setDeleteDialogOpen(false);
      await fetchDevices();
    } catch (err) {
      setError(getErrorMessage(err, "Gagal menghapus device"));
    } finally {
      setDeleting(false);
    }
  };

  const tabs = [
    { id: "all", label: `Semua Device (${allDevices.length})` },
    { id: "unclaimed", label: `Belum Diklaim (${unclaimedDevices.length})` },
  ];

  const currentDevices = activeTab === "all" ? allDevices : unclaimedDevices;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-pcb-primary">Kelola Device</h1>
        <p className="text-sm text-pcb-secondary mt-1">
          {isSuperAdmin ? "Daftarkan, edit, dan hapus device" : "Kelola device yang terdaftar"}
        </p>
      </div>

      {/* Register Form — Super Admin only */}
      {isSuperAdmin ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="mb-6 border-pcb-sage/30">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Plus className="w-4 h-4 text-pcb-secondary" />
                <h3 className="text-sm font-semibold text-pcb-primary">Daftarkan Device Baru</h3>
              </div>
              <form onSubmit={handleRegister} className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 space-y-1.5">
                  <Label htmlFor="mac" className="text-xs text-pcb-secondary">MAC Address</Label>
                  <Input
                    id="mac"
                    placeholder="AA:BB:CC:DD:EE:FF atau AABBCCDDEEFF"
                    value={macAddress}
                    onChange={(e) => setMacAddress(e.target.value)}
                    required
                    disabled={registering}
                    className="h-9 font-mono text-sm"
                  />
                </div>
                <div className="flex items-end">
                  <Button type="submit" disabled={registering} size="sm" className="h-9">
                    {registering ? <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Mendaftarkan...</> : "Daftarkan"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
        <div className="mb-6 p-4 bg-pcb-mint/30 border border-pcb-sage/30 rounded-lg flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-pcb-secondary shrink-0" />
          <p className="text-sm text-pcb-secondary">
            Hanya <strong className="text-pcb-primary">Super Admin</strong> yang bisa mendaftarkan device baru.
          </p>
        </div>
      )}

      {/* Success / Error */}
      {success && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />{success}
        </motion.div>
      )}
      {error && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xs underline ml-2">Tutup</button>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-pcb-mint/20 p-1 rounded-lg w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === tab.id
                ? "bg-white text-pcb-primary shadow-sm"
                : "text-pcb-secondary hover:text-pcb-primary"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Device Table */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <Card className="border-pcb-sage/30">
          <CardContent className="p-0">
            {/* Table Header */}
            <div className="flex items-center justify-between p-4 border-b border-pcb-sage/20">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-pcb-secondary" />
                <h3 className="text-sm font-semibold text-pcb-primary">
                  {activeTab === "all" ? "Semua Device" : "Device Belum Diklaim"}
                </h3>
              </div>
              <Button variant="ghost" size="icon-sm" onClick={() => { setLoading(true); fetchDevices(); }}>
                <RefreshCw className="w-3.5 h-3.5" />
              </Button>
            </div>

            {loading ? (
              <TableSkeleton />
            ) : currentDevices.length === 0 ? (
              <div className="p-12 text-center">
                <Cpu className="w-8 h-8 text-pcb-sage mx-auto mb-3" />
                <p className="text-sm text-pcb-secondary">
                  {activeTab === "all" ? "Belum ada device terdaftar" : "Semua device sudah diklaim"}
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>MAC Address</TableHead>
                    <TableHead className="hidden sm:table-cell">Nama</TableHead>
                    <TableHead>Status</TableHead>
                    {activeTab === "all" && <TableHead className="hidden md:table-cell">Pemilik</TableHead>}
                    <TableHead className="text-right">Aksi</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentDevices.map((device, i) => (
                    <motion.tr
                      key={device.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.03 }}
                      className="border-b border-pcb-sage/10 hover:bg-pcb-mint/10 transition-colors"
                    >
                      <TableCell className="font-mono text-sm">{device.mac_address}</TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-pcb-secondary">{device.name || "-"}</TableCell>
                      <TableCell>
                        {device.user_id ? (
                          device.is_online ? (
                            <Badge className="bg-pcb-mint/50 text-pcb-primary hover:bg-pcb-mint/50 text-xs">
                              <Wifi className="w-3 h-3 mr-1" />Online
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-pcb-secondary text-xs">
                              <WifiOff className="w-3 h-3 mr-1" />Offline
                            </Badge>
                          )
                        ) : (
                          <Badge variant="outline" className="text-pcb-sand border-pcb-sand/40 text-xs">
                            Belum Diklaim
                          </Badge>
                        )}
                      </TableCell>
                      {activeTab === "all" && (
                        <TableCell className="hidden md:table-cell text-xs text-pcb-secondary">
                          {device.user_id ? "Diklaim" : "-"}
                        </TableCell>
                      )}
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => openEditDialog(device)}
                            title="Edit nama"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </Button>
                          {isSuperAdmin && (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => openDeleteDialog(device)}
                              className="text-red-500 hover:text-red-600 hover:bg-red-50"
                              title="Hapus device"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Nama Device</DialogTitle>
            <DialogDescription>
              Ubah nama untuk device <strong className="font-mono">{editDevice?.mac_address}</strong>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label htmlFor="edit-name" className="text-xs text-pcb-secondary">Nama Baru</Label>
            <Input
              id="edit-name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="Masukkan nama device"
              disabled={editing}
              className="h-9"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={editing}>Batal</Button>
            <Button onClick={handleEdit} disabled={editing || !editName.trim()}>
              {editing ? <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Menyimpan...</> : "Simpan"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">Hapus Device</DialogTitle>
            <DialogDescription>
              Apakah kamu yakin ingin menghapus device <strong className="font-mono">{deleteDevice?.mac_address}</strong>
              {deleteDevice?.name && <> (<strong>{deleteDevice.name}</strong>)</>}?
              <br /><br />
              <span className="text-red-500 font-medium">
                Semua data sensor logs dan assignments akan ikut terhapus. Operasi ini tidak bisa dibatalkan.
              </span>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} disabled={deleting}>Batal</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting ? <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Menghapus...</> : "Ya, Hapus Device"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
