const { ipcRenderer } = require('electron');

// Load saved credentials on page load
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const credentials = await ipcRenderer.invoke('load-credentials');
    if (credentials) {
      document.getElementById('server').value = credentials.server;
      document.getElementById('database').value = credentials.database;
      document.getElementById('username').value = credentials.username;
      document.getElementById('password').value = credentials.password;
      document.getElementById('saveCredentials').checked = true;
    }
  } catch (error) {
    console.error('Failed to load saved credentials:', error);
  }
});

async function clearSavedCredentials() {
  try {
    await ipcRenderer.invoke('clear-credentials');
    document.getElementById('server').value = 'GEMINI';
    document.getElementById('database').value = 'JanusPlatformQA';
    document.getElementById('username').value = 'IrisPlatformCreate';
    document.getElementById('password').value = '';
    document.getElementById('saveCredentials').checked = false;
    alert('Saved credentials cleared');
  } catch (error) {
    alert('Failed to clear credentials: ' + error.message);
  }
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const loginBtn = document.getElementById('loginBtn');
  const message = document.getElementById('message');
  
  loginBtn.disabled = true;
  loginBtn.textContent = 'Connecting...';
  message.innerHTML = '<div class="loading">Connecting to database...</div>';
  
  const config = {
    server: document.getElementById('server').value,
    database: document.getElementById('database').value,
    username: document.getElementById('username').value,
    password: document.getElementById('password').value,
    encrypt: false,
    saveCredentials: document.getElementById('saveCredentials').checked
  };
  
  try {
    const result = await ipcRenderer.invoke('connect-database', config);
    
    if (result.success) {
      message.innerHTML = '<div style="color: green;">Connected successfully!</div>';
      setTimeout(async () => {
        await ipcRenderer.invoke('show-main-app');
      }, 1000);
    } else {
      message.innerHTML = `<div class="error">Connection failed: ${result.error}</div>`;
      loginBtn.disabled = false;
      loginBtn.textContent = 'Connect';
    }
  } catch (error) {
    message.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    loginBtn.disabled = false;
    loginBtn.textContent = 'Connect';
  }
});