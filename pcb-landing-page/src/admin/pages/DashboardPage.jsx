import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import AnimatedCounter from "@/components/shared/AnimatedCounter";
import { Users, Cpu, Wifi, ShieldCheck, Package, TrendingUp, Crown, Wrench, Eye, Link2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { adminApi, getErrorMessage } from "@/lib/api";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

function StatCardSkeleton() {
  return (
    <Card className="border-slate-200/60">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-12" />
          </div>
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
      </CardContent>
    </Card>
  );
}

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
        setError(getErrorMessage(err, "Gagal memuat data dashboard"));
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
        {error}
      </div>
    );
  }

  const cards = stats
    ? [
        { title: "Total User", value: stats.total_users, icon: Users, color: "text-pcb-primary", bg: "bg-pcb-mint/40" },
        { title: "Super Admin", value: stats.total_super_admins, icon: Crown, color: "text-pcb-sand", bg: "bg-pcb-sand/20" },
        { title: "Admin", value: stats.total_admins, icon: ShieldCheck, color: "text-pcb-primary", bg: "bg-pcb-primary/10" },
        { title: "Operator", value: stats.total_operators, icon: Wrench, color: "text-pcb-secondary", bg: "bg-pcb-sage/30" },
        { title: "Viewer", value: stats.total_viewers, icon: Eye, color: "text-pcb-secondary", bg: "bg-pcb-mint/50" },
        { title: "Total Device", value: stats.total_devices, icon: Cpu, color: "text-pcb-primary", bg: "bg-pcb-sage/20" },
        { title: "Diklaim", value: stats.total_devices_claimed, icon: Package, color: "text-pcb-primary", bg: "bg-pcb-mint/40" },
        { title: "Belum Diklaim", value: stats.total_devices_unclaimed, icon: Package, color: "text-pcb-sand", bg: "bg-pcb-sand/15" },
        { title: "Online", value: stats.total_devices_online, icon: Wifi, color: "text-pcb-primary", bg: "bg-pcb-mint/50" },
        { title: "Assignments", value: stats.total_assignments, icon: Link2, color: "text-pcb-secondary", bg: "bg-pcb-sage/20" },
      ]
    : [];

  // Chart data from stats
  const chartData = stats
    ? [
        { name: "Users", value: stats.total_users, fill: "#3F4739" },
        { name: "Admin", value: stats.total_admins, fill: "#717568" },
        { name: "Operator", value: stats.total_operators, fill: "#BACBA9" },
        { name: "Viewer", value: stats.total_viewers, fill: "#E1F4CB" },
        { name: "Device", value: stats.total_devices, fill: "#3F4739" },
        { name: "Online", value: stats.total_devices_online, fill: "#F1BF98" },
      ]
    : [];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">Ringkasan sistem PCB Smart Kandang</p>
      </div>

      {/* Stat Cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {cards.map((card) => (
            <motion.div key={card.title} variants={cardVariants}>
              <Card className="border-pcb-sage/30 hover:border-pcb-sage/60 transition-colors">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                        {card.title}
                      </p>
                      <div className="text-3xl font-bold text-slate-900 mt-1">
                        <AnimatedCounter value={card.value} />
                      </div>
                    </div>
                    <div className={`p-2.5 rounded-lg ${card.bg}`}>
                      <card.icon className={`w-5 h-5 ${card.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Chart */}
      {!loading && stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-8"
        >
          <Card className="border-pcb-sage/30">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-6">
                <TrendingUp className="w-4 h-4 text-pcb-secondary" />
                <h3 className="text-sm font-semibold text-pcb-primary">Ringkasan Sistem</h3>
              </div>
              <div className="h-64 min-h-[256px]">
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <BarChart data={chartData} barSize={32}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 12, fill: "#94a3b8" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: "#94a3b8" }}
                      axisLine={false}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#fff",
                        border: "1px solid #e2e8f0",
                        borderRadius: "8px",
                        fontSize: "12px",
                        boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.05)",
                      }}
                    />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
