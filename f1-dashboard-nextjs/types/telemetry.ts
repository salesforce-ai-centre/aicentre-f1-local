export interface TelemetryData {
  // Session
  driverName?: string
  trackName?: string
  position?: number
  currentLap?: number
  currentLapInvalid?: boolean
  currentLapTime?: number
  lastLapTime?: number
  bestLapTime?: number

  // Vehicle
  speed?: number
  engineRPM?: number
  gear?: number
  throttle?: number
  brake?: number
  steer?: number
  drs?: number
  drsAvailable?: boolean

  // Tyres
  tyresWear?: number[]
  tyresSurfaceTemperature?: number[]
  actualTyreCompound?: string

  // ERS
  ersStoreEnergy?: number
  ersDeployMode?: string

  // Damage
  frontLeftWingDamage?: number
  frontRightWingDamage?: number
  rearWingDamage?: number
  floorDamage?: number
  engineDamage?: number
  gearBoxDamage?: number

  // G-Force
  gForceLateral?: number
  gForceLongitudinal?: number

  // Fuel
  fuelInTank?: number
  fuelMix?: string
  fuelRemainingLaps?: number

  // Events
  event?: {
    message: string
    type: string
  }
  aiCoachMessage?: string
  lapCompleted?: boolean
}

export interface WebSocketMessage {
  type: 'telemetry' | 'event' | 'status'
  data: TelemetryData
  timestamp?: string
}