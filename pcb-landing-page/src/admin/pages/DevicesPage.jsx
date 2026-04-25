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
import { Plus, Cpu, RefreshCw, Loader2, CheckCircle2, ShieldAlert } from "lucide-react";
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
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state
  const [macAddress, setMacAddress] = useState("");
  const [registering, setRegistering] = useState(false);

  // Cek role — hanya super_admin yang bisa register device
  const currentUser = JSON.parse(localStorage.getItem("user_info") || "{}");
  const isSuperAdmin = currentUser.role === "super_admin";

  const fetchDevices = async () => {
    try {
      const response = await deviceApi.getUnclaimed();
      setDevices(response.data);
    } catch (err) {
      setError(getErrorMessage(err, "Gagal memuat daftar device"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDevices(); }, []);

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

  // Auto-dismiss success after 5 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-pcb-primary">Kelola Device</h1>
        <p className="text-sm text-pcb-secondary mt-1">
          {isSuperAdmin ? "Daftarkan device baru dan lihat device yang belum diklaim" : "Lihat device yang belum diklaim"}
        </p>
      </div>

      {/* Register Form — hanya untuk Super Admin */}
      {isSuperAdmin ? (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Card className="mb-6 border-pcb-sage/30">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Plus className="w-4 h-4 text-slate-400" />
              <h3 className="text-sm font-semibold text-slate-900">Daftarkan Device Baru</h3>
            </div>
            <form onSubmit={handleRegister} className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 space-y-1.5">
                <Label htmlFor="mac" className="text-xs text-slate-500">MAC Address</Label>
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
                  {registering ? (
                    <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />Mendaftarkan...</>
                  ) : (
                    "Daftarkan"
                  )}
                </Button>
              </div>
            </form>

            {/* Success */}
            {success && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 p-2.5 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                {success}
              </motion.div>
            )}

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-3 p-2.5 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg flex justify-between items-center"
              >
                <span>{error}</span>
                <button onClick={() => setError(null)} className="text-xs underline ml-2">Tutup</button>
              </motion.div>
            )}
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

      {/* Unclaimed Devices Table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <Card className="border-pcb-sage/30">
          <CardContent className="p-0">
            {/* Table Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-slate-400" />
                <h3 className="text-sm font-semibold text-slate-900">
                  Device Belum Diklaim
                  {!loading && <span className="text-slate-400 font-normal ml-1">({devices.length})</span>}
                </h3>
              </div>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => { setLoading(true); fetchDevices(); }}
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </Button>
            </div>

            {loading ? (
              <TableSkeleton />
            ) : devices.length === 0 ? (
              <div className="p-12 text-center">
                <Cpu className="w-8 h-8 text-slate-200 mx-auto mb-3" />
                <p className="text-sm text-slate-400">Semua device sudah diklaim</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>MAC Address</TableHead>
                    <TableHead className="hidden sm:table-cell">Nama</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {devices.map((device, i) => (
                    <motion.tr
                      key={device.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors"
                    >
                      <TableCell className="font-mono text-sm">{device.mac_address}</TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-slate-500">{device.name || "-"}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-amber-600 border-amber-200 bg-amber-50 text-xs">
                          Belum Diklaim
                        </Badge>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
