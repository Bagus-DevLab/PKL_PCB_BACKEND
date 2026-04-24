import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";

/**
 * Animated counter yang menghitung dari 0 ke target value.
 * Animasi hanya berjalan saat elemen masuk viewport.
 */
export default function AnimatedCounter({ value, duration = 1.2, className = "" }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;

    const target = Number(value) || 0;
    if (target === 0) {
      setCount(0);
      return;
    }

    const startTime = Date.now();
    const durationMs = duration * 1000;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / durationMs, 1);

      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setCount(target);
      }
    };

    requestAnimationFrame(animate);
  }, [isInView, value, duration]);

  return (
    <motion.span
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 10 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.4 }}
    >
      {count.toLocaleString("id-ID")}
    </motion.span>
  );
}
