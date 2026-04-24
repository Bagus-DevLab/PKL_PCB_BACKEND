import { motion } from 'framer-motion';
import { Heart, Cpu } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-pcb-mint/20 border-t border-pcb-sage/30 pt-16 pb-8 px-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="max-w-6xl mx-auto"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 bg-pcb-primary rounded-lg flex items-center justify-center">
                <Cpu className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="text-lg font-bold text-slate-900">
                PCB<span className="text-slate-400 font-normal ml-1">Smart Kandang</span>
              </span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xs">
              Sistem monitoring dan otomatisasi kandang pintar berbasis IoT untuk efisiensi peternakan modern.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider">Navigasi</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="#beranda" className="text-pcb-secondary hover:text-pcb-primary transition-colors">Beranda</a></li>
              <li><a href="#fitur" className="text-pcb-secondary hover:text-pcb-primary transition-colors">Fitur Sistem</a></li>
              <li><a href="/admin/login" className="text-pcb-secondary hover:text-pcb-primary transition-colors">Admin Panel</a></li>
            </ul>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider">Tech Stack</h4>
            <div className="space-y-2.5 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                <span className="text-slate-500">React 19, Tailwind CSS, Shadcn UI</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span className="text-slate-500">Python FastAPI, PostgreSQL</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                <span className="text-slate-500">ESP32, DHT11, MQ-135</span>
              </div>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="pt-8 border-t border-pcb-sage/30 flex flex-col sm:flex-row items-center justify-between text-pcb-secondary text-xs gap-3">
          <p className="flex items-center gap-1">
            &copy; {new Date().getFullYear()} PCB Smart Kandang. Made with <Heart className="w-3 h-3 text-red-400 mx-0.5" /> by Bagus.
          </p>
          <p>Praktik Kerja Lapangan (PKL)</p>
        </div>
      </motion.div>
    </footer>
  );
}
