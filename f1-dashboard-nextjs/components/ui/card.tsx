import { cn } from "@/lib/utils"
import { ReactNode } from "react"

interface CardProps {
  children: ReactNode
  className?: string
  title?: string
  icon?: ReactNode
  variant?: "default" | "gradient" | "glass"
  noPadding?: boolean
}

export function Card({
  children,
  className,
  title,
  icon,
  variant = "default",
  noPadding = false
}: CardProps) {
  const variants = {
    default: "bg-white dark:bg-gray-900/90",
    gradient: "bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900/90 dark:to-gray-800/90",
    glass: "bg-white/80 dark:bg-gray-900/60 backdrop-blur-xl"
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl transition-all duration-300",
        "border border-gray-200/50 dark:border-gray-800/50",
        "shadow-f1 hover:shadow-f1-hover hover:-translate-y-1",
        "before:absolute before:inset-0 before:h-1 before:bg-f1-gradient before:opacity-80",
        variants[variant],
        className
      )}
    >
      {title && (
        <div className="relative border-b border-gray-200/50 dark:border-gray-800/50 bg-gradient-to-r from-gray-50/50 to-gray-100/50 dark:from-gray-800/50 dark:to-gray-900/50">
          <div className="flex items-center gap-3 px-6 py-4">
            {icon && (
              <span className="text-f1-red">{icon}</span>
            )}
            <h3 className="font-display font-bold text-sm uppercase tracking-wider text-gray-900 dark:text-gray-100">
              {title}
            </h3>
            <div className="ml-auto h-2 w-2 rounded-full bg-accent-green animate-pulse" />
          </div>
        </div>
      )}
      <div className={cn(!noPadding && "p-6", "relative")}>
        {children}
      </div>
    </div>
  )
}