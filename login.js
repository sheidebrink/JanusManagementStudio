const { ipcRenderer } = require('electron');

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
    encrypt: false
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