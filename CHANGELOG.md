# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-23

### Added
- **Dual-rig support**: Monitor two F1 simulators simultaneously
- **Track map visualization**: Live 2D track rendering with both drivers' positions
- **3-column layout**: Optimized for 55-inch 4K TV displays (Sim 1 | Map | Sim 2)
- **Marshal zone visualization**: Color-coded track zones based on flag status
- **Motion packet handling**: World position tracking for track map
- **Session state management**: Auto-detect session start/end, clear stale data
- **Steering input visualization**: Horizontal bar showing steering angle
- **Track auto-detection**: Automatically load correct circuit from session data
- **WebSocket streaming**: Real-time data broadcast with Flask-SocketIO
- **Multi-rig architecture**: Telemetry gateway for coordinating multiple receivers
- **Sector time display**: S1/S2/S3 breakdown per driver
- **Tire compound and age**: Visual indicators for tire management
- **Enhanced telemetry**: Throttle, brake, steering inputs with visual bars

### Changed
- **Layout restructure**: From 2-column to 3-column layout for better comparison
- **Font sizes**: Increased for 4K TV viewing (4rem speed, 3.5rem gear)
- **Track line width**: 5px (was 3px) for better visibility
- **Car markers**: 10px radius (was 6px) for TV displays
- **Responsive removed**: Fixed layout for large screen only (no mobile support)
- **UDP receiver**: Refactored to `receiver_multi.py` with callback pattern
- **Configuration**: Moved to environment variables (.env file)

### Fixed
- **Lap time display**: Proper formatting for all time values
- **WebSocket stability**: Changed from eventlet to threading mode
- **Session transitions**: Clear data when new session starts
- **Ping timeout**: Added 60s timeout, 25s interval for stable connections

### Improved
- **Performance**: <10ms latency from UDP to display
- **Memory usage**: <150MB total for dual-rig operation
- **CPU efficiency**: <5% per receiver on dual-core system

## [1.5.0] - 2025-10-20

### Added
- **Project cleanup**: Organized file structure for maintainability
- **Comprehensive documentation**: Setup guides, architecture docs, feature roadmap
- **Environment template**: `.env.example` with all configuration options
- **Contributing guide**: Guidelines for contributors
- **Archive system**: Moved old/unused files to `archive/` directory

### Changed
- **Requirements location**: Moved to root for standard Python convention
- **Documentation structure**: Reorganized into `docs/` subdirectories
- **Code organization**: Proper separation of concerns

### Removed
- **Old templates**: Archived `index-enhanced.html`, `index-original.html`
- **Old stylesheets**: Archived multiple CSS variants
- **Old JavaScript**: Archived `script-enhanced.js`, `script-original.js`

## [1.0.0] - 2025-09-15

### Added
- **Single-rig telemetry dashboard**: Monitor one F1 simulator
- **Real-time data visualization**: Speed, RPM, gear, position, lap times
- **Server-Sent Events (SSE)**: Real-time data streaming
- **Data Cloud integration**: Stream telemetry to Salesforce Data Cloud
- **AI Race Engineer**: GPT-4o powered race coaching (experimental)
- **Event detection**: Lap completion, damage, tire wear, fuel strategy
- **UDP packet parsing**: F1 25 and F1 24 protocol support
- **Flask web server**: Lightweight Python backend
- **Chart.js visualizations**: Gauges and real-time charts

### Technical Details
- **UDP receiver**: Port 20777, 60Hz packet rate
- **Binary protocol**: Struct unpacking for F1 telemetry
- **JWT authentication**: For Data Cloud integration
- **Async AI generation**: Thread pool for non-blocking coach messages

---

## Version History

### v2.0.0 (Current) - Dual-Rig + Track Map
Major release with dual-simulator support and live track visualization

### v1.5.0 - Project Maintenance
Cleanup and organization for production readiness

### v1.0.0 - Initial Release
Single-rig telemetry dashboard with Data Cloud integration

---

## Upcoming Features (Roadmap)

### v2.1.0 (Planned)
- [ ] Race director event log
- [ ] Speed trap analytics
- [ ] Weather forecast display
- [ ] Replay mode with session recording

### v2.2.0 (Planned)
- [ ] Multi-tab dashboard organization
- [ ] Comparative sector time visualization
- [ ] Voice announcements for key events
- [ ] Mobile companion app

### v3.0.0 (Future)
- [ ] Multi-session comparison
- [ ] Historical data analysis
- [ ] Strategy simulation
- [ ] Team dashboard (4+ simulators)

---

## Versioning

- **Major (X.0.0)**: Breaking changes, major features
- **Minor (x.X.0)**: New features, backward compatible
- **Patch (x.x.X)**: Bug fixes, minor improvements

---

## Links

- [Feature Roadmap](docs/development/FEATURE_ANALYSIS.md)
- [Architecture Documentation](docs/architecture/DUAL_RIG_ARCHITECTURE.md)
- [Setup Guide](docs/setup/DUAL_RIG_SETUP.md)
