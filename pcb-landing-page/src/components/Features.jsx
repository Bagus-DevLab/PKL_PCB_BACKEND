import React from 'react';
import { motion } from 'framer-motion';
import { ThermometerSun, Droplets, Wind, Waves, Lightbulb, Wheat } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

const featuresData = [
  {
    title: 'Monitoring Suhu',
    description: 'Pemantauan suhu kandang secara berkala untuk menjaga iklim tetap stabil dan nyaman bagi ternak.',
    icon: ThermometerSun,
    textColor: 'text-orange-600',
    iconBg: 'bg-orange-50',
    borderColor: 'border-orange-100',
  },
  {
    title: 'Monitoring Kelembaban',
    description: 'Pengawasan kelembaban udara untuk mencegah pertumbuhan jamur dan bakteri di lingkungan kandang.',
    icon: Droplets,
    textColor: 'text-blue-600',
    iconBg: 'bg-blue-50',
    borderColor: 'border-blue-100',
  },
  {
    title: 'Monitoring Amonia',
    description: 'Deteksi kadar amonia dari kotoran ayam untuk menjaga kualitas udara dan kesehatan pernapasan.',
    icon: Wind,
    textColor: 'text-emerald-600',
    iconBg: 'bg-emerald-50',
    borderColor: 'border-emerald-100',
  },
  {
    title: 'Kontrol Pompa Pembersih',
    description: 'Aktivasi pompa pembersih kotoran secara otomatis berdasarkan kondisi kandang dan jadwal yang ditentukan.',
    icon: Waves,
    textColor: 'text-cyan-600',
    iconBg: 'bg-cyan-50',
    borderColor: 'border-cyan-100',
  },
  {
    title: 'Manajemen Lampu Kandang',
    description: 'Pengaturan jadwal dan intensitas lampu untuk mendukung siklus istirahat dan pertumbuhan ayam.',
    icon: Lightbulb,
    textColor: 'text-amber-500',
    iconBg: 'bg-amber-50',
    borderColor: 'border-amber-100',
  },
  {
    title: 'Otomatisasi Pakan',
    description: 'Distribusi pakan terjadwal dengan kontrol yang mudah melalui dashboard untuk memastikan asupan selalu cukup.',
    icon: Wheat,
    textColor: 'text-indigo-600',
    iconBg: 'bg-indigo-50',
    borderColor: 'border-indigo-100',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
};

export default function Features() {
  return (
    <section id="fitur" className="py-24 px-6 bg-white relative overflow-hidden">
      {/* Dekorasi Background Sangat Halus */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-50/50 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-orange-50/50 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-bold mb-4 text-slate-900 tracking-tight">
            Fitur Utama <span className="text-pcb-blue">Smart Kandang PCB</span>
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto text-lg leading-relaxed">
            Kenali rangkaian modul monitoring dan otomatisasi yang memastikan kandang tetap bersih, nyaman, dan memiliki suplai pakan yang teratur.
          </p>
        </motion.div>

        {/* Grid Cards using Shadcn UI Minimalist Style */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {featuresData.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <motion.div key={index} variants={cardVariants} whileHover={{ y: -6 }} className="h-full">
                <Card className={`h-full bg-white border border-slate-200 hover:border-slate-300 transition-all duration-300 shadow-sm hover:shadow-md overflow-hidden group`}>
                  <CardHeader className="pb-4 relative">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 ${feature.iconBg} border ${feature.borderColor} transition-transform duration-300 group-hover:scale-105 group-hover:-rotate-3`}>
                      <IconComponent className={`w-7 h-7 ${feature.textColor}`} />
                    </div>
                    <CardTitle className="text-xl text-slate-900 font-semibold tracking-tight">
                      {feature.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-slate-600 text-base leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}