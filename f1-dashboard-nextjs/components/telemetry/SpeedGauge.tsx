"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface SpeedGaugeProps {
  speed: number
  maxSpeed?: number
  className?: string
}

export function SpeedGauge({ speed = 0, maxSpeed = 350, className }: SpeedGaugeProps) {
  const percentage = Math.min((speed / maxSpeed) * 100, 100)
  const rotation = (percentage * 270 / 100) - 135

  const getSpeedZone = () => {
    if (speed > 300) return "text-f1-red"
    if (speed > 250) return "text-accent-orange"
    if (speed > 200) return "text-accent-yellow"
    return "text-accent-green"
  }

  return (
    <div className={cn("relative", className)}>
      <div className="relative w-48 h-48 mx-auto">
        {/* Outer ring with gradient */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-800 dark:to-gray-900 p-1">
          <div className="w-full h-full rounded-full bg-white dark:bg-gray-900 relative overflow-hidden">
            {/* Speed zones */}
            <svg className="absolute inset-0 w-full h-full -rotate-90">
              <circle
                cx="96"
                cy="96"
                r="85"
                fill="none"
                stroke="url(#speedGradient)"
                strokeWidth="10"
                strokeDasharray={`${270 * Math.PI * 85 / 180} ${90 * Math.PI * 85 / 180}`}
                strokeLinecap="round"
                className="opacity-20"
              />
              <defs>
                <linearGradient id="speedGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00D735" />
                  <stop offset="50%" stopColor="#FFD700" />
                  <stop offset="75%" stopColor="#FF6700" />
                  <stop offset="100%" stopColor="#E10600" />
                </linearGradient>
              </defs>
            </svg>

            {/* Animated progress arc */}
            <svg className="absolute inset-0 w-full h-full -rotate-90">
              <motion.circle
                cx="96"
                cy="96"
                r="85"
                fill="none"
                stroke="url(#speedGradient)"
                strokeWidth="10"
                strokeDasharray={`${percentage * 270 * Math.PI * 85 / 18000} ${(360 - percentage * 270 / 100) * Math.PI * 85 / 180}`}
                strokeLinecap="round"
                initial={{ strokeDasharray: "0 600" }}
                animate={{
                  strokeDasharray: `${percentage * 270 * Math.PI * 85 / 18000} ${(360 - percentage * 270 / 100) * Math.PI * 85 / 180}`
                }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </svg>

            {/* Needle */}
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              style={{ transformOrigin: "center" }}
              animate={{ rotate: rotation }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <div className="relative w-1 h-24 -mt-12">
                <div className="absolute inset-x-0 top-0 h-16 bg-f1-red rounded-full shadow-glow-red" />
                <div className="absolute inset-x-0 bottom-8 w-3 h-3 -mx-1 bg-f1-red rounded-full" />
              </div>
            </motion.div>

            {/* Center hub */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-gray-900 dark:bg-gray-800 rounded-full border-2 border-f1-red shadow-lg" />
          </div>
        </div>

        {/* Speed display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            className={cn("text-5xl font-display font-black tabular-nums", getSpeedZone())}
            key={Math.floor(speed)}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.1 }}
          >
            {Math.round(speed)}
          </motion.div>
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            km/h
          </div>
        </div>
      </div>

      {/* Speed zones legend */}
      <div className="flex justify-center gap-2 mt-4">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-accent-green" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Safe</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-accent-yellow" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Fast</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-f1-red" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Max</span>
        </div>
      </div>
    </div>
  )
}