import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function Hero() {
  return (
    <section id="beranda" className="relative min-h-screen flex items-center justify-center overflow-hidden px-6 pt-20 bg-slate-50">
      {/* Efek Cahaya / Glow di Background yang sangat halus untuk versi terang */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-100/50 rounded-full blur-[140px] -z-10 animate-pulse"></div>
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-cyan-100/40 rounded-full blur-[120px] -z-10"></div>

      <div className="z-10 text-center max-w-4xl mx-auto flex flex-col items-center">
        {/* Badge Animasi */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mb-8"
        >
          <Badge variant="outline" className="px-4 py-1.5 text-sm font-medium border-slate-200 text-slate-700 bg-white shadow-sm rounded-full">
            <Activity className="w-4 h-4 mr-2 inline-block animate-pulse text-pcb-blue" />
            Sistem Pemantauan Cerdas v2.0
          </Badge>
        </motion.div>

        {/* Animasi Judul */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
        >
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 text-slate-900 leading-tight tracking-tight">
            Sistem Monitoring <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-blue-600">
              Smart Kandang PCB
            </span>
          </h1>
        </motion.div>

        {/* Animasi Deskripsi */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-lg md:text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed"
        >
          Platform IoT terintegrasi untuk memantau suhu, kelembaban, dan kadar amonia sekaligus mengotomatisasi pompa pembersih, pencahayaan, serta pemberian pakan.
        </motion.p>

        {/* Animasi Tombol Shadcn Minimalis */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto"
        >
          <Button
            asChild
            size="lg"
            className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 text-white rounded-full font-semibold shadow-md transition-all h-14 px-8 text-lg"
          >
            <a href="#fitur">
              Lihat Fitur Utama
              <ArrowRight className="ml-2 w-5 h-5" />
            </a>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="w-full sm:w-auto border-slate-300 text-slate-700 hover:bg-slate-50 hover:text-slate-900 rounded-full font-semibold transition-all h-14 px-8 text-lg bg-white"
          >
            <a href="https://api.pcb.my.id" target="_blank" rel="noopener noreferrer">
              Buka Dashboard
            </a>
          </Button>
        </motion.div>
      </div>
    </section>
  );
}