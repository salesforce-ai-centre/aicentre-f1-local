// F1 Simulator Window Controller - Background Script
// Manages native messaging to control window switching

console.log('F1 Window Controller: Background script loaded');

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);

  if (request.action === 'switchToGame') {
    switchToGame().then(sendResponse);
    return true; // Keep channel open for async response
  }

  if (request.action === 'switchToBrowser') {
    switchToBrowser().then(sendResponse);
    return true;
  }

  if (request.action === 'ping') {
    sendResponse({ status: 'alive' });
    return true;
  }
});

async function switchToGame() {
  console.log('Switching to F1 game...');

  try {
    // Send message to native host
    const response = await sendNativeMessage({ command: 'switchToGame' });
    console.log('Native host response:', response);
    return { success: true, message: 'Switched to game', response };
  } catch (error) {
    console.error('Failed to switch to game:', error);
    return { success: false, error: error.message };
  }
}

async function switchToBrowser() {
  console.log('Switching to browser...');

  try {
    // Send message to native host
    const response = await sendNativeMessage({ command: 'switchToBrowser' });
    console.log('Native host response:', response);
    return { success: true, message: 'Switched to browser', response };
  } catch (error) {
    console.error('Failed to switch to browser:', error);
    return { success: false, error: error.message };
  }
}

function sendNativeMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendNativeMessage(
      'com.f1.windowswitcher',
      message,
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      }
    );
  });
}

// Monitor extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('F1 Window Controller installed');
  } else if (details.reason === 'update') {
    console.log('F1 Window Controller updated');
  }
});
