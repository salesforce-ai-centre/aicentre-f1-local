#!/usr/bin/env python3
"""
F1 Window Switcher - Native Messaging Host
Communicates with Chrome extension to switch windows
"""

import sys
import json
import struct
import subprocess
import platform
import logging

# Set up logging
logging.basicConfig(
    filename='/tmp/f1-window-switcher.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_message(message):
    """Send message to Chrome extension"""
    try:
        encoded = json.dumps(message).encode('utf-8')
        sys.stdout.buffer.write(struct.pack('I', len(encoded)))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
        logging.info(f'Sent message: {message}')
    except Exception as e:
        logging.error(f'Failed to send message: {e}')

def read_message():
    """Read message from Chrome extension"""
    try:
        text_length_bytes = sys.stdin.buffer.read(4)
        if len(text_length_bytes) == 0:
            logging.info('No more input, exiting')
            sys.exit(0)

        text_length = struct.unpack('i', text_length_bytes)[0]
        text = sys.stdin.buffer.read(text_length).decode('utf-8')
        message = json.loads(text)
        logging.info(f'Received message: {message}')
        return message
    except Exception as e:
        logging.error(f'Failed to read message: {e}')
        return None

def switch_to_game():
    """Switch to F1 game window"""
    os_type = platform.system()
    logging.info(f'Switching to game on {os_type}')

    try:
        if os_type == 'Linux':
            # Try multiple methods to find and activate F1 game
            commands = [
                # Try exact match first
                ['wmctrl', '-a', 'F1'],
                # Try case-insensitive
                ['wmctrl', '-i', '-a', 'f1'],
                # Try partial match
                ['wmctrl', '-a', 'EA'],
                # Use xdotool as fallback
                ['xdotool', 'search', '--name', 'F1', 'windowactivate'],
            ]

            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        logging.info(f'Successfully switched using: {" ".join(cmd)}')
                        return {'status': 'success', 'method': ' '.join(cmd)}
                except subprocess.TimeoutExpired:
                    logging.warning(f'Command timed out: {" ".join(cmd)}')
                except FileNotFoundError:
                    logging.warning(f'Command not found: {cmd[0]}')
                except Exception as e:
                    logging.warning(f'Command failed: {e}')

            # If all else fails, try Alt+Tab
            logging.info('All methods failed, trying Alt+Tab simulation')
            subprocess.run(['xdotool', 'key', 'alt+Tab'], timeout=2)
            return {'status': 'success', 'method': 'alt+tab'}

        elif os_type == 'Windows':
            # PowerShell to activate F1 window
            ps_script = '''
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {
                    [DllImport("user32.dll")]
                    public static extern bool SetForegroundWindow(IntPtr hWnd);
                }
"@

            $processes = Get-Process | Where-Object {
                $_.MainWindowTitle -like "*F1*" -or
                $_.ProcessName -like "*F1*" -or
                $_.ProcessName -like "*EA*"
            }

            foreach ($proc in $processes) {
                if ($proc.MainWindowHandle -ne 0) {
                    [Win32]::SetForegroundWindow($proc.MainWindowHandle)
                    Write-Output "Activated: $($proc.ProcessName)"
                    exit 0
                }
            }

            # Fallback: Alt+Tab
            (New-Object -ComObject WScript.Shell).SendKeys("%{TAB}")
            '''

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            logging.info(f'PowerShell result: {result.stdout}')
            return {'status': 'success', 'method': 'powershell'}

        elif os_type == 'Darwin':  # macOS
            # Try to activate F1 game
            apps = ['F1 25', 'F1 24', 'F1 2025', 'F1 2024', 'EA']

            for app in apps:
                try:
                    result = subprocess.run(
                        ['osascript', '-e', f'tell application "{app}" to activate'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        logging.info(f'Activated {app}')
                        return {'status': 'success', 'app': app}
                except:
                    continue

            # Fallback: Cmd+Tab
            subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke tab using command down'])
            return {'status': 'success', 'method': 'cmd+tab'}

        else:
            logging.error(f'Unsupported OS: {os_type}')
            return {'status': 'error', 'message': f'Unsupported OS: {os_type}'}

    except Exception as e:
        logging.error(f'Error switching to game: {e}')
        return {'status': 'error', 'message': str(e)}

def switch_to_browser():
    """Switch to Chrome browser window"""
    os_type = platform.system()
    logging.info(f'Switching to browser on {os_type}')

    try:
        if os_type == 'Linux':
            commands = [
                ['wmctrl', '-a', 'Chrome'],
                ['wmctrl', '-a', 'Google Chrome'],
                ['wmctrl', '-a', 'Chromium'],
                ['xdotool', 'search', '--name', 'Chrome', 'windowactivate'],
            ]

            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        logging.info(f'Successfully switched using: {" ".join(cmd)}')
                        return {'status': 'success', 'method': ' '.join(cmd)}
                except:
                    continue

            # Fallback: Alt+Tab
            subprocess.run(['xdotool', 'key', 'alt+Tab'], timeout=2)
            return {'status': 'success', 'method': 'alt+tab'}

        elif os_type == 'Windows':
            ps_script = '''
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {
                    [DllImport("user32.dll")]
                    public static extern bool SetForegroundWindow(IntPtr hWnd);
                }
"@

            $chrome = Get-Process chrome, googlechrome, chromium -ErrorAction SilentlyContinue |
                      Where-Object { $_.MainWindowHandle -ne 0 } |
                      Select-Object -First 1

            if ($chrome) {
                [Win32]::SetForegroundWindow($chrome.MainWindowHandle)
                Write-Output "Activated Chrome"
            }
            '''

            subprocess.run(
                ['powershell', '-Command', ps_script],
                timeout=5
            )
            return {'status': 'success', 'method': 'powershell'}

        elif os_type == 'Darwin':  # macOS
            apps = ['Google Chrome', 'Chrome', 'Chromium']

            for app in apps:
                try:
                    result = subprocess.run(
                        ['osascript', '-e', f'tell application "{app}" to activate'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        logging.info(f'Activated {app}')
                        return {'status': 'success', 'app': app}
                except:
                    continue

            return {'status': 'success', 'method': 'fallback'}

        else:
            return {'status': 'error', 'message': f'Unsupported OS: {os_type}'}

    except Exception as e:
        logging.error(f'Error switching to browser: {e}')
        return {'status': 'error', 'message': str(e)}

# Main loop
logging.info('F1 Window Switcher native host starting...')

while True:
    try:
        message = read_message()
        if not message:
            break

        command = message.get('command')

        if command == 'switchToGame':
            result = switch_to_game()
            send_message(result)

        elif command == 'switchToBrowser':
            result = switch_to_browser()
            send_message(result)

        else:
            send_message({'status': 'error', 'message': f'Unknown command: {command}'})

    except Exception as e:
        logging.error(f'Error in main loop: {e}')
        send_message({'status': 'error', 'message': str(e)})
        break

logging.info('F1 Window Switcher native host exiting')
