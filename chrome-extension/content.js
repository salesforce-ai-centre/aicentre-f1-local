// F1 Simulator Window Controller - Content Script
// Injected into F1 simulator web pages to listen for race events

console.log('F1 Window Controller: Content script loaded');

// Check if extension is working
chrome.runtime.sendMessage({ action: 'ping' }, (response) => {
  if (response && response.status === 'alive') {
    console.log('✓ Extension is active and ready');
    showExtensionStatus(true);
  } else {
    console.error('✗ Extension is not responding');
    showExtensionStatus(false);
  }
});

// Listen for custom events from the web page
window.addEventListener('f1:switchToGame', () => {
  console.log('Received f1:switchToGame event');
  switchToGame();
});

window.addEventListener('f1:switchToBrowser', () => {
  console.log('Received f1:switchToBrowser event');
  switchToBrowser();
});

// Also listen for postMessage (alternative method)
window.addEventListener('message', (event) => {
  // Only accept messages from same origin
  if (event.origin !== window.location.origin) {
    return;
  }

  if (event.data.type === 'F1_SWITCH_TO_GAME') {
    console.log('Received F1_SWITCH_TO_GAME message');
    switchToGame();
  }

  if (event.data.type === 'F1_SWITCH_TO_BROWSER') {
    console.log('Received F1_SWITCH_TO_BROWSER message');
    switchToBrowser();
  }
});

function switchToGame() {
  chrome.runtime.sendMessage(
    { action: 'switchToGame' },
    (response) => {
      if (response && response.success) {
        console.log('✓ Successfully switched to game');
        notifyPage({ type: 'F1_SWITCHED_TO_GAME', success: true });
      } else {
        console.error('✗ Failed to switch to game:', response);
        notifyPage({ type: 'F1_SWITCH_FAILED', error: response?.error });
      }
    }
  );
}

function switchToBrowser() {
  chrome.runtime.sendMessage(
    { action: 'switchToBrowser' },
    (response) => {
      if (response && response.success) {
        console.log('✓ Successfully switched to browser');
        notifyPage({ type: 'F1_SWITCHED_TO_BROWSER', success: true });
      } else {
        console.error('✗ Failed to switch to browser:', response);
        notifyPage({ type: 'F1_SWITCH_FAILED', error: response?.error });
      }
    }
  );
}

function notifyPage(message) {
  // Send message back to web page
  window.postMessage(message, window.location.origin);
}

function showExtensionStatus(isActive) {
  // Inject status indicator into page
  const statusDiv = document.createElement('div');
  statusDiv.id = 'f1-extension-status';
  statusDiv.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    padding: 8px 12px;
    background: ${isActive ? '#4CAF50' : '#f44336'};
    color: white;
    border-radius: 4px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    z-index: 999999;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  `;
  statusDiv.textContent = isActive
    ? '✓ F1 Controller Active'
    : '✗ F1 Controller Error';

  document.body.appendChild(statusDiv);

  // Fade out after 3 seconds
  setTimeout(() => {
    statusDiv.style.transition = 'opacity 0.5s';
    statusDiv.style.opacity = '0';
    setTimeout(() => statusDiv.remove(), 500);
  }, 3000);
}

// Expose API to window for easy testing
window.F1Controller = {
  switchToGame,
  switchToBrowser,
  test: () => {
    console.log('F1 Controller Test');
    console.log('Try: F1Controller.switchToGame()');
    console.log('Try: F1Controller.switchToBrowser()');
  }
};

console.log('F1 Controller ready. Type F1Controller.test() in console to see available commands.');
