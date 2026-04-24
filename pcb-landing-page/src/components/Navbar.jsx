import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Cpu } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Deteksi scroll untuk mengubah background navbar
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleScrollTo = (e, targetId) => {
    e.preventDefault();
    const el = document.getElementById(targetId);
    if (el) {
      const offset = el.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: offset, behavior: 'smooth' });
      setIsOpen(false);
    }
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/90 backdrop-blur-xl border-b border-slate-200 shadow-sm'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        {/* Logo */}
        <div
          onClick={(e) => handleScrollTo(e, 'beranda')}
          className="flex items-center gap-2 cursor-pointer group"
        >
          <div className="w-8 h-8 bg-pcb-primary rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
            <Cpu className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-900">
            PCB<span className="text-slate-400 font-normal ml-1">Smart Kandang</span>
          </span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          <a
            href="#beranda"
            onClick={(e) => handleScrollTo(e, 'beranda')}
            className="text-sm font-medium text-pcb-secondary hover:text-pcb-primary transition-colors"
          >
            Beranda
          </a>
          <a
            href="#fitur"
            onClick={(e) => handleScrollTo(e, 'fitur')}
            className="text-sm font-medium text-pcb-secondary hover:text-pcb-primary transition-colors"
          >
            Fitur Utama
          </a>
          <a
            href="/admin/login"
            className="text-sm font-medium text-pcb-secondary hover:text-pcb-primary transition-colors"
          >
            Admin
          </a>
        </div>

        {/* Desktop CTA */}
        <div className="hidden md:block">
          <Button
            asChild
            className="rounded-full font-semibold shadow-md hover:shadow-lg transition-all"
          >
            <a href="#" target="_blank" rel="noopener noreferrer">
              Download Aplikasi
            </a>
          </Button>
        </div>

        {/* Mobile Menu Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsOpen(!isOpen)}
          className="md:hidden text-slate-600"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden bg-white/95 backdrop-blur-xl border-b border-slate-200 overflow-hidden"
          >
            <div className="px-6 py-4 flex flex-col gap-3">
              <a href="#beranda" onClick={(e) => handleScrollTo(e, 'beranda')}             className="text-pcb-secondary hover:text-pcb-primary font-medium py-2">Beranda</a>
              <a href="#fitur" onClick={(e) => handleScrollTo(e, 'fitur')}             className="text-pcb-secondary hover:text-pcb-primary font-medium py-2">Fitur Utama</a>
              <a href="/admin/login"             className="text-pcb-secondary hover:text-pcb-primary font-medium py-2">Admin</a>
              <Button asChild className="w-full mt-2 rounded-lg font-semibold">
                <a href="#" target="_blank" rel="noopener noreferrer">Download Aplikasi</a>
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
