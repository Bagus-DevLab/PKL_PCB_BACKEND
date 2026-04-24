import { motion } from 'framer-motion';
import { ArrowRight, Activity, ThermometerSun, Droplets, Wind, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function Hero() {
  return (
    <section id="beranda" className="relative min-h-screen flex items-center justify-center overflow-hidden px-6 pt-20">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-white via-pcb-mint/20 to-white -z-20" />

      {/* Decorative grid pattern */}
      <div className="absolute inset-0 -z-10 opacity-[0.04]" style={{
        backgroundImage: 'radial-gradient(circle, #3F4739 1px, transparent 1px)',
        backgroundSize: '32px 32px'
      }} />

      {/* Glow effects */}
      <div className="absolute top-1/3 left-1/4 w-[500px] h-[500px] bg-pcb-mint/40 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-pcb-sand/20 rounded-full blur-[100px] -z-10" />

      <div className="z-10 text-center max-w-4xl mx-auto flex flex-col items-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <Badge variant="outline" className="px-4 py-1.5 text-sm font-medium border-pcb-sage/40 text-pcb-secondary bg-white/80 backdrop-blur-sm shadow-sm rounded-full">
            <Activity className="w-3.5 h-3.5 mr-2 inline-block animate-pulse text-pcb-primary" />
            Sistem Pemantauan Cerdas v2.0
          </Badge>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-7xl font-extrabold mb-6 text-slate-900 leading-[1.1] tracking-tight"
        >
          Monitoring{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-pcb-primary to-pcb-secondary">
            Smart Kandang
          </span>
          <br className="hidden sm:block" />
          Berbasis IoT
        </motion.h1>

        {/* Description */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-base md:text-lg text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed"
        >
          Platform terintegrasi untuk memantau suhu, kelembaban, dan kadar amonia
          sekaligus mengotomatisasi pompa, pencahayaan, serta pemberian pakan.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center gap-4 mb-16"
        >
          <Button
            asChild
            size="lg"
            className="w-full sm:w-auto rounded-full font-semibold shadow-lg shadow-pcb-primary/20 hover:shadow-xl hover:shadow-pcb-primary/30 transition-all h-12 px-8"
          >
            <a href="#fitur">
              Lihat Fitur Utama
              <ArrowRight className="ml-2 w-4 h-4" />
            </a>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="w-full sm:w-auto border-pcb-sage/40 text-pcb-primary hover:bg-pcb-mint/30 rounded-full font-semibold transition-all h-12 px-8 bg-white/80 backdrop-blur-sm"
          >
            <a href="/admin/login">
              Buka Admin Panel
            </a>
          </Button>
        </motion.div>

        {/* Floating sensor cards */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
          className="flex flex-wrap justify-center gap-3 sm:gap-4"
        >
          {[
            { icon: ThermometerSun, label: 'Suhu', value: '28.5°C', color: 'text-pcb-sand', bg: 'bg-pcb-sand/20' },
            { icon: Droplets, label: 'Kelembaban', value: '72%', color: 'text-pcb-primary', bg: 'bg-pcb-mint/50' },
            { icon: Wind, label: 'Amonia', value: '12 ppm', color: 'text-pcb-secondary', bg: 'bg-pcb-sage/30' },
          ].map((item, i) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.9 + i * 0.1 }}
              className="flex items-center gap-3 bg-white/80 backdrop-blur-sm border border-pcb-sage/30 rounded-xl px-4 py-3 shadow-sm"
            >
              <div className={`p-2 rounded-lg ${item.bg}`}>
                <item.icon className={`w-4 h-4 ${item.color}`} />
              </div>
              <div className="text-left">
                <p className="text-xs text-slate-400">{item.label}</p>
                <p className="text-sm font-semibold text-slate-900">{item.value}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <ChevronDown className="w-5 h-5 text-slate-400" />
        </motion.div>
      </motion.div>
    </section>
  );
}
