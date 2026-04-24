import { motion } from "framer-motion";

/**
 * Wrapper untuk page transition animation.
 * Wrap konten halaman dengan komponen ini untuk animasi enter/exit.
 */
export default function PageTransition({ children, className = "" }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
