import { motion } from 'framer-motion';
import { ThermometerSun, Droplets, Wind, Waves, Lightbulb, Wheat, Monitor, Zap } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const categories = [
  {
    label: 'Monitoring',
    badge: 'Pemantauan',
    description: 'Pantau kondisi kandang secara real-time melalui sensor IoT.',
    features: [
      {
        title: 'Monitoring Suhu',
        description: 'Pemantauan suhu kandang secara berkala untuk menjaga iklim tetap stabil dan nyaman bagi ternak.',
        icon: ThermometerSun,
        color: 'text-pcb-sand',
        bg: 'bg-pcb-sand/20',
      },
      {
        title: 'Monitoring Kelembaban',
        description: 'Pengawasan kelembaban udara untuk mencegah pertumbuhan jamur dan bakteri di lingkungan kandang.',
        icon: Droplets,
        color: 'text-pcb-primary',
        bg: 'bg-pcb-mint/50',
      },
      {
        title: 'Monitoring Amonia',
        description: 'Deteksi kadar amonia dari kotoran ayam untuk menjaga kualitas udara dan kesehatan pernapasan.',
        icon: Wind,
        color: 'text-pcb-secondary',
        bg: 'bg-pcb-sage/30',
      },
    ],
  },
  {
    label: 'Otomatisasi',
    badge: 'Kontrol',
    description: 'Kendalikan perangkat kandang secara otomatis dari mana saja.',
    features: [
      {
        title: 'Kontrol Pompa Pembersih',
        description: 'Aktivasi pompa pembersih kotoran secara otomatis berdasarkan kondisi kandang dan jadwal.',
        icon: Waves,
        color: 'text-pcb-primary',
        bg: 'bg-pcb-primary/10',
      },
      {
        title: 'Manajemen Lampu',
        description: 'Pengaturan jadwal dan intensitas lampu untuk mendukung siklus istirahat dan pertumbuhan ayam.',
        icon: Lightbulb,
        color: 'text-pcb-sand',
        bg: 'bg-pcb-sand/20',
      },
      {
        title: 'Otomatisasi Pakan',
        description: 'Distribusi pakan terjadwal dengan kontrol mudah melalui dashboard untuk memastikan asupan cukup.',
        icon: Wheat,
        color: 'text-pcb-secondary',
        bg: 'bg-pcb-mint/40',
      },
    ],
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
};

export default function Features() {
  return (
    <section id="fitur" className="py-24 px-6 bg-white relative overflow-hidden">
      {/* Subtle background */}
      <div className="absolute inset-0 -z-10 opacity-[0.03]" style={{
        backgroundImage: 'radial-gradient(circle, #3F4739 1px, transparent 1px)',
        backgroundSize: '24px 24px'
      }} />

      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <Badge variant="outline" className="mb-4 px-3 py-1 text-xs font-medium rounded-full border-pcb-sage/40 text-pcb-secondary">
            Fitur Lengkap
          </Badge>
          <h2 className="text-3xl md:text-4xl font-bold text-pcb-primary tracking-tight mb-4">
            Semua yang Kamu Butuhkan
          </h2>
          <p className="text-pcb-secondary max-w-xl mx-auto">
            Monitoring real-time dan otomatisasi perangkat kandang dalam satu platform terintegrasi.
          </p>
        </motion.div>

        {/* Categories */}
        {categories.map((category, catIdx) => (
          <div key={category.label} className={catIdx > 0 ? 'mt-16' : ''}>
            {/* Category Header */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className="flex items-center gap-3 mb-8"
            >
              <div className="p-2 rounded-lg bg-pcb-mint/40">
                {catIdx === 0 ? <Monitor className="w-4 h-4 text-pcb-primary" /> : <Zap className="w-4 h-4 text-pcb-primary" />}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-pcb-primary">{category.label}</h3>
                <p className="text-sm text-pcb-secondary/70">{category.description}</p>
              </div>
            </motion.div>

            {/* Feature Cards */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-60px' }}
              className="grid grid-cols-1 md:grid-cols-3 gap-4"
            >
              {category.features.map((feature) => (
                <motion.div
                  key={feature.title}
                  variants={cardVariants}
                  whileHover={{ y: -6, transition: { duration: 0.2 } }}
                >
                  <Card className="h-full border-pcb-sage/30 bg-white hover:border-pcb-sage/60 hover:shadow-lg transition-all duration-300 group cursor-default">
                    <CardContent className="p-6">
                      <motion.div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${feature.bg}`}
                        whileHover={{ scale: 1.15, rotate: -5 }}
                        transition={{ type: "spring", stiffness: 300 }}
                      >
                        <feature.icon className={`w-5 h-5 ${feature.color}`} />
                      </motion.div>
                      <h4 className="text-base font-semibold text-pcb-primary mb-2">
                        {feature.title}
                      </h4>
                      <p className="text-sm text-pcb-secondary leading-relaxed">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        ))}
      </div>
    </section>
  );
}
