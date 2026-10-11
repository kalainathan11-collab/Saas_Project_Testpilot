import { motion, type Variants } from 'framer-motion'
import { Children, type ReactNode } from 'react'
import { cn } from '../../lib/cn'

const container: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
}

const item: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
}

interface AnimatedListProps {
  children: ReactNode
  className?: string
}

export function AnimatedList({ children, className }: AnimatedListProps) {
  return (
    <motion.div initial="hidden" animate="visible" variants={container} className={cn(className)}>
      {Children.toArray(children).map((child, index) => (
        <motion.div key={index} variants={item}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  )
}
