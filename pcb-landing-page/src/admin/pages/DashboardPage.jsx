import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Cpu, Wifi, WifiOff, ShieldCheck, Package } from "lucide-react";
import { adminApi } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await adminApi.getStats();
        setStats(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Gagal memuat data dashboard");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">Memuat dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
        {error}
      </div>
    );
  }

  const cards = [
    {
      title: "Total User",
      value: stats.total_users,
      icon: Users,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      title: "Admin",
      value: stats.total_admins,
      icon: ShieldCheck,
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
    {
      title: "Total Device",
      value: stats.total_devices,
      icon: Cpu,
      color: "text-slate-600",
      bg: "bg-slate-100",
    },
    {
      title: "Device Diklaim",
      value: stats.total_devices_claimed,
      icon: Package,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      title: "Device Belum Diklaim",
      value: stats.total_devices_unclaimed,
      icon: Package,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
    {
      title: "Device Online",
      value: stats.total_devices_online,
      icon: Wifi,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
    },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Ringkasan sistem PCB Smart Kandang</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <Card key={card.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">
                    {card.title}
                  </p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">
                    {card.value}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${card.bg}`}>
                  <card.icon className={`w-6 h-6 ${card.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
