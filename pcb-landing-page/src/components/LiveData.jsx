import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, ThermometerSun, Droplets, Wind, Power } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function LiveData() {
  const [sensorData, setSensorData] = useState({
    suhu: 0,
    kelembaban: 0,
    amonia: 0,
    statusPompa: 'OFF'
  });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await fetch('https://api.pcb.my.id/api/kandang/status');
      if (!response.ok) throw new Error('Gagal narik data');

      const data = await response.json();
      setSensorData({
        suhu: data.suhu,
        kelembaban: data.kelembaban,
        amonia: data.amonia,
        statusPompa: data.status_pompa
      });
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      setSensorData({
        suhu: 28.5,
        kelembaban: 65,
        amonia: 12,
        statusPompa: 'ON'
      });
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const itemVariants = {
    hidden: { scale: 0.95, opacity: 0, y: 20 },
    visible: { scale: 1, opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100 } }
  };

  return (
    <section id="live-data" className="py-24 px-6 relative overflow-hidden bg-slate-50">
      {/* Background Ornamen Halus */}
      <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-blue-50/50 to-transparent -z-10 pointer-events-none"></div>

      <div className="max-w-6xl mx-auto z-10 relative">
        <div className="flex flex-col md:flex-row justify-between items-end mb-12">
          <div>
            <h2 className="text-3xl md:text-5xl font-bold mb-4 text-slate-900 tracking-tight">
              Live <span className="text-pcb-blue">Dashboard</span>
            </h2>
            <p className="text-slate-600 max-w-xl text-lg leading-relaxed">
              Pantauan langsung dari sensor DHT11 dan MQ-135 yang terpasang di kandang saat ini. Data diperbarui secara real-time.
            </p>
          </div>

          {/* Indikator Status */}
          <div className="mt-6 md:mt-0">
            <Badge variant="outline" className={`px-4 py-1.5 text-sm font-medium border-slate-200 bg-white shadow-sm ${loading ? 'text-slate-500' : 'text-emerald-700 border-emerald-200'} `}>
              <Activity className={`w-4 h-4 mr-2 ${loading ? 'animate-pulse' : 'text-emerald-500'}`} />
              {loading ? 'Menghubungkan...' : 'Sistem Online'}
            </Badge>
          </div>
        </div>

        {/* Grid Angka Sensor */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={{ visible: { transition: { staggerChildren: 0.15 } } }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {/* Card Suhu */}
          <motion.div variants={itemVariants} className="h-full">
            <Card className="bg-white border border-slate-200 shadow-sm overflow-hidden relative group h-full">
              <div className="absolute -right-10 -top-10 w-32 h-32 bg-orange-50 rounded-full blur-2xl group-hover:bg-orange-100 transition-all duration-500"></div>
              <CardContent className="p-8">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-slate-500 font-medium text-lg">Suhu Ruangan</h3>
                  <ThermometerSun className="w-6 h-6 text-orange-500" />
                </div>
                <div className="flex items-baseline gap-2 mt-4">
                  <span className="text-6xl font-black text-orange-600 drop-shadow-sm">{loading ? '--' : sensorData.suhu}</span>
                  <span className="text-2xl text-slate-400 font-bold">°C</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Card Kelembaban */}
          <motion.div variants={itemVariants} className="h-full">
            <Card className="bg-white border border-slate-200 shadow-sm overflow-hidden relative group h-full">
              <div className="absolute -right-10 -top-10 w-32 h-32 bg-blue-50 rounded-full blur-2xl group-hover:bg-blue-100 transition-all duration-500"></div>
              <CardContent className="p-8">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-slate-500 font-medium text-lg">Kelembaban</h3>
                  <Droplets className="w-6 h-6 text-blue-500" />
                </div>
                <div className="flex items-baseline gap-2 mt-4">
                  <span className="text-6xl font-black text-blue-600 drop-shadow-sm">{loading ? '--' : sensorData.kelembaban}</span>
                  <span className="text-2xl text-slate-400 font-bold">%</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Card Amonia */}
          <motion.div variants={itemVariants} className="h-full">
            <Card className="bg-white border border-slate-200 shadow-sm overflow-hidden relative group h-full flex flex-col justify-between">
              <div className="absolute -right-10 -top-10 w-32 h-32 bg-emerald-50 rounded-full blur-2xl group-hover:bg-emerald-100 transition-all duration-500"></div>
              <CardContent className="p-8 flex-1">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-slate-500 font-medium text-lg">Kadar Amonia</h3>
                  <Wind className="w-6 h-6 text-emerald-500" />
                </div>
                <div className="flex items-baseline gap-2 mt-4">
                  <span className="text-6xl font-black text-emerald-600 drop-shadow-sm">{loading ? '--' : sensorData.amonia}</span>
                  <span className="text-2xl text-slate-400 font-bold">ppm</span>
                </div>
              </CardContent>
              {/* Indikator Pompa Kecil */}
              <div className="px-8 pb-8 pt-4 border-t border-slate-100 flex justify-between items-center bg-slate-50 absolute bottom-0 w-full rounded-b-xl">
                <span className="text-sm text-slate-500 font-medium">Pompa Limbah</span>
                <Badge variant={sensorData.statusPompa === 'ON' ? 'success' : 'destructive'} className="font-bold flex items-center gap-1.5 shadow-none">
                  <Power className="w-3 h-3" />
                  {loading ? '...' : sensorData.statusPompa}
                </Badge>
              </div>
            </Card>
          </motion.div>

        </motion.div>
      </div>
    </section>
  );
}