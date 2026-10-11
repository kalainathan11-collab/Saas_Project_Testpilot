import { motion, type HTMLMotionProps } from 'framer-motion'
import { cn } from '../../lib/cn'

interface GlassCardProps extends HTMLMotionProps<'div'> {
  /** Disable the hover elevation (e.g. for large containers like tables). */
  static?: boolean
}

export function GlassCard({ children, className, static: isStatic = false, ...props }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={isStatic ? undefined : { y: -3 }}
      transition={{ duration: 0.25 }}
      className={cn(
        'rounded-2xl border border-slate-200 bg-white/80 p-5 shadow-sm backdrop-blur-lg transition-shadow',
        !isStatic && 'hover:shadow-lg',
        className,
      )}
      {...props}
    >
      {children}
    </motion.div>
  )
}
