import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Cpu } from 'lucide-react';
import { Button } from '@/components/ui/button';

const navLinks = [
  { label: 'Beranda', href: '#beranda' },
  { label: 'Fitur Utama', href: '#fitur' },
  { label: 'Admin', href: '/admin/login', isRoute: true },
];

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

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
          ? 'bg-white/90 backdrop-blur-xl border-b border-pcb-sage/30 shadow-sm'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        {/* Logo */}
        <motion.div
          onClick={(e) => handleScrollTo(e, 'beranda')}
          className="flex items-center gap-2 cursor-pointer group"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <div className="w-8 h-8 bg-pcb-primary rounded-lg flex items-center justify-center group-hover:scale-105 transition-transform">
            <Cpu className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-bold text-pcb-primary">
            PCB<span className="text-pcb-secondary font-normal ml-1">Smart Kandang</span>
          </span>
        </motion.div>

        {/* Desktop Nav — staggered entrance */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link, i) => (
            <motion.a
              key={link.label}
              href={link.href}
              onClick={link.isRoute ? undefined : (e) => handleScrollTo(e, link.href.replace('#', ''))}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 + i * 0.1 }}
              whileHover={{ y: -2 }}
              className="text-sm font-medium text-pcb-secondary hover:text-pcb-primary transition-colors"
            >
              {link.label}
            </motion.a>
          ))}
        </div>

        {/* Desktop CTA */}
        <motion.div
          className="hidden md:block"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.6 }}
        >
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }}>
            <Button
              asChild
              className="rounded-full font-semibold shadow-md hover:shadow-lg transition-all"
            >
              <a href="#" target="_blank" rel="noopener noreferrer">
                Download Aplikasi
              </a>
            </Button>
          </motion.div>
        </motion.div>

        {/* Mobile Menu Toggle */}
        <motion.div whileTap={{ scale: 0.9 }} className="md:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsOpen(!isOpen)}
            className="text-pcb-secondary"
          >
            <AnimatePresence mode="wait">
              {isOpen ? (
                <motion.div key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.15 }}>
                  <X className="w-5 h-5" />
                </motion.div>
              ) : (
                <motion.div key="menu" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.15 }}>
                  <Menu className="w-5 h-5" />
                </motion.div>
              )}
            </AnimatePresence>
          </Button>
        </motion.div>
      </div>

      {/* Mobile Menu — staggered links */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="md:hidden bg-white/95 backdrop-blur-xl border-b border-pcb-sage/30 overflow-hidden"
          >
            <div className="px-6 py-4 flex flex-col gap-1">
              {navLinks.map((link, i) => (
                <motion.a
                  key={link.label}
                  href={link.href}
                  onClick={link.isRoute ? undefined : (e) => handleScrollTo(e, link.href.replace('#', ''))}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.08 }}
                  className="text-pcb-secondary hover:text-pcb-primary font-medium py-2.5"
                >
                  {link.label}
                </motion.a>
              ))}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
                className="mt-2"
              >
                <Button asChild className="w-full rounded-lg font-semibold">
                  <a href="#" target="_blank" rel="noopener noreferrer">Download Aplikasi</a>
                </Button>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
