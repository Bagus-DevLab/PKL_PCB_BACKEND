import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  // Fungsi untuk custom smooth scroll dengan offset
  const handleScroll = (e, targetId) => {
    e.preventDefault();
    const targetElement = document.getElementById(targetId);

    if (targetElement) {
      const navbarHeight = 80;
      const elementPosition = targetElement.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.scrollY - navbarHeight;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
      });
      setIsOpen(false);
    }
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200"
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">

        {/* Logo Text */}
        <div
          onClick={(e) => handleScroll(e, 'beranda')}
          className="text-2xl font-black tracking-wider text-slate-900 cursor-pointer hover:opacity-80 transition-opacity"
        >
          PCB<span className="text-slate-500 text-sm font-medium ml-2 tracking-normal">Smart Kandang</span>
        </div>

        {/* Navigation Links - Desktop */}
        <div className="hidden md:flex items-center space-x-8 text-slate-600 font-medium">
          <a
            href="#beranda"
            onClick={(e) => handleScroll(e, 'beranda')}
            className="hover:text-pcb-blue transition-colors text-sm"
          >
            Beranda
          </a>
          <a
            href="#fitur"
            onClick={(e) => handleScroll(e, 'fitur')}
            className="hover:text-pcb-blue transition-colors text-sm"
          >
            Fitur Utama
          </a>
        </div>

        {/* CTA Button - Desktop */}
        <div className="hidden md:block">
          <Button
            asChild
            className="bg-pcb-blue hover:bg-pcb-blue/90 text-white rounded-full font-semibold shadow-[0_0_15px_rgba(60,145,230,0.2)] hover:shadow-[0_0_20px_rgba(60,145,230,0.4)] transition-all"
          >
            <a href="#" target="_blank" rel="noopener noreferrer">
              Download Aplikasi
            </a>
          </Button>
        </div>

        {/* Mobile Menu Icon */}
        <div className="md:hidden text-slate-600 cursor-pointer">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsOpen(!isOpen)}
            className="text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </Button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white/95 backdrop-blur-xl border-b border-slate-200 overflow-hidden"
          >
            <div className="px-6 py-6 flex flex-col space-y-4">
              <a
                href="#beranda"
                onClick={(e) => handleScroll(e, 'beranda')}
                className="text-slate-700 hover:text-pcb-blue transition-colors font-medium text-lg"
              >
                Beranda
              </a>
              <a
                href="#fitur"
                onClick={(e) => handleScroll(e, 'fitur')}
                className="text-slate-700 hover:text-pcb-blue transition-colors font-medium text-lg"
              >
                Fitur Utama
              </a>
              <Button
                asChild
                className="w-full mt-4 bg-pcb-blue hover:bg-pcb-blue/90 text-white rounded-lg font-semibold"
              >
                <a href="#" target="_blank" rel="noopener noreferrer">
                  Download Aplikasi
                </a>
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}