import { motion, type HTMLMotionProps } from 'framer-motion'
import { cn } from '../../lib/cn'

type Variant = 'primary' | 'secondary' | 'danger'

interface GradientButtonProps extends HTMLMotionProps<'button'> {
  variant?: Variant
}

const variants: Record<Variant, string> = {
  primary: 'bg-gradient-to-r from-brand-600 to-purple-500 text-white hover:shadow-lg',
  secondary: 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50',
  danger: 'bg-gradient-to-r from-red-600 to-rose-500 text-white hover:shadow-lg',
}

export function GradientButton({
  children,
  className,
  variant = 'primary',
  type = 'button',
  ...props
}: GradientButtonProps) {
  return (
    <motion.button
      type={type}
      whileHover={{ scale: 1.02, y: -1 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition-shadow disabled:cursor-not-allowed disabled:opacity-50',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </motion.button>
  )
}
