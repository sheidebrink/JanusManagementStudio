const { app, BrowserWindow, ipcMain, safeStorage, screen } = require('electron');
const path = require('path');
const fs = require('fs');
const sql = require('mssql');
const { BedrockRuntimeClient, InvokeModelCommand } = require('@aws-sdk/client-bedrock-runtime');

let mainWindow;
let dbConnection = null;
let currentTenant = null;
let currentDatabase = null;
const credentialsPath = path.join(__dirname, 'credentials.dat');
const windowStatePath = path.join(__dirname, 'windowstate.json');

function createWindow() {
  const windowState = loadWindowState();
  
  mainWindow = new BrowserWindow({
    width: windowState.width || 450,
    height: windowState.height || 600,
    x: windowState.x,
    y: windowState.y,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    resizable: false,
    title: 'Janus Management Studio',
    icon: null
  });

  mainWindow.loadFile('login.html');
  
  // Add keyboard shortcut for developer tools
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.control && input.shift && input.key.toLowerCase() === 'i') {
      mainWindow.webContents.toggleDevTools();
    }
    if (input.key === 'F12') {
      mainWindow.webContents.toggleDevTools();
    }
  });
  
  mainWindow.on('moved', saveWindowState);
  mainWindow.on('resized', saveWindowState);
}

function loadWindowState() {
  try {
    if (fs.existsSync(windowStatePath)) {
      const state = JSON.parse(fs.readFileSync(windowStatePath, 'utf8'));
      const displays = screen.getAllDisplays();
      
      // Check if saved position is still valid
      const validDisplay = displays.find(display => 
        state.x >= display.bounds.x && 
        state.x < display.bounds.x + display.bounds.width &&
        state.y >= display.bounds.y && 
        state.y < display.bounds.y + display.bounds.height
      );
      
      if (validDisplay) {
        return state;
      }
    }
  } catch (error) {
    console.error('Failed to load window state:', error);
  }
  
  // Default to primary display center
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  return {
    x: Math.round((width - 450) / 2),
    y: Math.round((height - 600) / 2),
    width: 450,
    height: 600
  };
}

function saveWindowState() {
  try {
    const bounds = mainWindow.getBounds();
    fs.writeFileSync(windowStatePath, JSON.stringify(bounds));
  } catch (error) {
    console.error('Failed to save window state:', error);
  }
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
      },
      requestTimeout: 60000
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
    
    console.log('\n=== SQL QUERY ===');
    console.log(query);
    console.log('================\n');
    
    const result = await dbConnection.request().query(query);
    return { success: true, data: result.recordset };
  } catch (error) {
    console.log('\n=== SQL ERROR ===');
    console.log('Query:', query);
    console.log('Error:', error.message);
    console.log('=================\n');
    return { success: false, error: error.message };
  }
});

// Switch to main app window
ipcMain.handle('show-main-app', () => {
  mainWindow.setSize(1200, 800);
  mainWindow.setResizable(true);
  mainWindow.setTitle('Janus Management Studio');
  mainWindow.loadFile('app.html');
  saveWindowState();
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

// Toggle developer tools
ipcMain.handle('toggle-dev-tools', () => {
  mainWindow.webContents.toggleDevTools();
});

// AI Analysis with AWS Bedrock
ipcMain.handle('analyze-with-ai', async (event, prompt) => {
  try {
    const client = new BedrockRuntimeClient({ region: 'us-east-1' });
    
    const command = new InvokeModelCommand({
      modelId: 'anthropic.claude-3-haiku-20240307-v1:0',
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify({
        anthropic_version: 'bedrock-2023-05-31',
        max_tokens: 4000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });
    
    const response = await client.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    
    // Try to parse the AI response as JSON
    let aiResponse = responseBody.content[0].text;
    try {
      const jsonMatch = aiResponse.match(/\[.*\]/s);
      if (jsonMatch) {
        aiResponse = JSON.parse(jsonMatch[0]);
      }
    } catch (parseError) {
      // If JSON parsing fails, return the raw text
    }
    
    return { success: true, data: aiResponse };
  } catch (error) {
    console.error('AI Analysis error:', error);
    return { success: false, error: error.message };
  }
});