const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const sql = require('mssql');

let mainWindow;
let dbConnection = null;
let currentTenant = null;
let currentDatabase = null;

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