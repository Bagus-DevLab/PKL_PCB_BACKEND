
import { Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-white border-t border-slate-200 pt-16 pb-8 px-6">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">

        {/* Brand & Deskripsi */}
        <div>
          <div className="text-2xl font-black tracking-wider text-slate-900 mb-4">
            PCB<span className="text-slate-500 text-sm font-medium ml-2 tracking-normal">Smart Kandang</span>
          </div>
          <p className="text-slate-600 text-sm leading-relaxed max-w-xs">
            Sistem monitoring dan otomatisasi kandang pintar berbasis IoT. Dikembangkan sebagai bentuk implementasi teknologi untuk efisiensi peternakan modern.
          </p>
        </div>

        {/* Quick Links Navigasi */}
        <div>
          <h4 className="text-slate-900 font-bold mb-4 tracking-wide">Navigasi Utama</h4>
          <ul className="space-y-3 text-slate-600 text-sm">
            <li><a href="#beranda" className="hover:text-pcb-blue transition-colors flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>Beranda</a></li>
            <li><a href="#fitur" className="hover:text-pcb-blue transition-colors flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-teal-400"></div>Fitur Sistem</a></li>
            <li><a href="#live-data" className="hover:text-pcb-blue transition-colors flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-orange-400"></div>Live Dashboard</a></li>
          </ul>
        </div>

        {/* Tech Stack Info */}
        <div>
          <h4 className="text-slate-900 font-bold mb-4 tracking-wide">Spesifikasi Sistem</h4>
          <ul className="space-y-3 text-slate-600 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-semibold min-w-[80px]">Frontend</span>
              <span>React 19, Tailwind CSS v4, Shadcn UI</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-teal-600 font-semibold min-w-[80px]">Backend</span>
              <span>Python (FastAPI)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-orange-500 font-semibold min-w-[80px]">Hardware</span>
              <span>ESP32, Sensor DHT11 & MQ-135</span>
            </li>
          </ul>
        </div>

      </div>

      {/* Copyright Line */}
      <div className="max-w-7xl mx-auto pt-8 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between text-slate-500 text-xs gap-4">
        <p className="flex items-center gap-1">
          &copy; {new Date().getFullYear()} Project PCB. Made with <Heart className="w-3 h-3 text-red-500 mx-0.5" /> by Bagus.
        </p>
        <p className="font-medium tracking-wide">Dibuat untuk Praktik Kerja Lapangan (PKL)</p>
      </div>
    </footer>
  );
}