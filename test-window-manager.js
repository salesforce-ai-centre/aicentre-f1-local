/**
 * Window Manager Test Script
 *
 * Tests node-window-manager functionality for Beam's external app switching feature.
 * Run this on the Windows F1 Simulator PC to validate window enumeration and focusing.
 *
 * Setup:
 *   npm init -y
 *   npm install node-window-manager
 *
 * Usage:
 *   node test-window-manager.js              # List all windows
 *   node test-window-manager.js "F1"         # Focus window with "F1" in title
 *   node test-window-manager.js "Media"      # Focus Windows Media Player
 *   node test-window-manager.js "Photos"     # Focus Photos app
 */

const { windowManager } = require("node-window-manager");

// Get CLI argument for window title pattern
const targetPattern = process.argv[2];

// List all open windows
console.log("\n========================================");
console.log("  OPEN WINDOWS");
console.log("========================================\n");

const windows = windowManager.getWindows();
const windowsWithTitles = windows.filter(win => {
  try {
    const title = win.getTitle();
    return title && title.trim().length > 0;
  } catch {
    return false;
  }
});

if (windowsWithTitles.length === 0) {
  console.log("No windows found. This may indicate:");
  console.log("  - node-window-manager needs to be rebuilt for this Node version");
  console.log("  - Permissions issue on this system");
  console.log("");
} else {
  windowsWithTitles.forEach((win, i) => {
    const title = win.getTitle();
    console.log(`[${i.toString().padStart(2, " ")}] ${title}`);
  });
  console.log(`\n  Total: ${windowsWithTitles.length} windows\n`);
}

// If a pattern was provided, try to focus that window
if (targetPattern) {
  console.log("========================================");
  console.log(`  FOCUSING: "${targetPattern}"`);
  console.log("========================================\n");

  const target = windowsWithTitles.find(win =>
    win.getTitle().toLowerCase().includes(targetPattern.toLowerCase())
  );

  if (target) {
    const title = target.getTitle();
    console.log(`Found: "${title}"`);

    try {
      target.bringToTop();
      console.log("SUCCESS - Window should now be focused\n");
    } catch (err) {
      console.log(`FAILED - Could not focus window: ${err.message}\n`);
    }
  } else {
    console.log(`NOT FOUND - No window title contains "${targetPattern}"`);
    console.log("\nAvailable windows:");
    windowsWithTitles.slice(0, 10).forEach(win => {
      console.log(`  - ${win.getTitle()}`);
    });
    if (windowsWithTitles.length > 10) {
      console.log(`  ... and ${windowsWithTitles.length - 10} more`);
    }
    console.log("");
  }
} else {
  console.log("TIP: Pass a window title pattern to focus it:");
  console.log('  node test-window-manager.js "F1"');
  console.log('  node test-window-manager.js "Media Player"');
  console.log("");
}
