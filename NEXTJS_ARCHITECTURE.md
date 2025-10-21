# Next.js + Tailwind F1 Dashboard Architecture

## Overview
Modern real-time F1 telemetry dashboard supporting dual UDP streams for head-to-head racing comparison, built with Next.js, Tailwind CSS, and real-time WebSocket connections.

## Architecture

```
┌──────────────┐     UDP:20777    ┌─────────────────┐
│  F1 25 Game  │ ─────────────────>│                 │
│  Machine 1   │                   │   UDP Receiver  │
└──────────────┘                   │   Service       │
                                   │                 │
┌──────────────┐     UDP:20778    │  - Player 1     │      WebSocket       ┌────────────────┐
│  F1 25 Game  │ ─────────────────>│  - Player 2     │ ───────────────────> │  Next.js App   │
│  Machine 2   │                   │                 │                      │                │
└──────────────┘                   │  Python Backend │                      │  - Dashboard   │
                                   │                 │                      │  - Comparison  │
                                   └─────────────────┘                      │  - Leaderboard │
                                            │                               └────────────────┘
                                            │ HTTPS API                              │
                                            ▼                                        │ Static
                                   ┌─────────────────┐                              ▼
                                   │  Salesforce     │                      [Browser Clients]
                                   │  Data Cloud     │
                                   └─────────────────┘
```

## Components

### 1. UDP Receiver Service (Python)
**Path:** `backend/`

```python
# backend/telemetry_service.py
- Listens on multiple UDP ports (20777, 20778)
- Maintains separate state for each player
- Aggregates and streams data via WebSocket
- Sends telemetry to Salesforce Data Cloud
```

**Features:**
- Multi-port UDP listening
- Player session management
- Real-time data aggregation
- WebSocket broadcasting
- Data Cloud integration

### 2. Next.js Frontend
**Path:** `frontend/`

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with Tailwind
│   ├── page.tsx            # Main dashboard
│   ├── comparison/
│   │   └── page.tsx        # Head-to-head comparison
│   ├── api/
│   │   └── telemetry/
│   │       └── route.ts    # WebSocket endpoint
│   └── components/
│       ├── Dashboard/
│       │   ├── PlayerDashboard.tsx
│       │   ├── DualDashboard.tsx
│       │   └── ComparisonMetrics.tsx
│       ├── Telemetry/
│       │   ├── SpeedGauge.tsx
│       │   ├── TyreStatus.tsx
│       │   ├── GForceRadar.tsx
│       │   └── ThrottleBrake.tsx
│       └── UI/
│           ├── ThemeToggle.tsx
│           └── Card.tsx
```

### 3. Technology Stack

**Backend:**
- Python 3.11+
- asyncio for concurrent UDP handling
- websockets library
- Salesforce Data Cloud SDK
- Redis for session state (optional)

**Frontend:**
- Next.js 14 (App Router)
- Tailwind CSS 3.4
- shadcn/ui components
- Recharts for data viz
- Socket.io-client
- Framer Motion animations

## Implementation Plan

### Phase 1: Backend Multi-Stream Support

```python
# backend/multi_receiver.py
import asyncio
import json
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class PlayerSession:
    id: str
    name: str
    port: int
    last_data: Optional[dict] = None

class MultiStreamReceiver:
    def __init__(self):
        self.players: Dict[str, PlayerSession] = {}
        self.websocket_clients = set()

    async def listen_udp(self, port: int, player_id: str):
        """Listen for UDP packets on specified port for player"""
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: F1UDPProtocol(player_id, self),
            local_addr=('0.0.0.0', port)
        )

    async def broadcast_telemetry(self):
        """Broadcast aggregated telemetry to all WebSocket clients"""
        while True:
            data = {
                'players': {
                    pid: player.last_data
                    for pid, player in self.players.items()
                },
                'comparison': self.calculate_comparison()
            }
            await self.send_to_websockets(data)
            await asyncio.sleep(0.05)  # 20Hz update rate
```

### Phase 2: Next.js Dashboard Setup

```bash
# Create Next.js app with TypeScript and Tailwind
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend

# Install dependencies
npm install socket.io-client recharts framer-motion
npm install @radix-ui/react-* # UI primitives
npm install lucide-react # Icons
```

### Phase 3: Component Structure

```tsx
// app/components/Dashboard/DualDashboard.tsx
'use client'

import { useEffect, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import PlayerDashboard from './PlayerDashboard'
import ComparisonMetrics from './ComparisonMetrics'

export default function DualDashboard() {
  const [player1Data, setPlayer1Data] = useState(null)
  const [player2Data, setPlayer2Data] = useState(null)
  const [socket, setSocket] = useState<Socket | null>(null)

  useEffect(() => {
    const newSocket = io('ws://localhost:8000', {
      transports: ['websocket']
    })

    newSocket.on('telemetry', (data) => {
      if (data.players.player1) setPlayer1Data(data.players.player1)
      if (data.players.player2) setPlayer2Data(data.players.player2)
    })

    setSocket(newSocket)
    return () => { newSocket.close() }
  }, [])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
      <PlayerDashboard
        data={player1Data}
        playerName="Player 1"
        accentColor="blue"
      />
      <PlayerDashboard
        data={player2Data}
        playerName="Player 2"
        accentColor="red"
      />
      <div className="lg:col-span-2">
        <ComparisonMetrics
          player1={player1Data}
          player2={player2Data}
        />
      </div>
    </div>
  )
}
```

### Phase 4: Tailwind Styling

```tsx
// app/components/UI/Card.tsx
import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'glass' | 'gradient'
}

export function Card({ children, className, variant = 'default' }: CardProps) {
  const variants = {
    default: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800',
    glass: 'bg-white/10 backdrop-blur-md border border-white/20',
    gradient: 'bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-sm'
  }

  return (
    <div className={cn(
      'rounded-xl shadow-lg p-6 transition-all hover:shadow-xl',
      variants[variant],
      className
    )}>
      {children}
    </div>
  )
}
```

### Phase 5: Real-time Visualizations

```tsx
// app/components/Telemetry/SpeedComparison.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { motion } from 'framer-motion'

export function SpeedComparison({ player1, player2 }) {
  const data = useSpeedHistory(player1, player2) // Custom hook for data

  return (
    <Card variant="glass">
      <h3 className="text-lg font-semibold mb-4">Speed Comparison</h3>
      <LineChart width={600} height={200} data={data}>
        <Line
          type="monotone"
          dataKey="player1"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="player2"
          stroke="#EF4444"
          strokeWidth={2}
          dot={false}
        />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
      </LineChart>

      <div className="flex justify-between mt-4">
        <motion.div
          animate={{ scale: player1?.speed > player2?.speed ? 1.1 : 1 }}
          className="text-blue-500"
        >
          P1: {player1?.speed || 0} km/h
        </motion.div>
        <motion.div
          animate={{ scale: player2?.speed > player1?.speed ? 1.1 : 1 }}
          className="text-red-500"
        >
          P2: {player2?.speed || 0} km/h
        </motion.div>
      </div>
    </Card>
  )
}
```

## Configuration

### Backend Config
```yaml
# backend/config.yaml
players:
  player1:
    name: "Driver 1"
    port: 20777
    color: "#3B82F6"
  player2:
    name: "Driver 2"
    port: 20778
    color: "#EF4444"

websocket:
  host: "0.0.0.0"
  port: 8000

datacloud:
  enabled: true
  endpoint: "https://..."
  batch_size: 20
  flush_interval: 2
```

### Frontend Environment
```env
# frontend/.env.local
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:3000
```

## Key Features

### 1. Dual Player Support
- Simultaneous telemetry from 2 F1 games
- Real-time synchronization
- Player identification and color coding

### 2. Comparison Views
- Side-by-side dashboards
- Overlaid metrics (speed, lap times)
- Delta timing between players
- Sector comparisons
- Live position tracking

### 3. Modern UI with Tailwind
- Dark/light theme with `next-themes`
- Responsive grid layouts
- Glass morphism effects
- Smooth animations with Framer Motion
- Custom color schemes per player

### 4. Performance Optimizations
- Server Components where possible
- WebSocket for real-time updates
- Virtualized lists for lap history
- Memoized expensive calculations
- Lazy loading of heavy components

### 5. Data Cloud Integration
- Batch telemetry uploads
- Player session tracking
- Historical data analysis
- Leaderboard persistence

## Development Workflow

```bash
# Start backend service
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python multi_receiver.py

# Start Next.js dev server
cd frontend
npm run dev

# Configure F1 games
# Game 1: UDP to 127.0.0.1:20777
# Game 2: UDP to 127.0.0.1:20778
```

## Deployment (Local)

```bash
# Build Next.js for production
cd frontend
npm run build
npm start

# Run backend with PM2
pm2 start backend/multi_receiver.py --interpreter python3
```

## Future Enhancements

1. **Multi-player support (3+ players)**
2. **Race replay system**
3. **AI-powered race analysis**
4. **Voice commentary generation**
5. **VR/AR dashboard view**
6. **Mobile companion app**
7. **Stream to Twitch/YouTube overlay**
8. **Historical race database**

## Benefits of Next.js + Tailwind

1. **Developer Experience**
   - Hot reload
   - TypeScript support
   - Built-in optimization

2. **Performance**
   - SSR/SSG capabilities
   - Image optimization
   - Code splitting

3. **Styling**
   - Utility-first CSS
   - Dark mode support
   - Responsive by default
   - No CSS-in-JS overhead

4. **Ecosystem**
   - Rich component libraries
   - Great tooling
   - Active community