import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Plus, Cpu, RefreshCw } from "lucide-react";
import { deviceApi } from "@/lib/api";

export default function DevicesPage() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state
  const [macAddress, setMacAddress] = useState("");
  const [registering, setRegistering] = useState(false);

  const fetchDevices = async () => {
    try {
      const response = await deviceApi.getUnclaimed();
      setDevices(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Gagal memuat daftar device");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegistering(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await deviceApi.register(macAddress);
      setSuccess(
        `Device ${response.data.mac_address} berhasil didaftarkan!`
      );
      setMacAddress("");
      // Refresh list
      await fetchDevices();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Gagal mendaftarkan device"
      );
    } finally {
      setRegistering(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Kelola Device</h1>
        <p className="text-slate-500 mt-1">
          Daftarkan device baru dan lihat device yang belum diklaim
        </p>
      </div>

      {/* Register Device Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Daftarkan Device Baru
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRegister} className="flex gap-4 items-end">
            <div className="flex-1 space-y-2">
              <Label htmlFor="mac">MAC Address</Label>
              <Input
                id="mac"
                placeholder="AA:BB:CC:DD:EE:FF atau AABBCCDDEEFF"
                value={macAddress}
                onChange={(e) => setMacAddress(e.target.value)}
                required
                disabled={registering}
              />
            </div>
            <Button type="submit" disabled={registering}>
              {registering ? "Mendaftarkan..." : "Daftarkan"}
            </Button>
          </form>

          {success && (
            <div className="mt-4 p-3 text-sm text-green-600 bg-green-50 border border-green-200 rounded-lg">
              {success}
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg">
              {error}
              <button
                onClick={() => setError(null)}
                className="ml-2 underline"
              >
                Tutup
              </button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Unclaimed Devices Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              Device Belum Diklaim ({devices.length})
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setLoading(true);
                fetchDevices();
              }}
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-slate-500">
              Memuat daftar device...
            </div>
          ) : devices.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              Semua device sudah diklaim. Tidak ada device yang tersedia.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>MAC Address</TableHead>
                  <TableHead>Nama</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {devices.map((device) => (
                  <TableRow key={device.id}>
                    <TableCell className="font-mono text-sm">
                      {device.mac_address}
                    </TableCell>
                    <TableCell>{device.name || "-"}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-amber-600 border-amber-300">
                        Belum Diklaim
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
