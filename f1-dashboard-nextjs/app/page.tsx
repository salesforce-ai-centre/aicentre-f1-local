"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { SpeedGauge } from "@/components/telemetry/SpeedGauge"
import { TelemetryData } from "@/types/telemetry"
import { formatLapTime, cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import {
  Activity, Gauge, Zap, Timer, Trophy, AlertTriangle,
  Fuel, Battery, Radio, Flag
} from "lucide-react"

export default function Home() {
  const [telemetry, setTelemetry] = useState<TelemetryData>({})
  const [connected, setConnected] = useState(false)
  const [theme, setTheme] = useState<"light" | "dark">("light")

  // SSE connection for telemetry
  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8080/stream")

    eventSource.onopen = () => {
      setConnected(true)
      console.log("Connected to telemetry stream")
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setTelemetry(data)
      } catch (error) {
        console.error("Error parsing telemetry:", error)
      }
    }

    eventSource.onerror = () => {
      setConnected(false)
      console.error("Connection lost")
    }

    return () => eventSource.close()
  }, [])

  // Theme toggle
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
  }, [theme])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 transition-colors duration-500">
      {/* Animated background pattern */}
      <div className="fixed inset-0 opacity-5 dark:opacity-10">
        <div className="absolute inset-0 bg-grid-pattern" />
        <div className="absolute inset-0 bg-gradient-radial from-f1-red/10 via-transparent to-transparent animate-float" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-gray-200/50 dark:border-gray-800/50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* F1 Logo */}
              <div className="relative">
                <div className="text-3xl font-display font-black bg-f1-gradient bg-clip-text text-transparent">
                  F1
                </div>
                <div className="absolute -inset-1 bg-f1-gradient opacity-20 blur-xl" />
              </div>
              <div className="h-8 w-px bg-gray-300 dark:bg-gray-700" />
              <h1 className="text-xl font-display font-bold text-gray-900 dark:text-gray-100">
                TELEMETRY DASHBOARD
              </h1>
            </div>

            <div className="flex items-center gap-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                <div className={cn(
                  "w-2 h-2 rounded-full animate-pulse",
                  connected ? "bg-accent-green shadow-glow-green" : "bg-gray-400"
                )} />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {connected ? "Connected" : "Disconnected"}
                </span>
              </div>

              {/* Theme Toggle */}
              <button
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="relative p-3 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                <motion.div
                  animate={{ rotate: theme === "dark" ? 180 : 0 }}
                  transition={{ duration: 0.5 }}
                >
                  {theme === "dark" ? "🌙" : "☀️"}
                </motion.div>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard Grid */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">

          {/* Session Info */}
          <Card title="Session Info" icon={<Flag size={18} />} variant="gradient">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Driver</span>
                <span className="font-display font-bold text-gray-900 dark:text-gray-100">
                  {telemetry.driverName || "---"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Track</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {telemetry.trackName || "---"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Position</span>
                <div className={cn(
                  "px-3 py-1 rounded-full font-bold text-white",
                  telemetry.position === 1 ? "bg-gradient-to-r from-yellow-400 to-yellow-600" :
                  telemetry.position === 2 ? "bg-gradient-to-r from-gray-400 to-gray-600" :
                  telemetry.position === 3 ? "bg-gradient-to-r from-orange-600 to-orange-800" :
                  "bg-gray-500"
                )}>
                  P{telemetry.position || "-"}
                </div>
              </div>
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Current Lap Time</div>
                <div className="text-2xl font-mono font-bold text-f1-red">
                  {formatLapTime(telemetry.currentLapTime)}
                </div>
              </div>
            </div>
          </Card>

          {/* Speed & RPM */}
          <Card title="Speed & RPM" icon={<Gauge size={18} />} variant="glass">
            <SpeedGauge speed={telemetry.speed || 0} />
            <div className="mt-6 space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">RPM</span>
                  <span className="font-mono font-bold">{telemetry.engineRPM || 0}</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-accent-green via-accent-yellow to-f1-red"
                    initial={{ width: "0%" }}
                    animate={{ width: `${((telemetry.engineRPM || 0) / 15000) * 100}%` }}
                    transition={{ duration: 0.1 }}
                  />
                </div>
              </div>
              <div className="flex justify-center">
                <div className="px-8 py-4 bg-gray-900 dark:bg-black rounded-xl border-2 border-f1-red">
                  <div className="text-5xl font-display font-black text-white text-center">
                    {telemetry.gear === 0 ? "N" : telemetry.gear === -1 ? "R" : telemetry.gear || "N"}
                  </div>
                  <div className="text-xs text-gray-400 text-center mt-1">GEAR</div>
                </div>
              </div>
            </div>
          </Card>

          {/* Throttle & Brake */}
          <Card title="Inputs" icon={<Activity size={18} />}>
            <div className="space-y-4">
              {/* Throttle */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Throttle</span>
                  <span className="text-sm font-bold">{Math.round((telemetry.throttle || 0) * 100)}%</span>
                </div>
                <div className="h-12 bg-gray-200 dark:bg-gray-800 rounded-lg overflow-hidden relative">
                  <motion.div
                    className="h-full bg-gradient-to-r from-accent-green to-green-400 shadow-glow-green flex items-center justify-end pr-3"
                    initial={{ width: "0%" }}
                    animate={{ width: `${(telemetry.throttle || 0) * 100}%` }}
                    transition={{ duration: 0.1 }}
                  >
                    <span className="text-white font-bold text-sm">
                      {Math.round((telemetry.throttle || 0) * 100)}%
                    </span>
                  </motion.div>
                </div>
              </div>

              {/* Brake */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Brake</span>
                  <span className="text-sm font-bold">{Math.round((telemetry.brake || 0) * 100)}%</span>
                </div>
                <div className="h-12 bg-gray-200 dark:bg-gray-800 rounded-lg overflow-hidden relative">
                  <motion.div
                    className="h-full bg-gradient-to-r from-f1-red to-red-400 shadow-glow-red flex items-center justify-end pr-3"
                    initial={{ width: "0%" }}
                    animate={{ width: `${(telemetry.brake || 0) * 100}%` }}
                    transition={{ duration: 0.1 }}
                  >
                    <span className="text-white font-bold text-sm">
                      {Math.round((telemetry.brake || 0) * 100)}%
                    </span>
                  </motion.div>
                </div>
              </div>

              {/* Steering */}
              <div className="pt-4">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 text-center mb-2">
                  Steering
                </div>
                <div className="relative h-20 flex items-center justify-center">
                  <div className="absolute w-full h-1 bg-gray-300 dark:bg-gray-700" />
                  <div className="absolute w-px h-4 bg-gray-400 dark:bg-gray-600 left-1/2 -translate-x-1/2" />
                  <motion.div
                    className="absolute w-16 h-16 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border-4 border-f1-red shadow-lg"
                    animate={{ x: (telemetry.steer || 0) * 100 }}
                    transition={{ duration: 0.1 }}
                  >
                    <div className="absolute inset-x-0 top-1/2 h-1 bg-white/50 -translate-y-1/2" />
                  </motion.div>
                </div>
              </div>
            </div>
          </Card>

          {/* DRS & ERS */}
          <Card title="DRS & ERS" icon={<Zap size={18} />}>
            <div className="space-y-4">
              {/* DRS Status */}
              <div className="text-center">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">DRS Status</div>
                <div className={cn(
                  "px-6 py-3 rounded-full font-bold text-white transition-all",
                  telemetry.drs === 1 ? "bg-gradient-to-r from-accent-green to-green-400 shadow-glow-green animate-pulse" :
                  telemetry.drsAvailable ? "bg-gradient-to-r from-accent-orange to-yellow-500" :
                  "bg-gray-500"
                )}>
                  {telemetry.drs === 1 ? "ACTIVE" :
                   telemetry.drsAvailable ? "AVAILABLE" : "INACTIVE"}
                </div>
              </div>

              {/* ERS Store */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">ERS Store</span>
                  <span className="font-mono font-bold">
                    {Math.round(((telemetry.ersStoreEnergy || 0) / 4000000) * 100)}%
                  </span>
                </div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-accent-purple to-purple-400"
                    initial={{ width: "0%" }}
                    animate={{ width: `${((telemetry.ersStoreEnergy || 0) / 4000000) * 100}%` }}
                    transition={{ duration: 0.1 }}
                  />
                </div>
              </div>

              {/* Deploy Mode */}
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Deploy Mode</div>
                <div className="text-lg font-bold text-accent-purple">
                  {telemetry.ersDeployMode || "None"}
                </div>
              </div>
            </div>
          </Card>

        </div>
      </main>
    </div>
  )
}
