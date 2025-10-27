# Contributing to F1 Dual-Rig Telemetry Dashboard

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. Use the bug report template
3. Include:
   - Python version
   - F1 game version (F1 25 or F1 24)
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots/logs if applicable

### Suggesting Features

1. Check if the feature has been requested
2. Open an issue with "Feature Request" label
3. Describe:
   - Use case and motivation
   - Proposed implementation
   - Any alternatives considered

### Pull Requests

#### Before You Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Set up development environment:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   ```

#### Development Guidelines

**Code Style**
- Follow PEP 8 for Python code
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to functions/classes

**Python Example:**
```python
def calculate_lap_time(milliseconds: int) -> str:
    """
    Convert lap time from milliseconds to formatted string.

    Args:
        milliseconds: Lap time in milliseconds

    Returns:
        Formatted string in MM:SS.mmm format

    Example:
        >>> calculate_lap_time(92456)
        '1:32.456'
    """
    minutes = milliseconds // 60000
    seconds = (milliseconds % 60000) / 1000
    return f"{minutes}:{seconds:06.3f}"
```

**JavaScript Style**
- Use ES6+ features
- Use `const` for constants, `let` for variables
- Add JSDoc comments for functions
- Use camelCase for variables

**JavaScript Example:**
```javascript
/**
 * Update telemetry display element
 * @param {string} elementId - DOM element ID
 * @param {any} value - Value to display
 * @param {Function} formatter - Optional formatting function
 */
function updateElement(elementId, value, formatter = null) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const displayValue = formatter ? formatter(value) : value;
    element.textContent = displayValue;
}
```

#### Commit Guidelines

Use semantic commit messages:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(track-map): add marshal zone visualization

- Implement color-coded marshal zones
- Add flag status indicators
- Update rendering logic

Closes #123
```

```
fix(receiver): handle malformed UDP packets gracefully

Previously, malformed packets would crash the receiver.
Now they are logged and skipped.

Fixes #456
```

#### Testing

1. Test your changes thoroughly:
   ```bash
   # Run unit tests
   python -m pytest tests/

   # Run performance tests
   python3 scripts/run_performance_test.py

   # Test with actual F1 game
   python3 scripts/run_dual_dashboard.py
   ```

2. Ensure no regressions in existing functionality
3. Add tests for new features
4. Update documentation if needed

#### Pull Request Process

1. Update README.md if adding features
2. Update documentation in `docs/` if needed
3. Ensure all tests pass
4. Update CHANGELOG.md (coming soon)
5. Submit PR with clear description:
   - What changed
   - Why it changed
   - How to test it
   - Screenshots/videos if UI changes

**PR Template:**
```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of changes

## Testing
How to test these changes

## Screenshots (if applicable)
Before/after screenshots

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
```

### Adding New Telemetry Fields

To add a new telemetry field from F1 game:

1. **Decode in receiver** (`src/receiver_multi.py`):
   ```python
   def _handle_car_telemetry(self, header, payload):
       # ... existing code ...
       'newField': player_telem.m_newField,
   ```

2. **Add to WebSocket publisher** (`src/websocket_publisher.py`):
   ```python
   # Usually automatic via pass-through
   ```

3. **Add HTML element** (`templates/dual_rig_dashboard.html`):
   ```html
   <div class="metric-card">
       <h3>New Metric</h3>
       <div class="metric-value" id="rigA-newMetric">--</div>
   </div>
   ```

4. **Update JavaScript** (`static/js/dual-rig-dashboard.js`):
   ```javascript
   if (data.newField !== undefined) {
       updateElement(`${prefix}-newMetric`, data.newField);
   }
   ```

5. **Test with real game data**

### Adding New Track Circuits

1. Obtain racing line data (CSV format: distance, x, y, z)
2. Add to `static/tracks/` directory
3. Update `TRACK_DICTIONARY` in `static/js/track-map.js`:
   ```javascript
   42: { name: "new_track", scale: 2, offsetX: 300, offsetZ: 300 }
   ```
4. Test with session at that track

## Project Structure

```
src/              - Python backend code
  ├── app_dual_rig.py        - Main Flask application
  ├── receiver_multi.py      - UDP packet decoder
  ├── telemetry_gateway.py   - Multi-rig coordinator
  └── websocket_publisher.py - WebSocket broadcaster

templates/        - HTML templates
  └── dual_rig_dashboard.html - Main dashboard UI

static/           - Frontend assets
  ├── js/
  │   ├── dual-rig-dashboard.js - Dashboard logic
  │   └── track-map.js          - Track visualization
  ├── css/
  │   └── dual-rig-style.css    - Styling
  └── tracks/                   - Circuit data

docs/             - Documentation
scripts/          - Utility scripts
tests/            - Test suite
```

## Development Environment

### Prerequisites
- Python 3.8+
- pip
- Git
- F1 25 or F1 24 game (for testing)

### Setup

```bash
# Clone
git clone <repository-url>
cd aicentre-f1-local

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run
python3 scripts/run_dual_dashboard.py
```

### Development Tips

1. **Use debug mode:**
   ```bash
   export FLASK_DEBUG=true
   python3 src/app_dual_rig.py
   ```

2. **Check logs:**
   ```bash
   tail -f logs/dashboard.log
   ```

3. **Test UDP reception:**
   ```bash
   python3 scripts/test_dual_receiver.py
   ```

4. **Monitor performance:**
   ```bash
   python3 tests/performance_monitor.py
   ```

## Documentation

When adding features, update relevant documentation:

- `README.md` - User-facing features
- `docs/setup/` - Installation/configuration changes
- `docs/architecture/` - System design changes
- `docs/development/` - Developer information
- Code comments - Inline documentation

## Questions?

- Open an issue for questions
- Check existing documentation in `docs/`
- Review code comments

## Recognition

Contributors will be added to CONTRIBUTORS.md (coming soon)

Thank you for contributing! 🎉
