import { motion } from 'framer-motion';
import { Heart, Cpu } from 'lucide-react';

const columnVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.15, ease: 'easeOut' },
  }),
};

const techItemVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, delay: 0.5 + i * 0.1 },
  }),
};

export default function Footer() {
  return (
    <footer className="bg-pcb-mint/20 border-t border-pcb-sage/30 pt-16 pb-8 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
          {/* Brand — column 1 */}
          <motion.div
            custom={0}
            variants={columnVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <div className="flex items-center gap-2 mb-4">
              <motion.div
                className="w-7 h-7 bg-pcb-primary rounded-lg flex items-center justify-center"
                whileHover={{ rotate: 10, scale: 1.1 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Cpu className="w-3.5 h-3.5 text-white" />
              </motion.div>
              <span className="text-lg font-bold text-pcb-primary">
                PCB<span className="text-pcb-secondary font-normal ml-1">Smart Kandang</span>
              </span>
            </div>
            <p className="text-sm text-pcb-secondary leading-relaxed max-w-xs">
              Sistem monitoring dan otomatisasi kandang pintar berbasis IoT untuk efisiensi peternakan modern.
            </p>
          </motion.div>

          {/* Navigation — column 2 */}
          <motion.div
            custom={1}
            variants={columnVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h4 className="text-sm font-semibold text-pcb-primary mb-4 uppercase tracking-wider">Navigasi</h4>
            <ul className="space-y-2.5 text-sm">
              {[
                { label: 'Beranda', href: '#beranda' },
                { label: 'Fitur Sistem', href: '#fitur' },
                { label: 'Admin Panel', href: '/admin/login' },
              ].map((link) => (
                <li key={link.label}>
                  <motion.a
                    href={link.href}
                    className="text-pcb-secondary hover:text-pcb-primary transition-colors"
                    whileHover={{ x: 4 }}
                    transition={{ duration: 0.15 }}
                  >
                    {link.label}
                  </motion.a>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Tech Stack — column 3 */}
          <motion.div
            custom={2}
            variants={columnVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <h4 className="text-sm font-semibold text-pcb-primary mb-4 uppercase tracking-wider">Tech Stack</h4>
            <div className="space-y-2.5 text-sm">
              {[
                { color: 'bg-pcb-primary', text: 'React 19, Tailwind CSS, Shadcn UI' },
                { color: 'bg-pcb-sage', text: 'Python FastAPI, PostgreSQL' },
                { color: 'bg-pcb-sand', text: 'ESP32, DHT11, MQ-135' },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  custom={i}
                  variants={techItemVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="flex items-center gap-2"
                >
                  <div className={`w-1.5 h-1.5 rounded-full ${item.color}`} />
                  <span className="text-pcb-secondary">{item.text}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Copyright */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="pt-8 border-t border-pcb-sage/30 flex flex-col sm:flex-row items-center justify-between text-pcb-secondary text-xs gap-3"
        >
          <p className="flex items-center gap-1">
            &copy; {new Date().getFullYear()} PCB Smart Kandang. Made with{' '}
            <Heart className="w-3 h-3 text-red-400 mx-0.5 animate-heartbeat" />{' '}
            by Bagus.
          </p>
          <p>Praktik Kerja Lapangan (PKL)</p>
        </motion.div>
      </div>
    </footer>
  );
}
