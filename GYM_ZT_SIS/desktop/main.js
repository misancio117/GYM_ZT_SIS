'use strict';

const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn, execFileSync } = require('child_process');

const SERVER_BASE = process.env.GYM_SERVER_BASE || 'http://127.0.0.1:8000';
const SERVER_URL = `${SERVER_BASE.replace(/\/$/, '')}/login/`;
const APP_ICON = path.join(__dirname, 'build', 'gym_zt.ico');

let mainWindow = null;
let splashWindow = null;
let djangoProcess = null;
let logStream = null;
let backendExitEarly = null;

function getBackendRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }
  return path.join(__dirname, '..', 'backend');
}

function whichWindows(cmd) {
  try {
    const out = execFileSync('where.exe', [cmd], {
      encoding: 'utf8',
      windowsHide: true,
      timeout: 8000,
    });
    const line = out.split(/\r?\n/).map((s) => s.trim()).find(Boolean);
    return line && fs.existsSync(line) ? line : null;
  } catch {
    return null;
  }
}

function collectWindowsPythonCandidates() {
  const list = [];
  const pushExe = (p) => {
    if (p && fs.existsSync(p)) list.push(p);
  };

  if (process.env.GYM_PYTHON) pushExe(process.env.GYM_PYTHON);

  if (app.isPackaged) {
    pushExe(path.join(process.resourcesPath, 'python', 'python.exe'));
  }

  const win = process.env.WINDIR || 'C:\\Windows';
  pushExe(path.join(win, 'py.exe'));

  const localPrograms = process.env.LOCALAPPDATA
    ? path.join(process.env.LOCALAPPDATA, 'Programs', 'Python')
    : null;
  if (localPrograms && fs.existsSync(localPrograms)) {
    try {
      for (const name of fs.readdirSync(localPrograms)) {
        pushExe(path.join(localPrograms, name, 'python.exe'));
      }
    } catch {
      /* ignore */
    }
  }

  pushExe(
    process.env.LOCALAPPDATA
      ? path.join(process.env.LOCALAPPDATA, 'Python', 'bin', 'python.exe')
      : null
  );

  const pythonRoot = process.env.LOCALAPPDATA
    ? path.join(process.env.LOCALAPPDATA, 'Python')
    : null;
  if (pythonRoot && fs.existsSync(pythonRoot)) {
    try {
      for (const name of fs.readdirSync(pythonRoot)) {
        pushExe(path.join(pythonRoot, name, 'python.exe'));
      }
    } catch {
      /* ignore */
    }
  }

  const fromWhere = whichWindows('python');
  if (fromWhere) pushExe(fromWhere);

  return [...new Set(list)];
}

/**
 * { cmd: string, args: string[] } — args ya incluyen run_server.py absoluto.
 * En Windows prueba varias rutas porque el .exe no hereda el mismo PATH que PowerShell.
 */
function resolvePythonLaunch(runServerAbs) {
  if (process.env.GYM_PYTHON && fs.existsSync(process.env.GYM_PYTHON)) {
    return { cmd: process.env.GYM_PYTHON, args: [runServerAbs] };
  }

  if (app.isPackaged) {
    const embedded = path.join(process.resourcesPath, 'python', 'python.exe');
    if (fs.existsSync(embedded)) {
      return { cmd: embedded, args: [runServerAbs] };
    }
  }

  if (process.platform === 'win32') {
    for (const py of collectWindowsPythonCandidates()) {
      return { cmd: py, args: [runServerAbs] };
    }
    const pyExe = path.join(process.env.WINDIR || 'C:\\Windows', 'py.exe');
    if (fs.existsSync(pyExe)) {
      return { cmd: pyExe, args: ['-3', runServerAbs] };
    }
  }

  return {
    cmd: process.platform === 'win32' ? 'python' : 'python3',
    args: [runServerAbs],
  };
}

function augmentPathForPython(env) {
  if (process.platform !== 'win32') return env;
  const extra = [];
  if (process.env.LOCALAPPDATA) {
    extra.push(path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python311'));
    extra.push(path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python312'));
    extra.push(path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python313'));
    extra.push(path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python314'));
    extra.push(path.join(process.env.LOCALAPPDATA, 'Python', 'bin'));
  }
  const cur = env.PATH || process.env.PATH || '';
  env.PATH = [...extra.filter((d) => d && fs.existsSync(d)), cur].filter(Boolean).join(path.delimiter);
  return env;
}

function openLogFile() {
  try {
    const p = path.join(app.getPath('userData'), 'gym_zt_sis_backend.log');
    logStream = fs.createWriteStream(p, { flags: 'a' });
    logStream.write(`\n--- ${new Date().toISOString()} ---\n`);
    return p;
  } catch {
    return null;
  }
}

function logLine(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  if (logStream) logStream.write(line);
  if (!app.isPackaged) console.log(msg);
}

function waitForHttpOk(url, { maxAttempts = 120, intervalMs = 1000, abortCheck } = {}) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const tryOnce = () => {
      if (typeof abortCheck === 'function') {
        const msg = abortCheck();
        if (msg) {
          reject(new Error(msg));
          return;
        }
      }
      const req = http.get(url, (res) => {
        res.resume();
        if (res.statusCode >= 200 && res.statusCode < 500) {
          resolve();
          return;
        }
        attempts++;
        if (attempts >= maxAttempts) {
          reject(new Error(`HTTP ${res.statusCode} en ${url}`));
          return;
        }
        setTimeout(tryOnce, intervalMs);
      });
      req.on('error', (err) => {
        attempts++;
        if (attempts >= maxAttempts) {
          reject(new Error(`Sin respuesta del servidor (${err.message})`));
          return;
        }
        setTimeout(tryOnce, intervalMs);
      });
      req.setTimeout(15000, () => {
        req.destroy();
      });
    };
    tryOnce();
  });
}

async function waitForDjangoReady() {
  const candidates = [
    `${SERVER_BASE.replace(/\/$/, '')}/login/`,
    `${SERVER_BASE.replace(/\/$/, '')}/`,
  ];
  let lastErr = null;
  const abortCheck = () => {
    if (backendExitEarly) {
      return `El proceso Python terminó antes de abrir el puerto (código ${backendExitEarly.code}). Revise gym_zt_sis_backend.log.`;
    }
    return null;
  };

  for (const u of candidates) {
    try {
      await waitForHttpOk(u, {
        maxAttempts: 120,
        intervalMs: 1000,
        abortCheck,
      });
      return;
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error('No se pudo conectar al backend');
}

function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 320,
    frame: true,
    show: true,
    resizable: false,
    title: 'GYM ZT SIS',
    icon: APP_ICON,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

function createErrorWindow(message) {
  const w = new BrowserWindow({
    width: 520,
    height: 400,
    title: 'GYM ZT SIS — Error',
    icon: APP_ICON,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  const htmlPath = path.join(__dirname, 'error.html');
  w.loadFile(htmlPath);
  w.webContents.once('did-finish-load', () => {
    const text = message || 'Error desconocido';
    w.webContents.executeJavaScript(
      `document.getElementById('msg').textContent = ${JSON.stringify(text)}`
    );
  });
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 640,
    show: false,
    title: 'GYM ZT SIS',
    icon: APP_ICON,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.loadURL(SERVER_URL);
  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    mainWindow.show();
  });
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function killDjangoProcess() {
  if (!djangoProcess || djangoProcess.killed) return;
  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/PID', String(djangoProcess.pid), '/T', '/F'], {
        stdio: 'ignore',
        windowsHide: true,
      });
    } else {
      djangoProcess.kill('SIGTERM');
    }
  } catch (e) {
    logLine(`Error al detener Django: ${e.message}`);
  }
  djangoProcess = null;
}

function startDjango() {
  backendExitEarly = null;
  const backendRoot = getBackendRoot();
  const runServer = path.join(backendRoot, 'run_server.py');
  if (!fs.existsSync(runServer)) {
    throw new Error(`No se encontró run_server.py en ${runServer}`);
  }

  const runServerAbs = path.resolve(runServer);
  const launch = resolvePythonLaunch(runServerAbs);

  const userData = app.getPath('userData');
  const configDir = process.env.GYM_ZT_SIS_CONFIG_DIR || userData;
  const dataDir = process.env.GYM_ZT_SIS_DATA_DIR || path.join(userData, 'data');

  let env = {
    ...process.env,
    PYTHONUTF8: '1',
    PYTHONUNBUFFERED: '1',
    GYM_ZT_SIS_BACKEND_ROOT: backendRoot,
    GYM_ZT_SIS_CONFIG_DIR: configDir,
    GYM_ZT_SIS_DATA_DIR: dataDir,
    DJANGO_SETTINGS_MODULE: 'gym_zt_sis.settings',
  };
  env = augmentPathForPython(env);

  logLine(`Iniciando backend: ${launch.cmd} ${launch.args.join(' ')}`);
  logLine(`cwd=${backendRoot}`);
  logLine(`GYM_ZT_SIS_CONFIG_DIR=${configDir}`);

  djangoProcess = spawn(launch.cmd, launch.args, {
    cwd: backendRoot,
    env,
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  djangoProcess.stdout.on('data', (d) => logLine(d.toString().trim()));
  djangoProcess.stderr.on('data', (d) => logLine(d.toString().trim()));
  djangoProcess.on('error', (err) => {
    logLine(`spawn error: ${err.message}`);
    backendExitEarly = { code: -1, err: err.message };
  });
  djangoProcess.on('exit', (code, sig) => {
    logLine(`Django terminó code=${code} signal=${sig}`);
    if (code !== 0 && code !== null) {
      backendExitEarly = { code, sig };
    }
  });

  if (djangoProcess.pid) {
    logLine(`PID backend: ${djangoProcess.pid}`);
  }
}

async function launchFlow() {
  openLogFile();
  createSplash();

  try {
    startDjango();
  } catch (e) {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    createErrorWindow(`No se pudo iniciar el backend: ${e.message}`);
    return;
  }

  try {
    await waitForDjangoReady();
    createMainWindow();
  } catch (e) {
    logLine(`Health check falló: ${e.message}`);
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    killDjangoProcess();
    createErrorWindow(
      `El servidor no respondió a tiempo.\n\n${e.message}\n\nRevise el log:\n${path.join(app.getPath('userData'), 'gym_zt_sis_backend.log')}\n\nSi dice "spawn error" o el proceso termina al instante: la app no encontró Python. Defina la variable de entorno GYM_PYTHON con la ruta completa a python.exe (como en PowerShell: where.exe python) y vuelva a abrir la aplicación.\n\nTambién: PostgreSQL en ejecución y puerto 8000 libre.`
    );
  }
}

app.whenReady().then(() => {
  launchFlow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) launchFlow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    killDjangoProcess();
    if (logStream) logStream.end();
    app.quit();
  }
});

app.on('before-quit', () => {
  killDjangoProcess();
  if (logStream) logStream.end();
});
