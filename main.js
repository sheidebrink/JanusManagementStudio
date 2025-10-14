const { app, BrowserWindow, ipcMain, safeStorage } = require('electron');
const path = require('path');
const fs = require('fs');
const sql = require('mssql');

let mainWindow;
let dbConnection = null;
let currentTenant = null;
let currentDatabase = null;
const credentialsPath = path.join(__dirname, 'credentials.dat');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 450,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    resizable: false,
    title: 'Janus Management Studio',
    icon: null
  });

  mainWindow.loadFile('login.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (dbConnection) {
    dbConnection.close();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle database connection
ipcMain.handle('connect-database', async (event, config) => {
  try {
    if (dbConnection) {
      await dbConnection.close();
    }
    
    dbConnection = await sql.connect({
      server: config.server,
      database: config.database,
      user: config.username,
      password: config.password,
      options: {
        encrypt: config.encrypt || false,
        trustServerCertificate: true
      }
    });
    
    currentDatabase = `${config.server}\\${config.database}`;
    
    // Set default tenant to 1
    currentTenant = { id: 1, name: 'Default Tenant' };
    
    // Save credentials if requested
    if (config.saveCredentials && safeStorage.isEncryptionAvailable()) {
      const credentials = {
        server: config.server,
        database: config.database,
        username: config.username,
        password: config.password
      };
      const encrypted = safeStorage.encryptString(JSON.stringify(credentials));
      fs.writeFileSync(credentialsPath, encrypted);
    }
    
    return { success: true, database: currentDatabase };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Handle SQL queries
ipcMain.handle('execute-query', async (event, query) => {
  try {
    if (!dbConnection) {
      throw new Error('No database connection');
    }
    
    const result = await dbConnection.request().query(query);
    return { success: true, data: result.recordset };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Switch to main app window
ipcMain.handle('show-main-app', () => {
  mainWindow.setSize(1200, 800);
  mainWindow.setResizable(true);
  mainWindow.center();
  mainWindow.setTitle('Janus Management Studio');
  mainWindow.loadFile('app.html');
});

// Set current tenant
ipcMain.handle('set-tenant', (event, tenantId, tenantName) => {
  currentTenant = { id: tenantId, name: tenantName };
  return { success: true };
});

// Get current context
ipcMain.handle('get-context', () => {
  return {
    database: currentDatabase,
    tenant: currentTenant
  };
});

// Load saved credentials
ipcMain.handle('load-credentials', () => {
  try {
    if (fs.existsSync(credentialsPath) && safeStorage.isEncryptionAvailable()) {
      const encrypted = fs.readFileSync(credentialsPath);
      const decrypted = safeStorage.decryptString(encrypted);
      return JSON.parse(decrypted);
    }
  } catch (error) {
    console.error('Failed to load credentials:', error);
  }
  return null;
});

// Clear saved credentials
ipcMain.handle('clear-credentials', () => {
  try {
    if (fs.existsSync(credentialsPath)) {
      fs.unlinkSync(credentialsPath);
    }
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});